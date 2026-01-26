import sys
from dotenv import load_dotenv
print("dotenv imported successfully")
try:
    load_dotenv()
    print("load_dotenv called successfully")
except Exception as e:
    print(f"Error calling load_dotenv: {e}")
