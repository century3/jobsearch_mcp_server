import logging
import os
try:
    from fastmcp import FastMCP
except ImportError:
    from fastmcp.server import FastMCP
from .tools.job import JobTools
from .tools.resume import ResumeTools

class JobSearchMCPServer:
    def __init__(self):
        self.name = "jobsearch_mcp_server"
        self.mcp = FastMCP(self.name)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.name)
        
        # Initialize tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools."""
        # Initialize tool classes
        job_tools = JobTools(self.logger)
        #resume_tools = ResumeTools()

        job_tools.register_tools(self.mcp)
        #resume_tools.register_tools(self.mcp)

    def run(self):
        """Run the MCP server."""
        host = os.getenv("FASTMCP_HOST", "127.0.0.1")
        port = int(os.getenv("FASTMCP_PORT", "18082"))
        self.mcp.run(transport="streamable-http", host=host, port=port)

def main():
    server = JobSearchMCPServer()
    server.run()

