# Job Search  MCP Project

This folder contains the MCP job-search demo used in Chapter 4.6.

## Structure

- `jobsearch-mcp-server/`: MCP server implementation
- `jobsearch-mcp-client/`: MCP client implementation
- `.venv-mcp/`: local Python environment used for MCP debugging

## Quick Start

### 1) Start MCP server (streamable HTTP)

`server.py` uses relative imports and has no `__main__` entry, so do not run `python server.py` directly.

```powershell
Set-Location "d:/AIAgent-main/第4章/4.6/jobsearch-mcp-server"
.\.venv\Scripts\python.exe -c "from jobsearch_mcp_server import main; main()"
```

MCP endpoint: `http://127.0.0.1:18082/mcp`

### 2) Run client with local stdio server mode (recommended)

```powershell
Set-Location "d:/AIAgent-main/第4章/4.6/jobsearch-mcp-client"
d:/AIAgent-main/第4章/4.6/.venv-mcp/Scripts/python.exe client.py stdio
```

### 3) Example query

```text
以下是我的简历，请帮我匹配合适的工作： 姓名：张三 专业技能：精通AI Agent ,RAG 开发 工作经验：5年 教育背景：本科 期望薪资：30K
```

## Notes

- Streamable HTTP mode may fail in some local version combinations.
- The client supports `stdio` mode as a stable fallback.
- Resume matching returns multiple ranked jobs (default 8, configurable from query).
