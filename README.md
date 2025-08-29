# AI Research Assistant with MCP Protocol

A sophisticated multi-agent AI research system that uses the Model Context Protocol (MCP) for seamless communication between specialized agents, powered by Google Gemini API.

## Features

- **Multi-Agent Architecture**: Specialized agents for different research tasks
- **MCP Protocol**: Standardized communication between agents
- **Google Gemini Integration**: Free and powerful AI capabilities
- **Web Interface**: Modern React-based frontend
- **Real-time Communication**: WebSocket support for live updates
- **Vector Storage**: Efficient document storage and retrieval

## Architecture

### Agents
- **Research Orchestrator**: Coordinates research tasks between agents
- **Search Agent**: Handles web searches and data collection
- **Summarizer Agent**: Creates concise summaries of research findings
- **Report Writer**: Generates comprehensive research reports

### MCP Protocol Implementation
- Standardized message passing between agents
- Event-driven architecture
- Error handling and retry mechanisms
- Resource management and cleanup

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

2. **Environment Variables**:
   Create a `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   MCP_SERVER_PORT=8000
   WS_PORT=3001
   ```

3. **Get Gemini API Key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add it to your `.env` file

4. **Run the Application**:
   ```bash
   # Start Python backend
   python main.py
   
   # Start Node.js frontend server (in another terminal)
   npm start
   ```

## Usage

1. Open `http://localhost:8000` in your browser
2. Enter your research query
3. The system will automatically:
   - Route your query to appropriate agents
   - Conduct web searches
   - Analyze and summarize findings
   - Generate a comprehensive report

## MCP Protocol Benefits

- **Interoperability**: Agents can communicate regardless of implementation language
- **Scalability**: Easy to add new agents or scale existing ones
- **Reliability**: Built-in error handling and message persistence
- **Security**: Secure message passing with authentication

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with multiple agents
5. Submit a pull request

## License

MIT License - see LICENSE file for details# ScholarNet_ai
