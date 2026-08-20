import logging
import os
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
try:
    from fastmcp import FastMCP
except ImportError:
    from fastmcp.server import FastMCP
from .tools.job import JobTools
from .tools.resume import ResumeTools


class ExceptionLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logging.getLogger("jobsearch_mcp_server.http").exception(
                "Unhandled exception in HTTP middleware path=%s method=%s",
                request.url.path,
                request.method,
            )
            return JSONResponse({"error": "internal_server_error"}, status_code=500)

class JobSearchMCPServer:
    def __init__(self):
        self.name = "jobsearch_mcp_server"
        self.mcp = FastMCP(self.name)

        # Configure logging
        log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.DEBUG),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.name)

        # Explicitly expose HTTP transport internals for 502 debugging.
        for name in [
            "uvicorn",
            "uvicorn.error",
            "uvicorn.access",
            "mcp",
            "mcp.server",
            "mcp.server.streamable_http_manager",
            "fastmcp",
        ]:
            logging.getLogger(name).setLevel(logging.DEBUG)
        
        # Initialize tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools."""
        # Initialize tool classes
        job_tools = JobTools(self.logger)
        resume_tools = ResumeTools()

        job_tools.register_tools(self.mcp)
        resume_tools.register_tools(self.mcp)

    def run(self):
        """Run the MCP server."""
        host = os.getenv("FASTMCP_HOST", "127.0.0.1")
        port = int(os.getenv("FASTMCP_PORT", "18082"))
        uvicorn_log_level = os.getenv("UVICORN_LOG_LEVEL", "debug").lower()
        uvicorn_access_log = os.getenv("UVICORN_ACCESS_LOG", "1") not in {"0", "false", "False"}

        self.logger.info(
            "Starting server with host=%s port=%s uvicorn_log_level=%s access_log=%s",
            host,
            port,
            uvicorn_log_level,
            uvicorn_access_log,
        )

        try:
            self.mcp.run(
                transport="streamable-http",
                host=host,
                port=port,
                log_level="debug",
                middleware=[Middleware(ExceptionLoggingMiddleware)],
                uvicorn_config={
                    "log_level": uvicorn_log_level,
                    "access_log": uvicorn_access_log,
                },
            )
        except Exception:
            self.logger.exception("MCP server crashed with unhandled exception")
            raise

def main():
    server = JobSearchMCPServer()
    server.run()

