import asyncio
from langchain_core.messages import HumanMessage
from src.agent.graph import create_agent


async def main():
    print("Initialisation de l'agent...")
    agent = await create_agent()
    print("Agent prêt. Tape 'exit' pour quitter.\n")

    while True:
        question = input("Toi : ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        print("SteelBot : ", end="", flush=True)

        response = await agent.ainvoke(
            {"messages": [HumanMessage(content=question)]}
        )

        # Le dernier message de la liste est la réponse finale de l'agent
        final_message = response["messages"][-1]
        print(final_message.content)
        print()


if __name__ == "__main__":
    asyncio.run(main())