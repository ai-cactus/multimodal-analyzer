"""
Application configuration and settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # GCP Configuration
    gcp_project_id: str = Field(default="", env="GCP_PROJECT_ID")
    gcp_location: str = Field(default="us-central1", env="GCP_LOCATION")
    google_application_credentials: str = Field(default="", env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # Model-Specific Regions
    claude_region: str = Field(default="global", env="CLAUDE_REGION")
    llama_region: str = Field(default="us-east5", env="LLAMA_REGION")
    gemini_region: str = Field(default="global", env="GEMINI_REGION")
    gpt_oss_region: str = Field(default="global", env="GPT_OSS_REGION")
    
    # Document AI
    docai_layout_processor_id: str = Field(default="", env="DOCAI_LAYOUT_PROCESSOR_ID")
    docai_form_processor_id: str = Field(default="", env="DOCAI_FORM_PROCESSOR_ID")
    docai_location: str = Field(default="us", env="DOCAI_LOCATION")
    
    # File storage
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    max_upload_size: int = Field(default=104857600, env="MAX_UPLOAD_SIZE")  # 100MB
    
    # Database
    database_url: str = Field(default="postgresql+asyncpg://user:password@localhost:5432/rag_analyzer", env="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Optional processing settings (for backward compatibility)
    max_workers: int = Field(default=3, env="MAX_WORKERS")
    embedding_batch_size: int = Field(default=50, env="EMBEDDING_BATCH_SIZE")
    
    # Model Selection Configuration
    use_multi_model: bool = Field(default=True, env="USE_MULTI_MODEL")
    primary_model: str = Field(default="llama-scout", env="PRIMARY_MODEL")
    
    # Confidence Thresholds (parameterized for testing)
    high_confidence_threshold: float = Field(default=0.95, env="HIGH_CONFIDENCE_THRESHOLD")
    medium_confidence_threshold: float = Field(default=0.80, env="MEDIUM_CONFIDENCE_THRESHOLD")
    
    # Iterative Refinement
    max_iterations: int = Field(default=5, env="MAX_ITERATIONS")
    convergence_threshold: int = Field(default=0, env="CONVERGENCE_THRESHOLD")  # Max high-confidence findings to converge
    medium_convergence_threshold: int = Field(default=0, env="MEDIUM_CONVERGENCE_THRESHOLD")  # Max medium-confidence findings to converge
    
    # Critique System
    enable_critique_system: bool = Field(default=True, env="ENABLE_CRITIQUE_SYSTEM")
    proposer_model: str = Field(default="gemini-flash", env="PROPOSER_MODEL")
    critic_model: str = Field(default="llama-scout", env="CRITIC_MODEL")
    use_critique_in_single_model: bool = Field(default=True, env="USE_CRITIQUE_IN_SINGLE_MODEL")
    
    # Consensus Calculation
    consensus_method: str = Field(default="hybrid", env="CONSENSUS_METHOD")  # Options: agreement, confidence, hybrid
    min_model_agreement: float = Field(default=0.66, env="MIN_MODEL_AGREEMENT")  # Minimum % of models that must agree
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Singleton instance
_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        # Explicitly export GCP credentials for Google SDKs
        if _settings.google_application_credentials:
            import os
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _settings.google_application_credentials
        
        # Optimize gRPC for network stability (avoids IPv6 bottlenecks)
        import os
        os.environ["GRPC_DNS_RESOLVER"] = "native"
    return _settings
