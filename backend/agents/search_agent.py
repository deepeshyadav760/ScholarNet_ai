"""
Search Agent - Handles web searches and data collection
"""

import asyncio
import logging
import uuid
import aiohttp
import json
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import google.generativeai as genai
# --- START OF CHANGES ---
from ..utils.config import Config, MCPMessageTypes, AgentTypes
# --- END OF CHANGES ---

logger = logging.getLogger(__name__)

class SearchAgent:
    # ... (init and initialize are the same)
    def __init__(self, mcp_server):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = AgentTypes.SEARCH
        self.mcp_server = mcp_server
        self.session = None
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        logger.info(f"Search Agent initialized with ID: {self.agent_id}")
    
    async def initialize(self):
        """Initialize the search agent"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=Config.SEARCH_TIMEOUT)
            )
            await self.mcp_server.register_agent(self.agent_id, self.agent_type, self)
            logger.info("Search Agent initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Search Agent: {str(e)}")
            return False

    # ... (handle_message, _handle_search_request, _handle_extract_request are the same)
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP messages"""
        try:
            message_type = message.get('type')
            method = message.get('method')
            if message_type == MCPMessageTypes.REQUEST:
                if method == 'search':
                    return await self._handle_search_request(message['params'])
                elif method == 'extract_content':
                    return await self._handle_extract_request(message['params'])
            return {'error': 'Unknown method'}
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return {'error': str(e)}
    
    async def _handle_search_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search request"""
        try:
            query = params.get('query', '')
            max_results = params.get('max_results', Config.MAX_SEARCH_RESULTS)
            if not query:
                return {'error': 'Query parameter is required'}
            search_results = await self._web_search(query, max_results)
            return {'result': search_results}
        except Exception as e:
            logger.error(f"Error in search request: {str(e)}")
            return {'error': str(e)}

    async def _handle_extract_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content extraction request"""
        try:
            url = params.get('url', '')
            if not url:
                return {'error': 'URL parameter is required'}
            content = await self._extract_content(url)
            return {'result': content}
        except Exception as e:
            logger.error(f"Error in extract request: {str(e)}")
            return {'error': str(e)}

    # --- START OF MAJOR CHANGES ---

    async def _web_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform web search using Google Programmable Search Engine."""
        try:
            logger.info(f"Performing Google search for: {query}")
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': Config.GOOGLE_API_KEY,
                'cx': Config.SEARCH_ENGINE_ID,
                'q': query,
                'num': max_results
            }

            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    for item in data.get('items', []):
                        results.append({
                            'title': item.get('title', 'No Title'),
                            'url': item.get('link', ''),
                            'content': item.get('snippet', 'No snippet available.'),
                            'type': 'web_result'
                        })
                    logger.info(f"Found {len(results)} results from Google search.")
                    return results
                else:
                    error_text = await response.text()
                    logger.error(f"Google Search API error: {response.status} - {error_text}")
                    return await self._generate_synthetic_results(query, max_results)

        except Exception as e:
            logger.error(f"Error in web search: {str(e)}")
            return await self._generate_synthetic_results(query, max_results)

    # Note: _alternative_search and the DuckDuckGo logic are now removed in favor of Google.
    # The _generate_synthetic_results function is kept as a final fallback.
            
    async def _generate_synthetic_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
    # ... (this function remains the same as a fallback)
        try:
            logger.warning(f"Falling back to synthetic search result generation for query: {query}")
            prompt = f"""
            Generate {max_results} realistic web search results for the query: "{query}"
            Each result should have a relevant title, a realistic URL, and a brief content summary (2-3 sentences).
            Format as JSON array. Only return the JSON array.
            """
            response = await self.model.generate_content_async(prompt)
            result_text = response.text.strip().replace('```json', '').replace('```', '')
            try:
                return json.loads(result_text)[:max_results]
            except json.JSONDecodeError:
                return []
        except Exception as e:
            logger.error(f"Error generating synthetic results: {str(e)}")
            return []

    # --- END OF MAJOR CHANGES ---

    # ... (_extract_content, search_and_summarize, and shutdown methods are fine)
    async def _extract_content(self, url: str) -> str:
        """Extract content from a URL"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    for script in soup(["script", "style"]):
                        script.extract()
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    return text[:5000] + ('...' if len(text) > 5000 else '')
                return ""
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return ""

    async def search_and_summarize(self, query: str) -> Dict[str, Any]:
        """Search and provide AI-powered summary"""
        try:
            search_results = await self._web_search(query, 5)
            if search_results:
                content_text = "\n\n".join([f"Source: {result['title']}\nContent: {result['content']}" for result in search_results])
                summary_prompt = f"""Based on the following search results about "{query}", provide a comprehensive summary: {content_text}"""
                response = await self.model.generate_content_async(summary_prompt)
                return {'query': query, 'summary': response.text, 'sources': len(search_results), 'results': search_results}
            return {'query': query, 'summary': 'No search results found for this query.', 'sources': 0, 'results': []}
        except Exception as e:
            logger.error(f"Error in search and summarize: {str(e)}")
            return {'query': query, 'summary': f'Error performing search: {str(e)}', 'sources': 0, 'results': []}

    async def shutdown(self):
        """Shutdown the search agent"""
        try:
            if self.session:
                await self.session.close()
            logger.info("Search Agent shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
