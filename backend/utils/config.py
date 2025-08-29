"""
Configuration settings for AI Research Assistant
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "gemini-1.5-flash"
    

    # --- START OF CHANGES ---
    # Google Search API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "")

    # MCP Protocol Configuration
    MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", 8000))
    MCP_PROTOCOL_VERSION = "1.0.0"
    MCP_TIMEOUT = 30.0
    
    # Agent Configuration
    MAX_CONCURRENT_AGENTS = 5
    AGENT_RETRY_COUNT = 3
    AGENT_TIMEOUT = 60.0
    
    # Search Configuration
    MAX_SEARCH_RESULTS = 10
    SEARCH_TIMEOUT = 15.0
    
    # Vector Store Configuration
    VECTOR_DIMENSION = 384
    MAX_CHUNKS = 1000
    
    # Web Server Configuration
    WS_PORT = int(os.getenv("WS_PORT", 3001))
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required. Please set it in your .env file")
        if not cls.GOOGLE_API_KEY or not cls.SEARCH_ENGINE_ID:
            raise ValueError("GOOGLE_API_KEY and SEARCH_ENGINE_ID are required for web search.")
        
        return True

# MCP Message Types
class MCPMessageTypes:
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    SHUTDOWN = "shutdown"

# Agent Types
class AgentTypes:
    ORCHESTRATOR = "research_orchestrator"
    SEARCH = "search_agent"
    SUMMARIZER = "summarizer_agent"
    REPORT_WRITER = "report_writer_agent"

# Research Task Types
class TaskTypes:
    WEB_SEARCH = "web_search"
    SUMMARIZE = "summarize"
    GENERATE_REPORT = "generate_report"
    ANALYZE_DATA = "analyze_data"