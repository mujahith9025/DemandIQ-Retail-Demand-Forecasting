import os
import glob
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import joblib


class ModelStorage:
    """
    Manages filesystem serialization and retrieval of versioned demand forecasting artifacts.
    """

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            # Default to backend/saved_models
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.base_dir = os.path.join(current_dir, "saved_models")
        else:
            self.base_dir = base_dir

        os.makedirs(self.base_dir, exist_ok=True)

    def _get_filename(self, product_id: int, store_id: int, model_type: str, version: str) -> str:
        return f"{product_id}_{store_id}_{model_type}_v{version}.joblib"

    def save_model(
        self,
        product_id: int,
        store_id: int,
        model_type: str,
        model_object: Any,
        metrics: Dict[str, float],
        version: str = "1.0",
    ) -> str:
        """
        Serialize model and its evaluation metadata to disk.
        """
        filename = self._get_filename(product_id, store_id, model_type, version)
        filepath = os.path.join(self.base_dir, filename)

        payload = {
            "product_id": product_id,
            "store_id": store_id,
            "model_type": model_type,
            "version": version,
            "metrics": metrics,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "model": model_object,
        }

        joblib.dump(payload, filepath, compress=3)
        return filepath

    def load_model(
        self,
        product_id: int,
        store_id: int,
        model_type: str = "ensemble",
        version: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Load the latest or specific version of a saved model artifact.
        """
        if version:
            filename = self._get_filename(product_id, store_id, model_type, version)
            filepath = os.path.join(self.base_dir, filename)
            if os.path.exists(filepath):
                return joblib.load(filepath)
            return None

        # Look for matching pattern and pick latest
        pattern = os.path.join(self.base_dir, f"{product_id}_{store_id}_{model_type}_v*.joblib")
        matching = glob.glob(pattern)
        if not matching:
            return None

        # Sort by modification time (most recent first)
        matching.sort(key=os.path.getmtime, reverse=True)
        return joblib.load(matching[0])

    def has_model(self, product_id: int, store_id: int, model_type: str = "ensemble") -> bool:
        pattern = os.path.join(self.base_dir, f"{product_id}_{store_id}_{model_type}_v*.joblib")
        return len(glob.glob(pattern)) > 0

    def list_saved_models(self) -> List[Dict[str, Any]]:
        pattern = os.path.join(self.base_dir, "*.joblib")
        files = glob.glob(pattern)
        results = []
        for f in files:
            try:
                data = joblib.load(f)
                results.append(
                    {
                        "filename": os.path.basename(f),
                        "product_id": data.get("product_id"),
                        "store_id": data.get("store_id"),
                        "model_type": data.get("model_type"),
                        "version": data.get("version"),
                        "metrics": data.get("metrics"),
                        "saved_at": data.get("saved_at"),
                    }
                )
            except Exception:
                continue
        return results
