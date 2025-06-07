# api_clients.py
"""
API client initialization and management.
Centralizes the creation and configuration of API clients.
"""

from typing import Optional

import openai
import anthropic
import google.generativeai as genai

from src.config.settings import settings
from src.utils.logger import logger

class APIClients:
    """Singleton class to manage API client instances."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_clients()
            self.__class__._initialized = True
    
    def _initialize_clients(self):
        """Initialize all API clients with credentials from environment."""
        # API keys are already validated by `settings` during import
        self.openai_api_key = settings.OPENAI_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        self.gemini_api_key = settings.GEMINI_API_KEY
        
        # Initialize OpenAI client
        if self.openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            logger.warning("OPENAI_API_KEY is not configured – OpenAI models will be unavailable.")
            
        # Initialize Anthropic client
        if self.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        else:
            self.anthropic_client = None
            logger.warning("ANTHROPIC_API_KEY is not configured – Claude models will be unavailable.")
            
        # Configure Google Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_configured = True
        else:
            self.gemini_configured = False
            logger.warning("GEMINI_API_KEY is not configured – Gemini models will be unavailable.")
    
    def get_openai_client(self) -> Optional[openai.AsyncOpenAI]:
        """Get the OpenAI client instance."""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        return self.openai_client
    
    def get_anthropic_client(self) -> Optional[anthropic.Anthropic]:
        """Get the Anthropic client instance."""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        return self.anthropic_client
    
    def is_gemini_configured(self) -> bool:
        """Check if Gemini is configured."""
        return self.gemini_configured


# Global instance
api_clients = APIClients()