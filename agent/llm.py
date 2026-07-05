"""LLM 客户端封装 - 基于 Ollama SDK"""

import ollama
from typing import List, Dict, Any, Optional
import config


class LLMClient:
    """Ollama LLM 客户端封装"""
    
    def __init__(self, model: str = None):
        self.model = model or config.MODEL_NAME
    
    def chat(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Any:
        """
        调用 Ollama chat API
        
        Args:
            messages: 消息列表
            tools: 工具 schema 列表（可选）
            stream: 是否流式输出
            
        Returns:
            响应对象（流式时为迭代器）
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        if tools:
            kwargs["tools"] = tools
            
        try:
            response = ollama.chat(**kwargs)
            return response
        except ollama.ResponseError as e:
            raise ConnectionError(f"Ollama 连接失败: {e}")
        except Exception as e:
            raise RuntimeError(f"LLM 调用失败: {e}")
    
    def chat_with_tools(
        self, 
        messages: List[Dict[str, Any]], 
        tools: List[Dict]
    ) -> Any:
        """带工具调用的 chat（非流式）"""
        return self.chat(messages, tools=tools, stream=False)
    
    def chat_stream(
        self, 
        messages: List[Dict[str, Any]]
    ) -> Any:
        """流式 chat"""
        return self.chat(messages, stream=True)
