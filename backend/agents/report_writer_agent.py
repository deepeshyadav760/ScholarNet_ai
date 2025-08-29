"""
Report Writer Agent - Generates comprehensive research reports
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime
import google.generativeai as genai
from ..utils.config import Config, MCPMessageTypes, AgentTypes

logger = logging.getLogger(__name__)

class ReportWriterAgent:
    def __init__(self, mcp_server):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = AgentTypes.REPORT_WRITER
        self.mcp_server = mcp_server
        self.report_templates = {
            'academic': self._get_academic_template(),
            'business': self._get_business_template(),
            'technical': self._get_technical_template(),
            'executive': self._get_executive_template()
        }
        
        # Initialize Gemini
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
        logger.info(f"Report Writer Agent initialized with ID: {self.agent_id}")
    
    async def initialize(self):
        """Initialize the report writer agent"""
        try:
            # Register with MCP server
            await self.mcp_server.register_agent(self.agent_id, self.agent_type, self)
            
            logger.info("Report Writer Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Report Writer Agent: {str(e)}")
            return False
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP messages"""
        try:
            message_type = message.get('type')
            method = message.get('method')
            
            if message_type == MCPMessageTypes.REQUEST:
                if method == 'generate_report':
                    return await self._handle_generate_report(message['params'])
                elif method == 'format_report':
                    return await self._handle_format_report(message['params'])
                elif method == 'create_executive_summary':
                    return await self._handle_executive_summary(message['params'])
            
            return {'error': 'Unknown method'}
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return {'error': str(e)}
    
    async def _handle_generate_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report generation request"""
        try:
            summary = params.get('summary', '')
            context = params.get('context', '')
            report_type = params.get('type', 'business')
            title = params.get('title', 'Research Report')
            
            if not summary:
                return {'error': 'Summary parameter is required'}
            
            # Generate comprehensive report
            report = await self._generate_report(summary, context, report_type, title)
            
            return {'result': report}
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {'error': str(e)}
    
    async def _handle_format_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report formatting request"""
        try:
            content = params.get('content', '')
            format_type = params.get('format', 'markdown')
            
            if not content:
                return {'error': 'Content parameter is required'}
            
            formatted_report = await self._format_report(content, format_type)
            
            return {'result': formatted_report}
            
        except Exception as e:
            logger.error(f"Error formatting report: {str(e)}")
            return {'error': str(e)}
    
    async def _handle_executive_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle executive summary creation request"""
        try:
            full_report = params.get('report', '')
            max_length = params.get('max_length', 300)
            
            if not full_report:
                return {'error': 'Report parameter is required'}
            
            exec_summary = await self._create_executive_summary(full_report, max_length)
            
            return {'result': exec_summary}
            
        except Exception as e:
            logger.error(f"Error creating executive summary: {str(e)}")
            return {'error': str(e)}
    
    async def _generate_report(self, summary: str, context: str, report_type: str, title: str) -> str:
        """Generate comprehensive report using Gemini AI"""
        try:
            template = self.report_templates.get(report_type, self.report_templates['business'])
            
            prompt = f"""
            Generate a comprehensive {report_type} research report based on the following information:
            
            Title: {title}
            Context: {context}
            Summary Data: {summary}
            
            Use this template structure:
            {template}
            
            Requirements:
            - Professional tone and language
            - Well-structured with clear sections
            - Include actionable insights and recommendations
            - Cite key findings appropriately
            - Use proper formatting (markdown)
            - Length: 1000-1500 words
            - Include current date: {datetime.now().strftime('%B %d, %Y')}
            
            Make the report comprehensive, insightful, and actionable.
            """
            
            response = await self.model.generate_content_async(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return f"# Error Generating Report\n\nAn error occurred while generating the report: {str(e)}"
    
    async def _format_report(self, content: str, format_type: str) -> str:
        """Format report in specified format"""
        try:
            if format_type == 'html':
                return await self._convert_to_html(content)
            elif format_type == 'pdf_ready':
                return await self._format_for_pdf(content)
            elif format_type == 'plain_text':
                return await self._convert_to_plain_text(content)
            else:  # markdown (default)
                return content
                
        except Exception as e:
            logger.error(f"Error formatting report: {str(e)}")
            return content
    
    async def _convert_to_html(self, markdown_content: str) -> str:
        """Convert markdown to HTML"""
        try:
            prompt = f"""
            Convert the following markdown content to clean, professional HTML:
            
            {markdown_content}
            
            Requirements:
            - Use semantic HTML tags
            - Include proper CSS styling (embedded)
            - Professional appearance
            - Responsive design
            - Clean, readable layout
            
            Return only the complete HTML document.
            """
            
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error converting to HTML: {str(e)}")
            return f"<html><body><pre>{markdown_content}</pre></body></html>"
    
    async def _format_for_pdf(self, content: str) -> str:
        """Format content for PDF generation"""
        try:
            prompt = f"""
            Format the following content for PDF generation with proper page breaks and structure:
            
            {content}
            
            Requirements:
            - Add appropriate page breaks
            - Format headers and footers
            - Include table of contents
            - Professional typography markers
            - Clear section divisions
            
            Use markdown with PDF formatting annotations.
            """
            
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error formatting for PDF: {str(e)}")
            return content
    
    async def _convert_to_plain_text(self, markdown_content: str) -> str:
        """Convert markdown to plain text"""
        try:
            # Simple markdown to text conversion
            import re
            
            text = markdown_content
            
            # Remove markdown formatting
            text = re.sub(r'#{1,6}\s*', '', text)  # Headers
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
            text = re.sub(r'\*(.*?)\*', r'\1', text)  # Italic
            text = re.sub(r'`(.*?)`', r'\1', text)  # Code
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
            text = re.sub(r'^\s*-\s*', '• ', text, flags=re.MULTILINE)  # Lists
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error converting to plain text: {str(e)}")
            return markdown_content
    
    async def _create_executive_summary(self, full_report: str, max_length: int) -> str:
        """Create executive summary from full report"""
        try:
            prompt = f"""
            Create a concise executive summary from the following full report:
            
            {full_report}
            
            Requirements:
            - Maximum {max_length} words
            - Focus on key findings and recommendations
            - Use bullet points for clarity
            - Include actionable insights
            - Professional tone
            - Highlight most critical information
            
            Format as a proper executive summary with sections:
            - Key Findings
            - Recommendations
            - Next Steps
            """
            
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error creating executive summary: {str(e)}")
            return f"Error creating executive summary: {str(e)}"
    
    def _get_academic_template(self) -> str:
        """Get academic report template"""
        return """
        # {title}
        
        **Date:** {date}
        **Research Context:** {context}
        
        ## Abstract
        [Brief overview of the research and key findings]
        
        ## Introduction
        [Background and research objectives]
        
        ## Literature Review
        [Review of existing research and sources]
        
        ## Methodology
        [Research approach and data collection methods]
        
        ## Findings
        [Detailed presentation of research results]
        
        ## Analysis
        [Interpretation of findings and implications]
        
        ## Conclusions
        [Summary of key insights and contributions]
        
        ## Recommendations
        [Actionable recommendations based on findings]
        
        ## References
        [List of sources and citations]
        """
    
    def _get_business_template(self) -> str:
        """Get business report template"""
        return """
        # {title}
        
        **Date:** {date}
        **Prepared for:** Business Decision Makers
        
        ## Executive Summary
        [High-level overview of key findings and recommendations]
        
        ## Background
        [Context and business problem addressed]
        
        ## Key Findings
        [Main discoveries and insights from research]
        
        ## Market Analysis
        [Relevant market trends and competitive landscape]
        
        ## Opportunities & Challenges
        [Identified opportunities and potential obstacles]
        
        ## Strategic Recommendations
        [Actionable business recommendations]
        
        ## Implementation Plan
        [Steps for putting recommendations into action]
        
        ## Risk Assessment
        [Potential risks and mitigation strategies]
        
        ## Conclusion
        [Summary and next steps]
        """
    
    def _get_technical_template(self) -> str:
        """Get technical report template"""
        return """
        # {title}
        
        **Date:** {date}
        **Technical Domain:** {context}
        
        ## Overview
        [Technical summary and scope]
        
        ## Technical Background
        [Relevant technical context and prerequisites]
        
        ## Analysis
        [Detailed technical analysis of findings]
        
        ## Technical Specifications
        [Relevant specifications and requirements]
        
        ## Performance Metrics
        [Quantitative analysis and benchmarks]
        
        ## Implementation Details
        [Technical implementation considerations]
        
        ## Testing & Validation
        [Validation methods and test results]
        
        ## Technical Recommendations
        [Technical best practices and recommendations]
        
        ## Future Considerations
        [Scalability and future technical directions]
        
        ## Appendices
        [Technical details and supporting data]
        """
    
    def _get_executive_template(self) -> str:
        """Get executive report template"""
        return """
        # {title}
        
        **Date:** {date}
        **For Executive Review**
        
        ## Executive Summary
        [Critical insights for decision-making - 2-3 paragraphs max]
        
        ## Strategic Overview
        [High-level strategic implications]
        
        ## Key Performance Indicators
        [Relevant metrics and performance data]
        
        ## Critical Findings
        [Most important discoveries that impact business]
        
        ## Strategic Recommendations
        [Priority actions for leadership consideration]
        
        ## Resource Requirements
        [Investment and resource implications]
        
        ## Timeline & Milestones
        [Implementation timeline and key milestones]
        
        ## ROI & Impact Assessment
        [Expected return on investment and business impact]
        
        ## Next Steps
        [Immediate actions required]
        """
    
    async def generate_multi_format_report(self, summary: str, context: str, title: str) -> Dict[str, str]:
        """Generate report in multiple formats"""
        try:
            # Generate base report
            base_report = await self._generate_report(summary, context, 'business', title)
            
            # Generate different formats
            formats = {
                'markdown': base_report,
                'html': await self._convert_to_html(base_report),
                'plain_text': await self._convert_to_plain_text(base_report),
                'executive_summary': await self._create_executive_summary(base_report, 300)
            }
            
            return formats
            
        except Exception as e:
            logger.error(f"Error generating multi-format report: {str(e)}")
            return {'error': str(e)}
    
    async def create_comparative_report(self, summaries: List[Dict[str, Any]], title: str) -> str:
        """Create comparative analysis report"""
        try:
            prompt = f"""
            Create a comparative analysis report titled "{title}" based on multiple research summaries:
            
            {summaries}
            
            Requirements:
            - Compare and contrast findings across sources
            - Identify common themes and discrepancies
            - Provide synthesis of information
            - Include comparative tables where appropriate
            - Highlight most reliable and significant findings
            - Professional format with clear sections
            
            Structure:
            1. Executive Summary
            2. Comparative Analysis
            3. Key Similarities
            4. Major Differences
            5. Synthesis & Conclusions
            6. Recommendations
            """
            
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error creating comparative report: {str(e)}")
            return f"# Error Creating Comparative Report\n\nError: {str(e)}"
    
    async def add_visualizations_suggestions(self, report_content: str) -> str:
        """Add suggestions for data visualizations"""
        try:
            prompt = f"""
            Analyze the following report and suggest appropriate data visualizations:
            
            {report_content}
            
            For each suggested visualization:
            - Type of chart/graph
            - Data to visualize
            - Purpose and insights it would provide
            - Placement in report
            
            Add these suggestions as a "Recommended Visualizations" section.
            """
            
            response = await self.model.generate_content_async(prompt)
            
            # Append visualizations section to report
            enhanced_report = report_content + "\n\n---\n\n" + response.text
            
            return enhanced_report
            
        except Exception as e:
            logger.error(f"Error adding visualization suggestions: {str(e)}")
            return report_content
    
    async def shutdown(self):
        """Shutdown the report writer agent"""
        try:
            # Clear templates and cached data
            self.report_templates.clear()
            
            logger.info("Report Writer Agent shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")