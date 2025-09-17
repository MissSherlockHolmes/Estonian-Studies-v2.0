"""
Configuration module for Estonian Studies Notes
Loads environment variables from config.env
"""

import os
from dotenv import load_dotenv

# Load environment variables from config.env file
load_dotenv("config.env")

# Adobe PDF Services Configuration
PDF_SERVICES_CLIENT_ID = os.getenv('PDF_SERVICES_CLIENT_ID')
PDF_SERVICES_CLIENT_SECRET = os.getenv('PDF_SERVICES_CLIENT_SECRET')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Ollama Configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434/api')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'granite3.2-vision:latest')

# Validate required configurations
def validate_config():
    """Validate that required environment variables are set"""
    errors = []
    
    if not PDF_SERVICES_CLIENT_ID:
        errors.append("PDF_SERVICES_CLIENT_ID not set")
    if not PDF_SERVICES_CLIENT_SECRET:
        errors.append("PDF_SERVICES_CLIENT_SECRET not set")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return True
