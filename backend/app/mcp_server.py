"""SoftUtter as an MCP server, so an AI client (Claude Desktop, MCP Inspector, OpenAI's Responses API, ...)
can read the phrasebook and My sounds tracker, save phrases and scaffold sentences.

Two ways to run it:
- stdio, for a client on the same computer:   python run_mcp.py
- HTTP at /mcp inside the FastAPI backend (see main.py), protected by a bearer token (MCP_TOKEN).
"""

import functools
import hmac

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from starlette.responses import JSONResponse

from . import mcp_tools as t

INSTRUCTIONS = """SoftUtter is a low-pressure speech-scaffolding app for language learners (French, Spanish, German,
Japanese, Korean, Mandarin). Use these tools to look at the learner's phrasebook and "My sounds" tracker,
save phrases for later practice, and help them say something in a target language.
Keep the tone warm and score-free: describe what is getting steady and what is worth another go. Never invent
phrases or sounds the tools did not return. Language codes: fr, es, de, ja, ko, zh."""

mcp = MCPServer("SoftUtter", instructions=INSTRUCTIONS)

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
WRITES = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False)
USES_MODEL = ToolAnnotations(read_only_hint=True, open_world_hint=True)



def register(fn, annotations):
    """Register a tool. Expected failures (bad input, a failed model call) become ToolErrors, whose message
    the client can read; anything else stays hidden from the client by the SDK."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (ValueError, RuntimeError) as exc:
            raise ToolError(str(exc)) from exc

    return mcp.tool(annotations=annotations)(wrapper)


register(t.list_languages, READ_ONLY)
register(t.list_phrases, READ_ONLY)
register(t.get_sounds, READ_ONLY)
register(t.progress_summary, READ_ONLY)
register(t.save_phrase, WRITES)
register(t.set_phrase_status, WRITES)
register(t.scaffold_sentence, USES_MODEL)


@mcp.prompt()
def warm_up(language: str = "") -> str:
    """A five-minute warm-up plan built from the learner's own phrasebook and sounds."""
    scope = f" in language code '{language}'" if language else ""
    return (
        f"Plan a five-minute SoftUtter warm-up{scope}. First call progress_summary"
        f"{f' with language={language!r}' if language else ''}. Then suggest: (1) one sound from revisit_sounds "
        "to listen for, with its tip, (2) up to three phrases from phrases_to_practice to say out loud, "
        "(3) one new sentence they could try saying and save with save_phrase. "
        "Be warm and brief. No scores, no streaks."
    )


class BearerAuth:
    """ASGI wrapper: only requests with 'Authorization: Bearer <token>' reach the MCP app."""

    def __init__(self, app, token: str):
        self.app = app
        self._expected = f"Bearer {token}".encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            got = dict(scope.get("headers") or []).get(b"authorization", b"")
            if not hmac.compare_digest(got, self._expected):
                resp = JSONResponse(
                    {"error": "unauthorized"}, status_code=401, headers={"WWW-Authenticate": "Bearer"}
                )
                await resp(scope, receive, send)
                return
        await self.app(scope, receive, send)


def http_app(token: str):
    """The MCP endpoint (POST /mcp) as an ASGI app. Stateless JSON responses suit a free, restarting host."""
    app = mcp.streamable_http_app(streamable_http_path="/mcp", json_response=True, stateless_http=True)
    return BearerAuth(app, token)
