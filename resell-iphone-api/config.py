import os
from dataclasses import dataclass, field
from typing import List
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Dependency injection markers
class DatabaseMarker:
    pass

class SettingsMarker:
    pass

# Settings class
@dataclass
class Settings:
    # Database settings
    db_name: str = os.getenv("DB_NAME", "resell_iphone")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "postgres")
    
    # API settings
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS settings
    cors_allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_allowed_methods: List[str] = field(default_factory=lambda: ["*"])
    cors_allowed_headers: List[str] = field(default_factory=lambda: ["*"])
    
    # Application settings
    pagination_limit: int = int(os.getenv("PAGINATION_LIMIT", "10"))

    @property
    def database_url(self) -> str:
        """Get database connection URL"""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

# Create settings instance
settings = Settings() 