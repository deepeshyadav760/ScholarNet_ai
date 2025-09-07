"""
Research Orchestrator Agent - Coordinates research tasks between specialized agents
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List
import google.generativeai as genai
import math # <--- IMPORT MATH LIBRARY

from ..utils.config import Config, MCPMessageTypes, AgentTypes, TaskTypes

logger = logging.getLogger(__name__)

class ResearchOrchestrator:
    def __init__(self, mcp_server):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = AgentTypes.ORCHESTRATOR
        self.mcp_server = mcp_server
        self.active_tasks = {}
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
        logger.info(f"Research Orchestrator initialized with ID: {self.agent_id}")
    
    async def initialize(self):
        try:
            await self.mcp_server.register_agent(self.agent_id, self.agent_type, self)
            logger.info("Research Orchestrator initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Research Orchestrator: {str(e)}")
            return False

    async def handle_research_request(self, query: str, session_id: str) -> Dict[str, Any]:
        try:
            task_id = str(uuid.uuid4())
            await self._notify_progress(task_id, "Creating a custom research plan...")
            plan = await self._create_research_plan(query)
            
            self.active_tasks[task_id] = {
                'query': query, 'session_id': session_id, 'plan': plan,
                'status': 'in_progress', 'results': {},
                'created_at': asyncio.get_event_loop().time()
            }
            results = await self._execute_research_plan(task_id, plan)
            
            self.active_tasks[task_id]['status'] = 'completed'
            self.active_tasks[task_id]['results'] = results
            
            return {'task_id': task_id, 'status': 'completed', 'results': results}
        except Exception as e:
            logger.error(f"Error handling research request: {str(e)}")
            return {'task_id': 'unknown', 'status': 'error', 'error': str(e)}

    async def _create_research_plan(self, query: str) -> List[Dict[str, Any]]:
        # This function is unchanged
        try:
            prompt = f"""
            Create a detailed research plan for the query: "{query}".
            Break the research into specific tasks for agents: web_search, summarize, generate_report.
            Return a JSON array of tasks. For web_search, provide a list of 2-3 diverse search_queries.
            Example: [{{"task_type": "web_search", "search_queries": ["query1", "query2"]}}]
            """
            response = await self.model.generate_content_async(prompt)
            plan_text = response.text.strip().replace('```json', '').replace('```', '')
            try:
                import json
                plan = json.loads(plan_text)
            except:
                plan = self._create_default_plan(query)
            logger.info(f"Created research plan with {len(plan)} tasks")
            return plan
        except Exception as e:
            logger.error(f"Error creating research plan: {str(e)}")
            return self._create_default_plan(query)

    def _create_default_plan(self, query: str) -> List[Dict[str, Any]]:
        # This function is unchanged
        return [
            {'task_type': TaskTypes.WEB_SEARCH, 'search_queries': [query], 'priority': 1},
            {'task_type': TaskTypes.SUMMARIZE, 'input_source': 'search_results', 'priority': 2},
            {'task_type': TaskTypes.GENERATE_REPORT, 'input_source': 'summary', 'priority': 3}
        ]

    async def _execute_research_plan(self, task_id: str, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        # This function is unchanged
        results = {}
        try:
            sorted_tasks = sorted(plan, key=lambda x: x.get('priority', 999))
            for task in sorted_tasks:
                task_desc = task.get('description', f"Processing {task.get('task_type')}")
                await self._notify_progress(task_id, task_desc)
                
                task_type = task.get('task_type')
                if task_type == TaskTypes.WEB_SEARCH:
                    results['search_results'] = await self._delegate_search_task(task)
                elif task_type == TaskTypes.SUMMARIZE:
                    input_data = results.get(task.get('input_source', 'search_results'), [])
                    results['summary'] = await self._delegate_summarize_task(task, input_data)
                elif task_type == TaskTypes.GENERATE_REPORT:
                    input_data = results.get(task.get('input_source', 'summary'), '')
                    results['report'] = await self._delegate_report_task(task, input_data)
            return results
        except Exception as e:
            logger.error(f"Error executing research plan: {str(e)}")
            return {'error': str(e)}

    # --- START OF MAJOR CHANGES ---

    async def _get_agent_id_by_type(self, agent_type: str) -> str | None:
        all_agents = await self.mcp_server.list_agents()
        for agent_id, agent_info in all_agents.items():
            if agent_info.get('type') == agent_type:
                return agent_id
        return None

    async def _delegate_search_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Delegate search task, ensuring total results do not exceed the configured limit."""
        try:
            search_agent_id = await self._get_agent_id_by_type(AgentTypes.SEARCH)
            if not search_agent_id:
                logger.error("Search agent not available")
                return []
            
            queries = task.get('search_queries', [])
            if not queries:
                return []

            # Calculate how many results to get per query to not exceed the total limit.
            num_queries = len(queries)
            results_per_query = math.ceil(Config.MAX_SEARCH_RESULTS / num_queries)
            
            all_results = []
            for query in queries:
                # Break the loop if we already have enough results
                if len(all_results) >= Config.MAX_SEARCH_RESULTS:
                    break
                    
                message = {
                    'type': MCPMessageTypes.REQUEST,
                    'method': 'search',
                    'params': {'query': query, 'max_results': results_per_query}
                }
                response = await self.mcp_server.send_message(search_agent_id, message)
                if response and response.get('result'):
                    all_results.extend(response['result'])
            
            # Final trim to ensure we respect the exact limit
            final_results = all_results[:Config.MAX_SEARCH_RESULTS]
            logger.info(f"Aggregated {len(final_results)} search results from {num_queries} queries.")
            return final_results

        except Exception as e:
            logger.error(f"Error delegating search task: {str(e)}")
            return []

    async def _delegate_summarize_task(self, task: Dict[str, Any], input_data: List) -> str:
        """Delegate summarization task to summarizer agent."""
        try:
            summarizer_agent_id = await self._get_agent_id_by_type(AgentTypes.SUMMARIZER)
            if not summarizer_agent_id:
                logger.error("Summarizer agent not available")
                return ""
            
            if not input_data:
                logger.warning("Summarizer received no input data.")
                return ""

            message = {
                'type': MCPMessageTypes.REQUEST,
                'method': 'summarize',
                'params': {'data': input_data, 'context': self.active_tasks[list(self.active_tasks.keys())[-1]]['query']}
            }
            response = await self.mcp_server.send_message(summarizer_agent_id, message)
            return response.get('result', "") if response else ""
        except Exception as e:
            logger.error(f"Error delegating summarize task: {str(e)}")
            return ""

    async def _delegate_report_task(self, task: Dict[str, Any], input_data: str) -> str:
        """Delegate report generation to report writer agent."""
        try:
            report_agent_id = await self._get_agent_id_by_type(AgentTypes.REPORT_WRITER)
            if not report_agent_id:
                logger.error("Report writer agent not available")
                return ""

            if not input_data:
                logger.warning("Report writer received no input data.")
                return ""

            message = {
                'type': MCPMessageTypes.REQUEST,
                'method': 'generate_report',
                'params': {'summary': input_data, 'context': self.active_tasks[list(self.active_tasks.keys())[-1]]['query']}
            }
            response = await self.mcp_server.send_message(report_agent_id, message)
            return response.get('result', "") if response else ""
        except Exception as e:
            logger.error(f"Error delegating report task: {str(e)}")
            return ""

    # --- END OF MAJOR CHANGES ---

    async def _notify_progress(self, task_id: str, message: str):
        try:
            if task_id in self.active_tasks:
                session_id = self.active_tasks[task_id]['session_id']
                await self.mcp_server.broadcast_to_session(session_id, {
                    'type': 'research_progress',
                    'task_id': task_id,
                    'message': message
                })
        except Exception as e:
            logger.error(f"Error notifying progress: {str(e)}")

    async def shutdown(self):
        try:
            self.active_tasks.clear()
            logger.info("Research Orchestrator shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
