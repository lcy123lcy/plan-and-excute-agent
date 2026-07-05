"""工具注册表"""

from typing import Dict, List, Any, Optional
from .base import Tool
from .file_tools import ReadFileTool, WriteFileTool
from .shell_tools import RunShellTool
from .code_tools import RunCodeTool


class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_builtins()
    
    def _register_builtins(self):
        """自动注册所有内置工具"""
        builtins = [
            ReadFileTool(),
            WriteFileTool(),
            RunShellTool(),
            RunCodeTool()
        ]
        for tool in builtins:
            self.register(tool)
    
    def register(self, tool: Tool) -> None:
        """注册一个工具"""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """根据名称获取工具"""
        return self._tools.get(name)
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 Ollama schema 列表"""
        return [tool.get_schema() for tool in self._tools.values()]
    
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        执行指定工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数字典
            
        Returns:
            执行结果字符串
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return f"错误: 未知工具 '{tool_name}'"
        
        try:
            return tool.execute(**arguments)
        except Exception as e:
            return f"错误: 工具执行失败 - {e}"
    
    def list_tools(self) -> List[str]:
        """列出所有已注册工具名称"""
        return list(self._tools.keys())
