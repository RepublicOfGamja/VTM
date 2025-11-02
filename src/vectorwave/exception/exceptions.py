"""
Defines custom exceptions for the VectorWave project.
"""

class VectorWaveError(Exception):
    """Base exception class for the VectorWave library."""
    pass


class WeaviateConnectionError(VectorWaveError):
    """Raised when an error occurs while attempting to connect to the Weaviate server."""
    pass


class WeaviateNotReadyError(VectorWaveError):
    """Raised when connected to Weaviate, but the server is not in a ready state."""
    pass


class SchemaCreationError(VectorWaveError):
    """Raised when an error occurs during Weaviate collection schema creation."""
    pass