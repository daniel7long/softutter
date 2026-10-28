"""Ask a question about your SoftUtter practice through OpenAI's Responses API and the deployed MCP server.

You only need an OpenAI API key. OpenAI's servers call your MCP endpoint, so it must be reachable from the
internet (your Render URL), not localhost.

PowerShell, from the backend folder with the venv active:

    $env:SOFTUTTER_MCP_URL = "https://<your-service>.onrender.com/mcp"
    $env:MCP_TOKEN = "<the same MCP_TOKEN you set on Render>"
    python examples/ask_softutter.py "What should I practice in French today?"

Optional: $env:OPENAI_MCP_MODEL to pick another model (default gpt-4.1-mini).
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

url = os.getenv("SOFTUTTER_MCP_URL", "").strip()
token = os.getenv("MCP_TOKEN", "").strip()
if not url or not token:
    sys.exit("Set SOFTUTTER_MCP_URL (https://.../mcp) and MCP_TOKEN first. See the top of this file.")

question = " ".join(sys.argv[1:]) or "Give me a five-minute warm-up from my phrasebook and sounds."

response = OpenAI().responses.create(
    model=os.getenv("OPENAI_MCP_MODEL", "gpt-4.1-mini"),
    input=question,
    tools=[
        {
            "type": "mcp",
            "server_label": "softutter",
            "server_url": url,
            "headers": {"Authorization": f"Bearer {token}"},
            "require_approval": "never",
        }
    ],
)

for item in response.output:
    if getattr(item, "type", "") == "mcp_call":
        print(f"[tool] {item.name}({item.arguments})")
print()
print(response.output_text)
