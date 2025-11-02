from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class WeaviateSettings(BaseSettings):
    """
    Manages Weaviate database connection settings.

    Reads values from environment variables or a .env file.
    (e.g., WEAVIATE_HOST=10.0.0.1)
    """
    # If environment variables are not set, these default values will be used.
    WEAVIATE_HOST: str = "localhost"
    WEAVIATE_PORT: int = 8080
    WEAVIATE_GRPC_PORT: int = 50051
    COLLECTION_NAME: str = "VectorWaveFunctions"
    IS_VECTORIZE_COLLECTION_NAME: bool = True

    # Configure to read from a .env file (optional)
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# @lru_cache ensures this function creates the Settings object only once (Singleton pattern)
# and reuses the cached object on subsequent calls.
@lru_cache
def get_weaviate_settings() -> WeaviateSettings:
    """
    Factory function that returns the settings object.
    """
    return WeaviateSettings()