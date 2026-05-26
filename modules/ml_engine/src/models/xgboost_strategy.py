import json
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
import structlog

from pathlib import Path
from datetime import datetime

log = structlog.get_logger()

MODEL_DIR = (
    Path(__file__).parent.parent.parent
    / "artifacts"
)

MODEL_DIR.mkdir(exist_ok=True)


class XGBoostStrategyModel:

    def __init__(self):
        self.model = None
        self.version = None

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series
    ):

        self.model = xgb.XGBRegressor(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
        )

        self.model.fit(
            X,
            y,
            eval_set=[(X, y)],
            verbose=False
        )

        self.version = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        return {
            "version": self.version,
            "features": list(X.columns),
        }

    def predict(
        self,
        X: pd.DataFrame
    ):

        if self.model is None:
            raise RuntimeError(
                "Model not trained or loaded."
            )

        return self.model.predict(X)

    def save(self):

        path = (
            MODEL_DIR
            / f"xgb_strategy_{self.version}.joblib"
        )

        joblib.dump(
            self.model,
            path
        )

        meta = {
            "version": self.version,
            "model_type": "xgboost_strategy",
        }

        (
            MODEL_DIR
            / f"xgb_strategy_{self.version}_meta.json"
        ).write_text(json.dumps(meta))

        log.info(
            "model_saved",
            path=str(path)
        )

        return path

    def load(self, version: str):

        path = (
            MODEL_DIR
            / f"xgb_strategy_{version}.joblib"
        )

        self.model = joblib.load(path)

        self.version = version

        log.info(
            "model_loaded",
            version=version
        )
