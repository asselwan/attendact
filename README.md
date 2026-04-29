# Noshight

No-show + Insight. UAE no-show prediction signal product. Scores appointment risk and triggers multilingual interventions.

## Stack

- **API**: FastAPI + XGBoost + SHAP (Python 3.12)
- **Web**: React + Vite + TypeScript + Tailwind
- **DB**: Supabase Postgres (Frankfurt)
- **Host**: Coolify on Hetzner
- **Domain**: noshight.nomoi.ai

## Local development

```bash
# API
cd apps/api
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000

# Web
cd apps/web
npm install
npm run dev
```

## Model versions

- `heuristic_v1`: Weighted additive scorer from published literature
- `brazil_xgb_v1`: XGBoost trained on Brazil Kaggle 110k dataset (week 4)
- `uae_xgb_v1`: Trained on first hospital partner retrospective (post DUA)

## Compliance

Not a clinical decision tool. Not SaMD. Operational AI only.
See `docs/compliance/` for ADHICS and PDPL checklists.
