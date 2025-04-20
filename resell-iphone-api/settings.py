from dataclasses import dataclass
from typing import List


@dataclass
class Settings:
    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    cors_allowed_origins: List[str]
    cors_allowed_methods: List[str]
    cors_allowed_headers: List[str]
    pagination_limit: int
