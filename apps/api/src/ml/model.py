"""XGBoost model wrapper. Ships in week 4 with brazil_xgb_v1."""

import os
from pathlib import Path


MODEL_ARTIFACTS_DIR = Path(__file__).parent.parent.parent.parent.parent / "ml" / "artifacts"


class XGBoostScorer:
    """Wrapper for trained XGBoost model. Not active until artifact exists."""

    def __init__(self, model_version: str = "brazil_xgb_v1"):
        self.model_version = model_version
        self.model = None
        self._load()

    def _load(self):
        artifact_path = MODEL_ARTIFACTS_DIR / f"{self.model_version}.pkl"
        if artifact_path.exists():
            import pickle

            with open(artifact_path, "rb") as f:
                self.model = pickle.load(f)

    def is_available(self) -> bool:
        return self.model is not None

    def score(self, features: dict) -> float:
        if not self.is_available():
            raise RuntimeError(f"Model {self.model_version} not loaded")
        # Feature vector ordering will be defined in train_xgboost.py
        raise NotImplementedError("XGBoost scoring ships in week 4")
