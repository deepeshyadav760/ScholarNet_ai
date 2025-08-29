"""
Summarizer Agent - Creates concise summaries of research findings
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List
import google.generativeai as genai
from ..utils.config import Config, MCPMessageTypes, AgentTypes
from ..utils.vector_store import VectorStore

logger = logging.getLogger(__name__)

class SummarizerAgent:
    def __init__(self, mcp_server):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = AgentTypes.SUMMARIZER
        self.mcp_server = mcp_server
        self.vector_store = VectorStore(dimension=Config.VECTOR_DIMENSION)
        
        # Initialize Gemini
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
        logger.info(f"Summarizer Agent initialized with ID: {self.agent_id}")
    
    async def initialize(self):
        """Initialize the summarizer agent"""
        try:
            # Register with MCP server
            await self.mcp_server.register_agent(self.agent_id, self.agent_type, self)
            
            logger.info("Summarizer Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Summarizer Agent: {str(e)}")
            return False
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP messages"""
        try:
            message_type = message.get('type')
            method = message.get('method')
            
            if message_type == MCPMessageTypes.REQUEST:
                if method == 'summarize':
                    return await self._handle_summarize_request(message['params'])
                elif method == 'extract_key_points':
                    return await self._handle_extract_key_points(message['params'])
                elif method == 'compare_sources':
                    return await self._handle_compare_sources(message['params'])
            
            return {'error': 'Unknown method'}
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return {'error': str(e)}
    
    async def _handle_summarize_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle summarization request"""
        try:
            data = params.get('data', [])
            context = params.get('context', '')
            summary_type = params.get('type', 'comprehensive')
            max_length = params.get('max_length', 500)
            
            if not data:
                return {'error': 'Data parameter is required'}
            
            # Store data in vector store for retrieval
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    content = item.get('content', str(item))
                    title = item.get('title', f'Document {i+1}')
                else:
                    content = str(item)
                    title = f'Document {i+1}'
                
                self.vector_store.add_document(
                    doc_id=f'doc_{i}_{self.agent_id}',
                    content=content,
                    metadata={'title': title, 'source': item.get('url', 'unknown')}
                )
            
            # Generate summary
            summary = await self._generate_summary(data, context, summary_type, max_length)
            
            return {'result': summary}
            
        except Exception as e:
            logger.error(f"Error in summarize request: {str(e)}")
            return {'error': str(e)}
    
    async def _handle_extract_key_points(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle key points extraction request"""
        try:
            data = params.get('data', [])
            max_points = params.get('max_points', 5)
            
            if not data:
                return {'error': 'Data parameter is required'}
            
            key_points = await self._extract_key_points(data, max_points)
            
            return {'result': key_points}
            
        except Exception as e:
            logger.error(f"Error extracting key points: {str(e)}")
            return {'error': str(e)}
    
    async def _handle_compare_sources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle source comparison request"""
        try:
            sources = params.get('sources', [])
            
            if len(sources) < 2:
                return {'error': 'At least 2 sources required for comparison'}
            
            comparison = await self._compare_sources(sources)
            
            return {'result': comparison}
            
        except Exception as e:
            logger.error(f"Error comparing sources: {str(e)}")
            return {'error': str(e)}
    
    async def _generate_summary(self, data: List, context: str, summary_type: str, max_length: int) -> str:
        """Generate summary using Gemini AI"""
        try:
            # Prepare content text
            content_parts = []
            for item in data:
                if isinstance(item, dict):
                    title = item.get('title', 'Untitled')
                    content = item.get('content', str(item))
                    source = item.get('url', 'Unknown source')
                    content_parts.append(f"Source: {title} ({source})\nContent: {content}\n")
                else:
                    content_parts.append(f"Content: {str(item)}\n")
            
            combined_content = "\n".join(content_parts)
            
            # Create summary prompt based on type
            if summary_type == 'bullet_points':
                prompt = f"""
                Create a bullet-point summary of the following content about "{context}":
                
                {combined_content}
                
                Requirements:
                - Use clear, concise bullet points
                - Maximum {max_length} words total
                - Focus on the most important information
                - Group related points together
                - Use proper formatting
                """
            elif summary_type == 'executive':
                prompt = f"""
                Create an executive summary of the following content about "{context}":
                
                {combined_content}
                
                Requirements:
                - Professional executive summary format
                - Maximum {max_length} words
                - Include key findings and recommendations
                - Highlight critical insights
                - Use clear, business-appropriate language
                """
            else:  # comprehensive
                prompt = f"""
                Create a comprehensive summary of the following content about "{context}":
                
                {combined_content}
                
                Requirements:
                - Comprehensive but concise summary
                - Maximum {max_length} words
                - Cover all major topics and themes
                - Maintain logical flow and structure
                - Include relevant details and context
                - Identify any contradictions or gaps
                """
            
            response = await self.model.generate_content_async(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
    async def _extract_key_points(self, data: List, max_points: int) -> List[str]:
        """Extract key points from data"""
        try:
            # Prepare content
            content_text = ""
            for item in data:
                if isinstance(item, dict):
                    content_text += item.get('content', str(item)) + "\n\n"
                else:
                    content_text += str(item) + "\n\n"
            
            prompt = f"""
            Extract the {max_points} most important key points from the following content:
            
            {content_text}
            
            Requirements:
            - Return exactly {max_points} key points
            - Each point should be a complete, standalone sentence
            - Focus on the most significant and actionable information
            - Avoid redundancy between points
            - Format as a numbered list
            
            Format:
            1. First key point
            2. Second key point
            etc.
            """
            
            response = await self.model.generate_content_async(prompt)
            
            # Parse numbered list
            points = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Remove numbering/bullets
                    point = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    if point:
                        points.append(point)
            
            return points[:max_points]
            
        except Exception as e:
            logger.error(f"Error extracting key points: {str(e)}")
            return [f"Error extracting key points: {str(e)}"]
    
    async def _compare_sources(self, sources: List[Dict]) -> Dict[str, Any]:
        """Compare multiple sources"""
        try:
            # Prepare source content
            source_summaries = []
            for i, source in enumerate(sources):
                title = source.get('title', f'Source {i+1}')
                content = source.get('content', '')
                source_summaries.append(f"Source {i+1}: {title}\nContent: {content}\n")
            
            combined_sources = "\n".join(source_summaries)
            
            prompt = f"""
            Compare and analyze the following sources:
            
            {combined_sources}
            
            Provide a comparison that includes:
            1. Common themes and agreements between sources
            2. Key differences and contradictions
            3. Reliability assessment of each source
            4. Synthesis of the most credible information
            5. Gaps in information that need further research
            
            Format the response as JSON:
            {{
                "common_themes": ["theme1", "theme2"],
                "differences": ["diff1", "diff2"],
                "reliability_assessment": {{"source1": "assessment", "source2": "assessment"}},
                "synthesis": "combined analysis",
                "information_gaps": ["gap1", "gap2"]
            }}
            """
            
            response = await self.model.generate_content_async(prompt)
            
            # Parse JSON response
            try:
                import json
                result_text = response.text.strip()
                if result_text.startswith('```json'):
                    result_text = result_text[7:-3].strip()
                elif result_text.startswith('```'):
                    result_text = result_text[3:-3].strip()
                
                comparison = json.loads(result_text)
                return comparison
                
            except json.JSONDecodeError:
                # Fallback to plain text response
                return {
                    'comparison_text': response.text,
                    'sources_count': len(sources)
                }
            
        except Exception as e:
            logger.error(f"Error comparing sources: {str(e)}")
            return {'error': str(e)}
    
    async def create_themed_summary(self, data: List, themes: List[str]) -> Dict[str, str]:
        """Create summaries organized by themes"""
        try:
            themed_summaries = {}
            
            for theme in themes:
                # Find relevant content for each theme
                relevant_content = await self._find_theme_relevant_content(data, theme)
                
                if relevant_content:
                    summary = await self._generate_summary(
                        relevant_content, 
                        f"content related to {theme}", 
                        'comprehensive', 
                        300
                    )
                    themed_summaries[theme] = summary
                else:
                    themed_summaries[theme] = f"No relevant content found for theme: {theme}"
            
            return themed_summaries
            
        except Exception as e:
            logger.error(f"Error creating themed summary: {str(e)}")
            return {}
    
    async def _find_theme_relevant_content(self, data: List, theme: str) -> List:
        """Find content relevant to a specific theme"""
        try:
            relevant_items = []
            
            # Use vector store for similarity search
            if hasattr(self, 'vector_store'):
                search_results = self.vector_store.search(theme, top_k=5)
                
                for doc_id, similarity, doc_data in search_results:
                    if similarity > 0.3:  # Threshold for relevance
                        relevant_items.append({
                            'title': doc_data['metadata'].get('title', 'Untitled'),
                            'content': doc_data['content'],
                            'similarity': similarity
                        })
            
            # Fallback: simple keyword matching
            if not relevant_items:
                theme_keywords = theme.lower().split()
                
                for item in data:
                    if isinstance(item, dict):
                        content = item.get('content', '').lower()
                        if any(keyword in content for keyword in theme_keywords):
                            relevant_items.append(item)
                    else:
                        content = str(item).lower()
                        if any(keyword in content for keyword in theme_keywords):
                            relevant_items.append({'content': str(item)})
            
            return relevant_items
            
        except Exception as e:
            logger.error(f"Error finding theme-relevant content: {str(e)}")
            return []
    
    async def shutdown(self):
        """Shutdown the summarizer agent"""
        try:
            # Clear vector store
            if hasattr(self, 'vector_store'):
                self.vector_store.clear()
            
            logger.info("Summarizer Agent shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")