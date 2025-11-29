from typing import Optional, Dict, Any
import httpx
from config import settings


class MCPClient:
    def __init__(self, server_url: Optional[str] = None, timeout: int = 30):
        self.server_url = server_url or settings.mcp_server_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Call an MCP tool on the server."""
        if not self.server_url:
            raise ValueError("MCP server URL not configured")
        
        response = await self.client.post(
            f"{self.server_url}/tools/{tool_name}",
            json=parameters
        )
        response.raise_for_status()
        return response.json()
    
    async def list_tools(self) -> list:
        """List available tools from MCP server."""
        if not self.server_url:
            return []
        
        response = await self.client.get(f"{self.server_url}/tools")
        response.raise_for_status()
        return response.json()
    
    async def get_context(self, context_id: str) -> Dict[str, Any]:
        """Retrieve context from MCP server."""
        if not self.server_url:
            raise ValueError("MCP server URL not configured")
        
        response = await self.client.get(f"{self.server_url}/context/{context_id}")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()


mcp_client = MCPClient()
