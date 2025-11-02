import weaviate
import weaviate.classes.config as wvc # (wvc = Weaviate Classes Config)
from vectorwave.models.db_config import WeaviateSettings
from vectorwave.exception.exceptions import (
    WeaviateConnectionError,
    WeaviateNotReadyError,
    SchemaCreationError
)
from weaviate.exceptions import WeaviateConnectionError as WeaviateClientConnectionError


# Code based on Weaviate v4 (latest) client.

def get_weaviate_client(settings: WeaviateSettings) -> weaviate.WeaviateClient:
    """
    Creates and returns a Weaviate client.

    [Raises]
    - WeaviateConnectionError: If connection fails.
    - WeaviateNotReadyError: If connected, but the server is not ready.
    """

    client: weaviate.WeaviateClient

    try:
        client = weaviate.connect_to_local(
            host=settings.WEAVIATE_HOST,
            port=settings.WEAVIATE_PORT,
            grpc_port=settings.WEAVIATE_GRPC_PORT
        )
    except WeaviateClientConnectionError as e:
        raise WeaviateConnectionError(f"Failed to connect to Weaviate: {e}")
    except Exception as e:
        raise WeaviateConnectionError(f"An unknown error occurred while connecting to Weaviate: {e}")


    if not client.is_ready():
        raise WeaviateNotReadyError("Connected to Weaviate, but the server is not ready.")

    print("Weaviate client connected successfully.")
    return client


def create_vectorwave_schema(client: weaviate.WeaviateClient, settings: WeaviateSettings):
    """
    Defines and creates the VectorWaveFunctions collection schema.

    [Raises]
    - SchemaCreationError: If an error occurs during schema creation.
    """
    collection_name = settings.COLLECTION_NAME

    # 1. Check if the collection already exists
    if client.collections.exists(collection_name):
        print(f"Collection '{collection_name}' already exists. Skipping creation.")
        return client.collections.get(collection_name)

    # 2. If it doesn't exist, define and create the collection
    print(f"Creating collection '{collection_name}'...")

    try:
        vectorwave_collection = client.collections.create(
            name=collection_name,

            # 3. Define Properties
            properties=[
                wvc.Property(
                    name="function_name",
                    data_type=wvc.DataType.TEXT,
                    description="The name of the vectorized function"
                ),
                wvc.Property(
                    name="module_name",
                    data_type=wvc.DataType.TEXT,
                    description="The Python module path where the function is defined"
                ),
                wvc.Property(
                    name="docstring",
                    data_type=wvc.DataType.TEXT,
                    description="The function's Docstring (description)"
                ),
                wvc.Property(
                    name="source_code",
                    data_type=wvc.DataType.TEXT,
                    description="The actual source code of the function"
                ),
                # TODO: Additional properties for 'execution flow prediction' (e.g., call_count, avg_runtime)
                wvc.Property(
                    name="call_count",
                    data_type=wvc.DataType.INT,
                    description="Function call count",
                    default_value=0
                ),
            ],

            # 4. Vectorizer Configuration
            vectorizer_config=wvc.Configure.Vectorizer.text2vec_openai(
                # OpenAI API key must be set via environment variable (OPENAI_API_KEY).
                vectorize_collection_name=settings.IS_VECTORIZE_COLLECTION_NAME, # Include collection name in vectorization
            ),

            # 5. Generative Configuration (for RAG, etc.)
            generative_config=wvc.Configure.Generative.openai()
        )

        print(f"Collection '{collection_name}' created successfully.")
        return vectorwave_collection

    except Exception as e:
        # Raise a specific exception instead of returning None
        raise SchemaCreationError(f"Error during schema creation: {e}")