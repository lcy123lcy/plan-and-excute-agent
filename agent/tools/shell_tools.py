"""Shell 命令执行工具"""

import subprocess
from .base import Tool
import config


class RunShellTool(Tool):
    """执行 Shell 命令"""
    
    @property
    def name(self) -> str:
        return "run_shell"
    
    @property
    def description(self) -> str:
        return "在本地执行 Shell 命令，返回命令输出（stdout + stderr）"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的 Shell 命令"
                }
            },
            "required": ["command"]
        }
    
    def execute(self, command: str, **kwargs) -> str:
        # 安全检查：命令黑名单
        cmd_lower = command.lower().strip()
        for dangerous in config.DANGEROUS_COMMANDS:
            if dangerous.lower() in cmd_lower:
                return f"错误: 禁止执行危险命令 '{command}'"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=config.SHELL_TIMEOUT,
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
            return f"错误: 命令执行超时（{config.SHELL_TIMEOUT}秒）"
        except Exception as e:
            return f"错误: 命令执行失败 - {e}"
