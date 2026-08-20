import asyncio
from contextlib import AsyncExitStack
from typing import Optional
import sys
import os
from pathlib import Path

from fastmcp.client import Client as FastMCPClient
from fastmcp.client.transports.stdio import StdioTransport


class MCPClient:
    def __init__(self):
        self.session: Optional[FastMCPClient] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, target: str):
        """Connect to MCP server via HTTP URL or local stdio transport."""
        if target.lower() == "stdio":
            workspace_root = Path(__file__).resolve().parents[3]
            server_dir = workspace_root / "第4章" / "4.6" / "jobsearch-mcp-server"
            python_exe = str((workspace_root / "第4章" / "4.6" / ".venv-mcp" / "Scripts" / "python.exe").resolve())
            server_boot = (
                "from jobsearch_mcp_server.server import JobSearchMCPServer; "
                "s=JobSearchMCPServer(); s.mcp.run(transport='stdio')"
            )

            transport = StdioTransport(
                command=python_exe,
                args=["-c", server_boot],
                cwd=str(server_dir),
                env={**os.environ, "PYTHONPATH": "src"},
            )
            self.session = await self.exit_stack.enter_async_context(FastMCPClient(transport))
        else:
            # Some local environments inject proxy settings that break localhost MCP
            # streamable-http calls with upstream 502. Force direct loopback access.
            if "127.0.0.1" in target or "localhost" in target:
                for k in [
                    "HTTP_PROXY",
                    "HTTPS_PROXY",
                    "ALL_PROXY",
                    "http_proxy",
                    "https_proxy",
                    "all_proxy",
                ]:
                    os.environ.pop(k, None)
                os.environ["NO_PROXY"] = "127.0.0.1,localhost"
                os.environ["no_proxy"] = "127.0.0.1,localhost"

            self.session = await self.exit_stack.enter_async_context(FastMCPClient(target))

        tools = await self.session.list_tools()
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Route user query to the proper MCP tool flow."""
        if self.session is None:
            return "MCP session is not connected."

        tools = await self.session.list_tools()
        if not tools:
            return "No tools available from server."

        tool_names = [tool.name for tool in tools]
        resume = query
        query_path = Path(query)

        if "get_word_by_filepath" in tool_names and query_path.suffix.lower() == ".docx":
            filepath = str(query_path.resolve()) if query_path.exists() else query
            word_result = await self.session.call_tool(
                "get_word_by_filepath",
                {"filepath": filepath},
            )
            resume = self._tool_result_to_text(word_result)
            print(f"\nLoaded resume from: {filepath}")

        # Prefer resume matching flow whenever the server provides this tool.
        # This avoids accidentally returning a raw full job list for resume queries.
        if "get_job_by_resume" in tool_names and "get_joblist_by_expect_job" in tool_names:
            jobs_result = await self.session.call_tool("get_joblist_by_expect_job", {"job": "AI Agent"})
            jobs_text = self._tool_result_to_text(jobs_result)

            match_result = await self.session.call_tool(
                "get_job_by_resume",
                {"jobs": jobs_text, "resume": resume},
            )
            return self._tool_result_to_text(match_result)

        if "get_joblist_by_expect_job" in tool_names:
            result = await self.session.call_tool("get_joblist_by_expect_job", {"job": query})
            return self._tool_result_to_text(result)

        tool = tools[0]
        result = await self.session.call_tool(tool.name, {"job": query})
        return self._tool_result_to_text(result)

    @staticmethod
    def _tool_result_to_text(result) -> str:
        content = getattr(result, "content", None)
        if content is None:
            return str(result)

        if isinstance(content, list):
            parts = []
            for item in content:
                text = getattr(item, "text", None)
                if text is not None:
                    parts.append(str(text))
                else:
                    parts.append(str(item))
            return "\n".join(parts)

        return str(content)

    async def chat_loop(self):
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == "quit":
                    break
                response = await self.process_query(query)
                print("\n" + response)
            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <server_url|stdio>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())