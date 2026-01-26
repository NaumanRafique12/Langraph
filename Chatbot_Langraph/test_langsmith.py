import os
from dotenv import load_dotenv
from langsmith import Client

# Load env vars
load_dotenv()

# Check env vars
print(f"LANGSMITH_TRACING: {os.getenv('LANGSMITH_TRACING')}")
print(f"LANGSMITH_ENDPOINT: {os.getenv('LANGSMITH_ENDPOINT')}")
print(f"LANGSMITH_PROJECT: {os.getenv('LANGSMITH_PROJECT')}")
# Only print start of API key for safety
api_key = os.getenv('LANGSMITH_API_KEY')
if api_key:
    print(f"LANGSMITH_API_KEY: {api_key[:10]}...")
else:
    print("LANGSMITH_API_KEY: NOT FOUND")

try:
    client = Client()
    # Try to list projects to see if the key works
    projects = list(client.list_projects())
    print(f"Successfully connected to LangSmith!")
    print(f"Projects count: {len(projects)}")
    for p in projects:
        print(f"- {p.name}")
except Exception as e:
    print(f"Error connecting to LangSmith: {e}")
