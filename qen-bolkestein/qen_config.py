# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import os
from dotenv import load_dotenv
from dataclasses import dataclass

@dataclass
class Neo4jConfig:
    uri: str
    username: str
    password: str

@dataclass
class OllamaConfig:
    base_url: str
    model_name: str = "mistral:7b"

class QENBolkesteinConfig:
    ENV = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
    
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
    NEO4J_CONFIG = Neo4jConfig(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
    )
    
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_CONFIG = OllamaConfig(base_url=OLLAMA_BASE_URL)
    
    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
    
    APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
    
    BASE_DIR = os.getenv("BASE_DIR", "/root/CognitiveLogic2026.github.io/qen-bolkestein/")
    
    @classmethod
    def load_from_env_file(cls, env_file_path: str = ".env"):
        if os.path.exists(env_file_path):
            load_dotenv(env_file_path)
        else:
            print(f"⚠️ .env file not found at {env_file_path}")
    
    @classmethod
    def validate(cls) -> bool:
        required = [
            ("ANTHROPIC_API_KEY", "Claude API"),
            ("MISTRAL_API_KEY", "Mistral API"),
            ("NEO4J_PASSWORD", "Neo4j Password"),
        ]
        missing = []
        for key, name in required:
            value = os.getenv(key, "")
            if not value or value.startswith("[") or value == "PLACEHOLDER":
                missing.append(f"{name} ({key})")
        
        if missing:
            print("❌ MISSING CREDENTIALS:")
            for item in missing:
                print(f"   - {item}")
            return False
        
        print("✅ All credentials present")
        return True

if __name__ == "__main__":
    QENBolkesteinConfig.load_from_env_file()
    QENBolkesteinConfig.validate()
