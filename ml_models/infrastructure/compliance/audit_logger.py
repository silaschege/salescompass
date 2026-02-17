import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class AuditLogger:
    """
    Handles compliance audit logging for ML operations.
    Ensures all inference requests and decisions are traceable.
    """
    
    def __init__(self, log_dir: str = "logs/audit"):
        self.log_dir = log_dir
        self.logger = logging.getLogger("ml_audit")
        self.logger.setLevel(logging.INFO)
        
        # Ensure log directory exists
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except OSError:
                # Fallback if cannot create dir (e.g. permission issue)
                pass
        
        # Setup file handler
        if not self.logger.handlers:
            timestamp = datetime.now().strftime("%Y%m")
            file_handler = logging.FileHandler(f"{log_dir}/ml_audit_{timestamp}.jsonl")
            file_handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(file_handler)

    def log_inference(self, 
                      model_id: str, 
                      inputs: Dict[str, Any], 
                      outputs: Any, 
                      latency_ms: float,
                      user_id: Optional[str] = None,
                      request_id: Optional[str] = None) -> None:
        """
        Log an inference event.
        
        Args:
            model_id: ID of the model used
            inputs: input features/data
            outputs: prediction results
            latency_ms: inference time in milliseconds
            user_id: ID of the user triggering the request
            request_id: Unique request identifier
        """
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "inference",
            "request_id": request_id,
            "user_id": user_id,
            "model_id": model_id,
            "inputs": self._sanitize(inputs),
            "outputs": self._sanitize(outputs),
            "latency_ms": latency_ms
        }
        
        self.logger.info(json.dumps(audit_record))

    def _sanitize(self, data: Any) -> Any:
        """Sanitize data for logging (remove potential PII if configured)"""
        # Placeholder for PII redaction logic
        # For now, just ensure it's serializable
        if hasattr(data, "to_dict"):
            return data.to_dict()
        if hasattr(data, "dict"): # Pydantic v1
            return data.dict()
        if hasattr(data, "model_dump"): # Pydantic v2
            return data.model_dump()
        return data

# Global instance
audit_logger = AuditLogger()
