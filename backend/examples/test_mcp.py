"""Check a SoftUtter MCP server from the command line. Standard library only, so nothing to install.

From the backend folder:

    python examples/test_mcp.py
    python examples/test_mcp.py --save "I would like a coffee with milk, please" --lang fr

It asks for your MCP_TOKEN (typing is hidden). To skip the prompt, set $env:MCP_TOKEN first.
The server URL defaults to https://softutter.onrender.com/mcp; override with --url or $env:SOFTUTTER_MCP_URL.
A sleeping Render free instance can take about a minute to answer the first request.
"""

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "https://softutter.onrender.com/mcp"


def rpc(url, token, method, params=None, rid=1):
    payload = {"jsonrpc": "2.0", "id": rid, "method": method}
    if params:
        payload["params"] = params
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def call_tool(url, token, name, arguments):
    status, body = rpc(url, token, "tools/call", {"name": name, "arguments": arguments}, rid=3)
    if status != 200 or not isinstance(body, dict) or "result" not in body:
        return False, f"HTTP {status}: {body}"
    result = body["result"]
    text = result["content"][0]["text"] if result.get("content") else ""
    return not result.get("isError"), text


def main():
    ap = argparse.ArgumentParser(description="Test a SoftUtter MCP server.")
    ap.add_argument("--url", default=os.getenv("SOFTUTTER_MCP_URL", DEFAULT_URL))
    ap.add_argument("--save", metavar="TEXT", help="also save this sentence to the phrasebook")
    ap.add_argument("--lang", default="fr", help="language code for --save (fr, es, de, ja, ko, zh)")
    args = ap.parse_args()

    token = os.getenv("MCP_TOKEN", "").strip() or getpass.getpass("MCP_TOKEN (hidden): ").strip()
    print(f"Server: {args.url}\n")

    status, _ = rpc(args.url, "", "tools/list")
    print(f"1. Without a token: HTTP {status}", "(good, it is locked)" if status == 401 else "(expected 401!)")

    status, body = rpc(args.url, token, "tools/list")
    if status == 401:
        sys.exit("2. The token was rejected. Check MCP_TOKEN on Render matches what you typed.")
    if status != 200 or not isinstance(body, dict):
        sys.exit(f"2. Unexpected answer: HTTP {status}: {body}")
    names = [t["name"] for t in body["result"]["tools"]]
    print(f"2. With the token: {len(names)} tools -> {', '.join(names)}")

    ok, text = call_tool(args.url, token, "progress_summary", {})
    print("3. progress_summary:", "ok" if ok else "FAILED")
    print(text if not ok else json.dumps(json.loads(text), ensure_ascii=False, indent=2))

    if args.save:
        ok, text = call_tool(args.url, token, "save_phrase", {"language": args.lang, "text": args.save})
        print("\n4. save_phrase:", "ok" if ok else "FAILED")
        print(text if not ok else json.dumps(json.loads(text), ensure_ascii=False, indent=2))
        if ok:
            print("\nNow refresh the Phrasebook on your website: the phrase should be there.")


if __name__ == "__main__":
    main()
