"""QEN Bolkestein sovereign configuration — ADR-CLE-004."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Neo4jConfig:
    uri: str
    username: str
    password: str


class QENBolkesteinConfig:
    ENV = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

    NEO4J_CONFIG = Neo4jConfig(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
    )

    GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
    APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")

    BASE_DIR = os.getenv(
        "BASE_DIR",
        str(Path(__file__).resolve().parent),
    )

    @classmethod
    def load_from_env_file(cls, env_file_path: str = ".env"):
        if os.path.exists(env_file_path):
            load_dotenv(env_file_path)

    @classmethod
    def validate(cls) -> bool:
        password = os.getenv("NEO4J_PASSWORD", cls.NEO4J_PASSWORD)

        if not password or password.startswith("[") or password == "PLACEHOLDER":
            print("❌ MISSING CREDENTIALS:")
            print("   - Neo4j Password (NEO4J_PASSWORD)")
            return False

        print("✅ Sovereign configuration valid")
        return True


if __name__ == "__main__":
    QENBolkesteinConfig.load_from_env_file()
    QENBolkesteinConfig.validate()
