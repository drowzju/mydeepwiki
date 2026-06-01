import adalflow as adal

from api.config import configs, get_embedder_type, is_rag_enabled


def get_embedder(is_local_ollama: bool = False, use_google_embedder: bool = False, embedder_type: str = None):
    """Get embedder based on configuration or parameters.

    Args:
        is_local_ollama: Legacy parameter for Ollama embedder
        use_google_embedder: Legacy parameter for Google embedder
        embedder_type: Direct specification of embedder type ('ollama', 'google', 'bedrock', 'openai')

    Returns:
        adalflow.Embedder or None: Configured embedder instance, or None if RAG is disabled
    """
    # Check if RAG is enabled
    if not is_rag_enabled():
        return None

    # Determine which embedder config to use
    if embedder_type:
        if embedder_type == 'ollama':
            embedder_config = configs.get("embedder_ollama")
        elif embedder_type == 'google':
            embedder_config = configs.get("embedder_google")
        elif embedder_type == 'bedrock':
            embedder_config = configs.get("embedder_bedrock")
        else:  # default to openai
            embedder_config = configs.get("embedder")
    elif is_local_ollama:
        embedder_config = configs.get("embedder_ollama")
    elif use_google_embedder:
        embedder_config = configs.get("embedder_google")
    else:
        # Auto-detect based on current configuration
        current_type = get_embedder_type()
        if current_type == 'bedrock':
            embedder_config = configs.get("embedder_bedrock")
        elif current_type == 'ollama':
            embedder_config = configs.get("embedder_ollama")
        elif current_type == 'google':
            embedder_config = configs.get("embedder_google")
        else:
            embedder_config = configs.get("embedder")

    # If no embedder config is found, return None
    if not embedder_config:
        return None

    # --- Initialize Embedder ---
    model_client_class = embedder_config.get("model_client")
    if not model_client_class:
        return None

    if "initialize_kwargs" in embedder_config:
        model_client = model_client_class(**embedder_config["initialize_kwargs"])
    else:
        model_client = model_client_class()

    # Create embedder with basic parameters
    embedder_kwargs = {"model_client": model_client, "model_kwargs": embedder_config.get("model_kwargs", {})}

    embedder = adal.Embedder(**embedder_kwargs)

    # Set batch_size as an attribute if available (not a constructor parameter)
    if "batch_size" in embedder_config:
        embedder.batch_size = embedder_config["batch_size"]
    return embedder
