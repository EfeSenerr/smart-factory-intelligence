"""Configuration for Azure AI Foundry connections."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

# Azure AI Foundry
PROJECT_ENDPOINT = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5")
MINI_DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_MINI_DEPLOYMENT_NAME", "gpt-5-mini")
EMBEDDING_DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-large")

# Database
DB_PATH = Path(__file__).parent / "database" / "manufacturing.db"
