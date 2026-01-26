import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Load env vars
load_dotenv()

print(f"Using Project: {os.getenv('LANGSMITH_PROJECT')}")

try:
    llm = ChatOpenAI()
    print("Sending a test message to OpenAI to trigger tracing...")
    response = llm.invoke([HumanMessage(content="Hello, this is a test for LangSmith tracing.")])
    print(f"Response: {response.content}")
    print("Trace should be sent to LangSmith. Please check the 'chatbot-project' project.")
except Exception as e:
    print(f"Error during LLM call: {e}")
