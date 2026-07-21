import os
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

class Config:
    """Base configuration settings."""
    FLASK_APP = os.getenv("FLASK_APP", "run.py")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"
    TESTING = False
    
    # Network setting
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # Security setting
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-please-change-in-prod")
    
    # NVIDIA API (placeholder for RAG phase)
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    
    # RAG Models & Configurations
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", 32))
    DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", 5))
    CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "ms-marco-MiniLM-L-6-v2")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))
    SEMANTIC_THRESHOLD = float(os.getenv("SEMANTIC_THRESHOLD", 0.6))
    
    # BM25 Configuration
    BM25_DEFAULT_TOP_K = int(os.getenv("BM25_DEFAULT_TOP_K", 5))
    BM25_TOKENIZER = os.getenv("BM25_TOKENIZER", "whitespace_lower")
    BM25_MAX_QUERY_LENGTH = int(os.getenv("BM25_MAX_QUERY_LENGTH", 1000))
    
    # Hybrid Retrieval Configuration
    HYBRID_RRF_K = int(os.getenv("HYBRID_RRF_K", 60))
    HYBRID_DEFAULT_TOP_K = int(os.getenv("HYBRID_DEFAULT_TOP_K", 5))
    
    # Reranking Configuration
    RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", 5))
    RERANK_BATCH_SIZE = int(os.getenv("RERANK_BATCH_SIZE", 32))
    RERANK_CANDIDATE_POOL = int(os.getenv("RERANK_CANDIDATE_POOL", 20))

    # Caching & Optimization Configuration
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() in ("true", "1", "yes")

    # Conversation Management Configuration
    MAX_CONVERSATION_TURNS = int(os.getenv("MAX_CONVERSATION_TURNS", 10))

    # Evaluation Configuration
    EVALUATION_ENABLED = os.getenv("EVALUATION_ENABLED", "True").lower() in ("true", "1", "yes")
    SAVE_EVALUATION_HISTORY = os.getenv("SAVE_EVALUATION_HISTORY", "True").lower() in ("true", "1", "yes")
    EVALUATION_DATASET_PATH = os.getenv("EVALUATION_DATASET_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "evaluation")))

    # Prompt Builder Configuration
    MAX_CONTEXT_CHUNKS = int(os.getenv("MAX_CONTEXT_CHUNKS", 5))
    MAX_CONTEXT_CHARACTERS = int(os.getenv("MAX_CONTEXT_CHARACTERS", 4000))
    PROMPT_TEMPLATE_VERSION = os.getenv("PROMPT_TEMPLATE_VERSION", "rag_prompt_v1")
    PROMPT_VERSION = os.getenv("PROMPT_VERSION", "1.0.0")
    PIPELINE_VERSION = os.getenv("PIPELINE_VERSION", "1.0.0")
    TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates")))

    # NVIDIA API LLM Generation Configuration
    NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 60))
    LLM_CONNECT_TIMEOUT = int(os.getenv("LLM_CONNECT_TIMEOUT", 10))
    LLM_READ_TIMEOUT = int(os.getenv("LLM_READ_TIMEOUT", 60))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 1024))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.2))
    LLM_TOP_P = float(os.getenv("LLM_TOP_P", 0.7))






class DevelopmentConfig(Config):
    """Development environment specific configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production environment specific configuration."""
    DEBUG = False
    # In production, require standard config checks if appropriate

class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True

# Dictionary to map environment name to config object
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}

def get_config():
    """Retrieve configuration class based on environment."""
    env = os.getenv("FLASK_ENV", "development").lower()
    return config_by_name.get(env, DevelopmentConfig)
