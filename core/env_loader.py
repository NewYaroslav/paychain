"""
Module: core.env_loader
Description: Loads environment variables from .env file and OS environment.
"""

import os
from dotenv import load_dotenv

def load_env():
    """
    Load environment variables from .env file if present.
    """
    env_path = os.getenv("ENV_FILE", ".env")
    load_dotenv(dotenv_path=env_path)