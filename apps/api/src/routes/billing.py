"""Stripe routes for Noshight per-hospital monthly subscription.

Mirrors the Deegha billing pattern. Per-hospital subscription:
  noshight_hospital_monthly_aed  → AED 1,499/mo
  noshight_hospital_monthly_usd  → USD 410/mo (parity)

Endpoints (mounted under /api/billing):
  POST /checkout    create Stripe Checkout session for the calling hospital
  POST /portal      create Billing Portal session for existing customer
  POST /webhook     receive Stripe-signed events
  POST /bootstrap   admin-token POST that idempotently upserts products+prices
"""

from __future__ import annotations

import os
import time
from typing import Any

import stripe
from fastapi import APIRouter, Header, HTTPException, Request, status

router = APIRouter(prefix="/api/billing", tags=["billing"])


LAUNCH_MODE = os.environ.get("LAUNCH_MODE", "invoice").lower()
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_BOOTSTRAP_TOKEN = os.environ.get("STRIPE_BOOTSTRAP_TOKEN", "")
SUCCESS_URL = os.environ.get(
    "NOSHIGHT_BILLING_SUCCESS_URL",
    "https://noshight.nomoi.ai/billing?checkout=success",
)
CANCEL_URL = os.environ.get(
    "NOSHIGHT_BILLING_CANCEL_URL",
    "https://noshight.nomoi.ai/billing?checkout=canceled",
)
PORTAL_RETURN_URL = os.environ.get(
    "NOSHIGHT_BILLING_PORTAL_RETURN_URL",
    "https://noshight.nomoi.ai/billing",
)

LOOKUP_KEYS = {
    "hospital_monthly_aed": "noshight_hospital_monthly_aed",
    "hospital_monthly_usd": "noshight_hospital_monthly_usd",
}


def _check_enabled() -> None:
    if LAUNCH_MODE == "invoice":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing in invoice-only mode. Contact assel@nomoi.ai.",
        )
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe not configured",
        )
    stripe.api_key = STRIPE_SECRET_KEY


def _dev_metadata() -> dict[str, str]:
    return {
        "env": "dev",
        "created_by": "noshight-billing-bringup",
        "product_slug": "noshight",
    }


@router.post("/checkout")
async def create_checkout(payload: dict[str, Any]) -> dict[str, Any]:
    _check_enabled()
    hospital_id = payload.get("hospital_id")
    email = payload.get("email")
    lookup_key = payload.get("lookup_key", LOOKUP_KEYS["hospital_monthly_aed"])
    if not hospital_id or not email:
        raise HTTPException(status_code=400, detail="hospital_id and email required")

    prices = stripe.Price.list(lookup_keys=[lookup_key], limit=1)
    if not prices.data:
        raise HTTPException(
            status_code=500,
            detail=f"Price not bootstrapped: {lookup_key}. Run /bootstrap first.",
        )
    price = prices.data[0]

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price.id, "quantity": 1}],
        success_url=payload.get("success_url", SUCCESS_URL),
        cancel_url=payload.get("cancel_url", CANCEL_URL),
        customer_email=email,
        allow_promotion_codes=True,
        metadata={
            "hospital_id": str(hospital_id),
            "lookup_key": lookup_key,
            "product": "noshight",
        },
    )
    return {"url": session.url, "id": session.id}


@router.post("/portal")
async def create_portal(payload: dict[str, Any]) -> dict[str, Any]:
    _check_enabled()
    customer_id = payload.get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="stripe_customer_id required")
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=payload.get("return_url", PORTAL_RETURN_URL),
    )
    return {"url": session.url}


@router.post("/webhook")
async def webhook(request: Request) -> dict[str, Any]:
    _check_enabled()
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="webhook secret not configured")
    body = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(body, sig, STRIPE_WEBHOOK_SECRET)
    except stripe.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"invalid signature: {e}") from e

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        hospital_id = obj.get("metadata", {}).get("hospital_id")
        customer = obj.get("customer")
        if hospital_id and customer:
            request.state.linkage = {"hospital_id": hospital_id, "stripe_customer_id": customer}
        return {"handled": event_type}

    if event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
    }:
        item = (obj.get("items", {}) or {}).get("data", [{}])[0]
        request.state.subscription = {
            "id": obj.get("id"),
            "stripe_customer_id": obj.get("customer"),
            "stripe_price_id": (item.get("price") or {}).get("id"),
            "lookup_key": (item.get("price") or {}).get("lookup_key", ""),
            "status": obj.get("status"),
            "current_period_start": obj.get("current_period_start"),
            "current_period_end": obj.get("current_period_end"),
            "cancel_at_period_end": obj.get("cancel_at_period_end", False),
            "hospital_id": obj.get("metadata", {}).get("hospital_id"),
        }
        return {"handled": event_type}

    if event_type == "customer.subscription.deleted":
        request.state.cancel_sub_id = obj.get("id")
        return {"handled": event_type}

    return {"ignored": event_type}


@router.post("/bootstrap")
async def bootstrap(x_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    _check_enabled()
    if not STRIPE_BOOTSTRAP_TOKEN or x_admin_token != STRIPE_BOOTSTRAP_TOKEN:
        raise HTTPException(status_code=401, detail="invalid admin token")

    products = []
    for slug, name, description, prices in [
        (
            "noshight-hospital",
            "Noshight — Hospital",
            "Per-hospital unlimited no-show prediction subscription",
            [
                {"lookup_key": LOOKUP_KEYS["hospital_monthly_aed"], "unit_amount": 149900, "currency": "aed"},
                {"lookup_key": LOOKUP_KEYS["hospital_monthly_usd"], "unit_amount": 41000, "currency": "usd"},
            ],
        ),
    ]:
        existing = stripe.Product.search(query=f"metadata['slug']:'{slug}'", limit=1)
        product = (
            existing.data[0]
            if existing.data
            else stripe.Product.create(
                name=name,
                description=description,
                metadata={"slug": slug, **_dev_metadata()},
            )
        )
        created_prices = []
        for p in prices:
            ex_prices = stripe.Price.list(lookup_keys=[p["lookup_key"]], limit=1)
            price = (
                ex_prices.data[0]
                if ex_prices.data
                else stripe.Price.create(
                    product=product.id,
                    unit_amount=p["unit_amount"],
                    currency=p["currency"],
                    recurring={"interval": "month"},
                    lookup_key=p["lookup_key"],
                    nickname=f"{name} — {p['currency'].upper()} monthly",
                    metadata=_dev_metadata(),
                )
            )
            created_prices.append({"lookup_key": p["lookup_key"], "id": price.id})
        products.append({
            "slug": slug,
            "stripe_product_id": product.id,
            "prices": created_prices,
        })

    return {"product_slug": "noshight", "products": products, "bootstrapped_at": int(time.time())}
