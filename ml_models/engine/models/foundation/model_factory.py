import importlib
import logging
from typing import Optional, Type
from ml_models.engine.models.foundation.base_model import BaseModel
from ml_models.infrastructure.config.ontology_config import ModelSpecification
from ml_models.infrastructure.config.model_registry_config import get_implementation_path

logger = logging.getLogger(__name__)

class ModelFactory:
    """
    Factory for dynamically instantiating ML models based on configuration.
    """
    
    @staticmethod
    def create_model(model_spec: ModelSpecification) -> Optional[BaseModel]:
        """
        Instantiates a model from its specification using dynamic imports.
        """
        algorithm = model_spec.algorithm
        impl_path = get_implementation_path(algorithm)
        
        if not impl_path:
            logger.error(f"No implementation found for algorithm: {algorithm}")
            return None
            
        try:
            module_path, class_name = impl_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            model_class: Type[BaseModel] = getattr(module, class_name)
            
            return model_class(model_spec)
        except (ImportError, AttributeError, ValueError) as e:
            logger.error(f"Failed to instantiate model {algorithm} from {impl_path}: {str(e)}")
            return None

    @staticmethod
    def get_available_algorithms() -> list:
        """Returns a list of all algorithms configured in the registry."""
        from ml_models.infrastructure.config.model_registry_config import MODEL_IMPLEMENTATIONS
        return list(MODEL_IMPLEMENTATIONS.keys())
