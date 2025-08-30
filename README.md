# AI Research Assistant with MCP Protocol

A sophisticated, web-based application that automates the entire research process using a **multi-agent system** powered by **Google's Gemini LLM**.  
The assistant takes a single research query, dynamically creates a research plan, browses the web for real-time information, synthesizes the findings, and generates a comprehensive, structured report.

<img width="1911" height="916" alt="image" src="https://github.com/user-attachments/assets/91a952da-893d-4801-8490-7713d9ec5397" />
---

## ✨ Features 

- 🧠 **Multi-Agent Architecture** – Utilizes a team of specialized AI agents (Orchestrator, Search, Summarizer, Report Writer) that collaborate to fulfill complex tasks.  
- 🌐 **Real-Time Web Search** – Integrates with the Google Search API to gather up-to-the-minute information, ensuring reports are based on the latest data.  
- 🚀 **Dynamic Research Planning** – The Orchestrator agent uses an LLM to create a custom, multi-step research plan for every unique query.  
- 📄 **AI-Powered Content Generation** – Leverages the Gemini 1.5 Flash model for both concise summarization of sources and detailed generation of full reports.  
- 📊 **Interactive Frontend** – A sleek, responsive UI with real-time progress updates, providing full transparency into the research process.  
- 🎨 **Dual-Theme UI** – Includes a persistent Light/Dark mode toggle for user comfort.  
- 🕓 **Recent Query History** – Automatically saves your recent queries in the browser for easy access.  

---

## 🏛️ System Architecture

The application is built on a **modular, multi-agent architecture**, ensuring scalability and maintainability.  
Think of it as a **digital assembly line** for research.

### The Kitchen Analogy
- **The User** → Customer placing an order  
- **Research Query** → The order  
- **AI Agents** → Specialist chefs working together  
  - **ResearchOrchestrator** → Head Chef (designs the recipe/plan)  
  - **SearchAgent** → Forager (gathers fresh web sources)  
  - **SummarizerAgent** → Sauce Chef (distills the raw data)  
  - **ReportWriterAgent** → Plating Artist (produces the final report)  
- **MCP Protocol** → The digital ordering system connecting all chefs  
- **Gemini LLM** → The Master Chef’s Brain powering each agent  

---

## ⚙️ Technical Flow

```text
+----------------+      +--------------------------+      +---------------------------+
|                |      |                          |      |   ResearchOrchestrator    |
|   Frontend UI  |----->|   Backend (FastAPI)      |----->|   (Creates Plan via LLM)  |
| (Socket.IO)    |<-----|   (MCP Protocol Server)  |<-----|                           |
+----------------+      +--------------------------+      +-------------+-------------+
                                                                         | (MCP)
                                                                         |
                        +---------------------------+      +-------------v-------------+
                        |                           |      |       SearchAgent         |
                        |   Google Gemini 1.5 LLM   |<---->|   (Uses Google Search)    |
                        |       (The "Brain")       |      +-------------+-------------+
                        |                           |                    | (MCP)
                        +---------------------------+                    |
                                     ^                       +-------------v-------------+
                                     |                       |      SummarizerAgent      |
                                     +-----------------------|      (Uses LLM)           |
                                     |                       +-------------+-------------+
                                     |                                     | (MCP)
                                     |                                     |
                                     |                       +-------------v-------------+
                                     +-----------------------|     ReportWriterAgent     |
                                                             |     (Uses LLM)            |
                                                             +---------------------------+```

## 🛠️ Tech Stack

**Backend**  
- Framework: Python, FastAPI  
- Real-Time Communication: python-socketio, Uvicorn  
- AI & LLM: google-generativeai (Gemini 1.5 Flash)  
- Web Search: google-api-python-client  
- HTTP Requests: aiohttp  

**Frontend**  
- Structure: HTML5  
- Styling: CSS3  
- Interactivity: JavaScript  
- Real-Time Communication: socket.io-client  
- Markdown Rendering: marked.js  

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+  
- A Google Cloud account for API keys  

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/ai-research-assistant.git
cd ai-research-assistant

### 3. Set Up the Python Environment
```bash
# Create a virtual environment
python -m venv ai_agents_env

# Activate it
# On Windows:
ai_agents_env\Scripts\activate
# On macOS/Linux:
source ai_agents_env/bin/activate

### 5. Configure Your API Keys

Create a file named **`.env`** in the root directory of the project and add the following:

```env
# Google AI API Key for Gemini
GEMINI_API_KEY="AIzaSy...YOUR_GEMINI_API_KEY"

# Google Custom Search API Keys
GOOGLE_API_KEY="AIzaSy...YOUR_GOOGLE_CLOUD_API_KEY"
SEARCH_ENGINE_ID="YOUR_SEARCH_ENGINE_ID"

### 6. Run the Application
```bash
python main.py

You should see:

Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)

### 7. Open the Assistant

Open your browser and go to:  
👉 **http://localhost:8000**

The AI Research Assistant interface should load and connect. You’re ready to start your research!

