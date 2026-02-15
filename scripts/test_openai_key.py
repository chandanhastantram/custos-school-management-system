import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env manually to be sure
load_dotenv(".env")

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ ERROR: OPENAI_API_KEY not found in .env")
    exit(1)

print(f"Checking key: {api_key[:10]}...")

try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5
    )
    print("✅ SUCCESS: OpenAI API is working!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ FAILED: {str(e)}")
