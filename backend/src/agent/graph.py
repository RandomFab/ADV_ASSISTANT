from langchain_mistralai import ChatMistralAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from src.agent.prompts import SYSTEM_PROMPT
import os
from dotenv import load_dotenv

load_dotenv()


async def create_agent():
    """
    Crée et retourne l'agent LangGraph connecté au serveur MCP.
    Cette fonction est async car la connexion MCP est asynchrone.
    """

    # 1. Le modèle Mistral
    llm = ChatMistralAI(
        model="mistral-small-latest",
        api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0,
    )

    # 2. Connexion au serveur MCP
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8001") + "/sse"
    mcp_client = MultiServerMCPClient(
        {
            "steelbot": {
                "url": mcp_url,
                "transport": "sse",
            }
        }
    )

    # 3. Récupération des outils MCP et conversion en outils LangChain
    tools = await mcp_client.get_tools()

    # 4. Création de l'agent avec le pattern ReAct
    agent = create_react_agent(model=llm, tools=tools, prompt=SYSTEM_PROMPT)

    return agent
