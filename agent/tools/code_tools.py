"""代码执行工具"""

import subprocess
import tempfile
import os
from .base import Tool
import config


class RunCodeTool(Tool):
    """执行 Python 或 Node.js 代码"""
    
    @property
    def name(self) -> str:
        return "run_code"
    
    @property
    def description(self) -> str:
        return "执行 Python 或 Node.js 代码片段，返回执行输出"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的代码内容"
                },
                "language": {
                    "type": "string",
                    "enum": ["python", "nodejs"],
                    "description": "代码语言（python 或 nodejs）",
                    "default": "python"
                }
            },
            "required": ["code"]
        }
    
    def execute(self, code: str, language: str = "python", **kwargs) -> str:
        # 根据语言选择解释器
        if language == "nodejs":
            cmd = ["node", "--eval", code]
            ext = ".js"
        else:
            cmd = ["python3", "-c", code]
            ext = ".py"
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.CODE_TIMEOUT,
                cwd=config.WORK_DIR
            )
            
            output_parts = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                output_parts.append(f"[stderr] {result.stderr}")
            if result.returncode != 0:
                output_parts.append(f"[exit code: {result.returncode}]")
            
            return "\n".join(output_parts) if output_parts else "(无输出)"
            
        except subprocess.TimeoutExpired:
            return f"错误: 代码执行超时（{config.CODE_TIMEOUT}秒）"
        except FileNotFoundError:
            return f"错误: 找不到 {language} 解释器"
        except Exception as e:
            return f"错误: 代码执行失败 - {e}"
