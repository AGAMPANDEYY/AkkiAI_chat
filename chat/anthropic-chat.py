import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('ANTHROPIC_API')
if not api_key:
    raise ValueError("ANTHROPIC_API environment variable not found. Please set it with your API key.")

client= anthropic.Anthropic(api_key=api_key)
MODEL_NAME="claude-3-haiku-20240307"

message = client.messages.create(
    model=MODEL_NAME,
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude"}
    ]
)