"""工具基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class Tool(ABC):
    """工具基类 - 所有工具必须继承"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        工具参数 schema（符合 Ollama tool schema 格式）
        
        返回格式示例:
        {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径"
                }
            },
            "required": ["path"]
        }
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            执行结果字符串
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """获取符合 Ollama tool schema 的工具定义"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
