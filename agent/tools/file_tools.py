"""文件读写工具"""

import os
from .base import Tool
import config


class ReadFileTool(Tool):
    """读取文件内容"""
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "读取指定路径文件的内容，返回文件文本"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径（相对或绝对）"
                }
            },
            "required": ["path"]
        }
    
    def execute(self, path: str, **kwargs) -> str:
        # 安全检查
        abs_path = os.path.abspath(path)
        for dangerous in config.DANGEROUS_PATHS:
            if abs_path.startswith(dangerous):
                return f"错误: 禁止访问系统路径 {dangerous}"
        
        if not os.path.exists(abs_path):
            return f"错误: 文件不存在 {abs_path}"
        
        if not os.path.isfile(abs_path):
            return f"错误: 不是文件 {abs_path}"
        
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except Exception as e:
            return f"错误: 读取文件失败 - {e}"


class WriteFileTool(Tool):
    """写入文件内容"""
    
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "将内容写入指定路径的文件，如果文件不存在则创建，存在则覆盖"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径（相对或绝对）"
                },
                "content": {
                    "type": "string",
                    "description": "要写入的文件内容"
                }
            },
            "required": ["path", "content"]
        }
    
    def execute(self, path: str, content: str, **kwargs) -> str:
        # 安全检查
        abs_path = os.path.abspath(path)
        for dangerous in config.DANGEROUS_PATHS:
            if abs_path.startswith(dangerous):
                return f"错误: 禁止写入系统路径 {dangerous}"
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"成功写入文件: {abs_path}"
        except Exception as e:
            return f"错误: 写入文件失败 - {e}"
