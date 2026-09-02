import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
load_dotenv()


async def create_my_agent():

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        temperature=0
    )

    client = MultiServerMCPClient(
        {
            "jouleops": {
                "transport": "stdio",
                "command": "python",
                "args": ["mcp_server.py"]
            }
        }
    )

    tools = await client.get_tools()

    agent = create_agent(
        model=model,
        tools=tools
    )

    return agent

async def ask_agent(question: str):

    agent = await create_my_agent()

    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        }
    )

    content = response["messages"][-1].content

    # Convert Gemini structured response to normal text
    if isinstance(content, list):
        text_parts = []

        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))

        return "\n".join(text_parts)

    return str(content)