import os
from pydantic import BaseModel


class Settings(BaseModel):
    APP_NAME: str = "Enterprise Multimodal Logistics Management Engine"
    ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Path configuration
    PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")
    RESULTS_DIR: str = os.path.join(PROJECT_ROOT, "results")
    GRAPH_CACHE_PATH: str = os.path.join(RESULTS_DIR, "multimodal_graph.pkl")


settings = Settings()
os.makedirs(settings.RESULTS_DIR, exist_ok=True)
