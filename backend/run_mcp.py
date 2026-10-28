"""Run SoftUtter's MCP server over stdio, for a client on this computer (Claude Desktop, MCP Inspector, ...).

    python run_mcp.py

It reads the same SQLite database and backend/.env as the web app, so phrases saved here show up in the app.
Nothing else may print to stdout: stdout is the protocol channel.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import store  # noqa: E402
from app.mcp_server import mcp  # noqa: E402

if __name__ == "__main__":
    store.init()
    mcp.run("stdio")
