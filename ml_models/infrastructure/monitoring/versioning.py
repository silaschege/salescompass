import os
import shutil
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from ml_models.infrastructure.config.settings import config

class ModelVersioningService:
    """
    Manages model artifact versions and metadata.
    Provides a centralized way to track production vs. experimental models.
    """
    
    def __init__(self):
        self.base_path = config.model_storage_path
        self.registry_file = os.path.join(self.base_path, "registry.json")
        os.makedirs(self.base_path, exist_ok=True)
        self._load_registry()

    def _load_registry(self):
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                self.registry = json.load(f)
        else:
            self.registry = {"models": {}}

    def _save_registry(self):
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def register_version(self, model_id: str, artifact_path: str, metrics: Dict[str, float]):
        """Registers a new model version."""
        if model_id not in self.registry["models"]:
            self.registry["models"][model_id] = {
                "active_version": None,
                "versions": []
            }
        
        version_id = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        version_data = {
            "version_id": version_id,
            "path": artifact_path,
            "metrics": metrics,
            "created_at": datetime.now().isoformat(),
            "status": "experimental"
        }
        
        self.registry["models"][model_id]["versions"].append(version_data)
        
        # If no active version, set this as active
        if not self.registry["models"][model_id]["active_version"]:
            self.registry["models"][model_id]["active_version"] = version_id
            version_data["status"] = "production"
            
        self._save_registry()
        return version_id

    def promote_to_production(self, model_id: str, version_id: str):
        """Promotes a specific version to production."""
        if model_id not in self.registry["models"]:
            return False
            
        model_data = self.registry["models"][model_id]
        found = False
        for v in model_data["versions"]:
            if v["version_id"] == version_id:
                v["status"] = "production"
                model_data["active_version"] = version_id
                found = True
            else:
                v["status"] = "experimental"
                
        if found:
            self._save_registry()
        return found

    def get_latest_production_path(self, model_id: str) -> Optional[str]:
        """Retrieves path to the active production model."""
        model_data = self.registry["models"].get(model_id)
        if not model_data or not model_data["active_version"]:
            return None
            
        active_id = model_data["active_version"]
        for v in model_data["versions"]:
            if v["version_id"] == active_id:
                return v["path"]
        return None
