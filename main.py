"""
Main application entry point for AI Research Assistant
"""

import asyncio
import logging
import signal
import sys
import uvicorn
import socketio  # <--- IMPORT SOCKET.IO
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List
import json
import uuid

# Import components
from backend.utils.config import Config
from backend.agents import ResearchOrchestrator, SearchAgent, SummarizerAgent, ReportWriterAgent

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# --- MCP SERVER CLASS (remains unchanged) ---
class MCPServer:
    # ... (no changes needed in this class)
    def __init__(self):
        self.agents = {}
        self.active_sessions = {}
        self.message_queue = asyncio.Queue()
        self.running = False
        
    async def register_agent(self, agent_id: str, agent_type: str, agent_instance):
        try:
            self.agents[agent_id] = {
                'id': agent_id,
                'type': agent_type,
                'instance': agent_instance,
                'status': 'active',
                'registered_at': asyncio.get_event_loop().time()
            }
            logger.info(f"Registered agent {agent_id} of type {agent_type}")
            return True
        except Exception as e:
            logger.error(f"Error registering agent {agent_id}: {str(e)}")
            return False
    
    async def unregister_agent(self, agent_id: str):
        try:
            if agent_id in self.agents:
                del self.agents[agent_id]
                logger.info(f"Unregistered agent {agent_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error unregistering agent {agent_id}: {str(e)}")
            return False
    
    async def send_message(self, agent_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if agent_id not in self.agents:
                return {'error': f'Agent {agent_id} not found'}
            agent_instance = self.agents[agent_id]['instance']
            if hasattr(agent_instance, 'handle_message'):
                response = await agent_instance.handle_message(message)
                return response
            else:
                return {'error': f'Agent {agent_id} does not support message handling'}
        except Exception as e:
            logger.error(f"Error sending message to agent {agent_id}: {str(e)}")
            return {'error': str(e)}
    
    async def broadcast_message(self, message: Dict[str, Any], exclude_agents: List[str] = None):
        try:
            exclude_agents = exclude_agents or []
            responses = {}
            for agent_id, agent_info in self.agents.items():
                if agent_id not in exclude_agents:
                    response = await self.send_message(agent_id, message)
                    responses[agent_id] = response
            return responses
        except Exception as e:
            logger.error(f"Error broadcasting message: {str(e)}")
            return {'error': str(e)}
    
    async def list_agents(self) -> Dict[str, Any]:
        return {
            agent_id: {
                'id': agent_id, # Return the full ID for delegate tasks
                'type': info['type'],
                'status': info['status'],
                'registered_at': info['registered_at']
            }
            for agent_id, info in self.agents.items()
        }
    
    async def add_session(self, session_id: str, websocket): # No longer needs websocket object
        self.active_sessions[session_id] = websocket # Can store sio session or just a placeholder
        logger.info(f"Added session {session_id}")
    
    async def remove_session(self, session_id: str):
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Removed session {session_id}")
    
    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        try:
            if session_id in self.active_sessions:
                # Use sio.emit to send message to a specific session (sid)
                event_name = message.get('type', 'message')
                await sio.emit(event_name, message, to=session_id)
                return True
            return False
        except Exception as e:
            logger.error(f"Error broadcasting to session {session_id}: {str(e)}")
            return False
    
    async def start(self):
        self.running = True
        logger.info("MCP Server started")
    
    async def stop(self):
        self.running = False
        for agent_id, agent_info in self.agents.items():
            try:
                agent_instance = agent_info['instance']
                if hasattr(agent_instance, 'shutdown'):
                    await agent_instance.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down agent {agent_id}: {str(e)}")
        self.agents.clear()
        self.active_sessions.clear()
        logger.info("MCP Server stopped")


# --- START OF CHANGES ---

# Global MCP server instance
mcp_server = MCPServer()

# Create a Socket.IO Async Server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")

# FastAPI application
app = FastAPI(title="AI Research Assistant", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Wrap FastAPI with Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Global agents
orchestrator = None
search_agent = None
summarizer_agent = None
report_writer_agent = None

@app.on_event("startup")
async def startup_event():
    # ... (startup logic remains the same)
    try:
        Config.validate_config()
        await mcp_server.start()
        global orchestrator, search_agent, summarizer_agent, report_writer_agent
        orchestrator = ResearchOrchestrator(mcp_server)
        search_agent = SearchAgent(mcp_server)
        summarizer_agent = SummarizerAgent(mcp_server)
        report_writer_agent = ReportWriterAgent(mcp_server)
        await orchestrator.initialize()
        await search_agent.initialize()
        await summarizer_agent.initialize()
        await report_writer_agent.initialize()
        logger.info("AI Research Assistant started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    # ... (shutdown logic remains the same)
    try:
        await mcp_server.stop()
        logger.info("AI Research Assistant shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# --- SOCKET.IO EVENT HANDLERS ---
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    await mcp_server.add_session(sid, sio)

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")
    await mcp_server.remove_session(sid)

@sio.event
async def research_request(sid, data):
    query = data.get('query', '')
    if query:
        result = await orchestrator.handle_research_request(query, sid)
        # Standardize the response format for the client
        await sio.emit('research_response', {'success': True, 'data': result}, to=sid)
    else:
        await sio.emit('research_response', {'success': False, 'error': 'Query is required'}, to=sid)
        
@sio.event
async def get_agents(sid): # <--- CHANGE HERE: REMOVED 'data'
    agents = await mcp_server.list_agents()
    await sio.emit('agents_response', {'success': True, 'data': {'agents': agents}}, to=sid)


@sio.event
async def health_check(sid):
    health = {
        'status': 'healthy',
        'agents': len(mcp_server.agents),
        'sessions': len(mcp_server.active_sessions)
    }
    await sio.emit('health_response', {'success': True, 'data': health}, to=sid)

# --- REMOVE OLD WEBSOCKET ENDPOINT ---
# @app.websocket("/ws/{session_id}") ... (This whole function is now deleted)

# --- REST API ENDPOINTS (remain unchanged) ---
# ... (all @app.post and @app.get endpoints are fine)
@app.post("/api/research")
async def research_endpoint(request: Dict[str, Any]):
    """Research endpoint for HTTP requests"""
    try:
        query = request.get('query', '')
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        session_id = str(uuid.uuid4())
        result = await orchestrator.handle_research_request(query, session_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in research endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents")
async def list_agents_endpoint():
    """List all registered agents"""
    try:
        agents = await mcp_server.list_agents()
        return {'agents': agents}
        
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'agents': len(mcp_server.agents),
        'sessions': len(mcp_server.active_sessions)
    }

@app.post("/api/search")
async def search_endpoint(request: Dict[str, Any]):
    """Direct search endpoint"""
    try:
        query = request.get('query', '')
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        result = await search_agent.search_and_summarize(query)
        return result
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- SERVE STATIC FILES (remains unchanged) ---
app.mount("/", StaticFiles(directory="public", html=True), name="public")

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    try:
        # Run the application using the socket_app wrapper
        uvicorn.run(
            "main:socket_app", # <--- IMPORTANT: RUN socket_app, NOT app
            host="localhost",
            port=Config.MCP_SERVER_PORT,
            log_level=Config.LOG_LEVEL.lower(),
            reload=True
        )
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)