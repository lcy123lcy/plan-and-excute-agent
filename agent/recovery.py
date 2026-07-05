"""错误恢复模块 - 三级降级状态机"""

import time
from typing import Optional, Callable, Any
from enum import Enum
import config
from .output import ProgressOutput


class RecoveryState(Enum):
    """错误恢复状态"""
    IDLE = "idle"                    # 空闲
    TOOL_CALL_FAILED = "failed"      # 工具调用失败
    RETRY = "retry"                  # 第一级：自动重试
    SELF_FIX = "self_fix"           # 第二级：模型自修复
    ESCALATE = "escalate"           # 第三级：上报用户


class ErrorRecovery:
    """三级降级错误恢复管理器"""
    
    def __init__(self, output: ProgressOutput):
        self.state = RecoveryState.IDLE
        self.retry_count = 0
        self.error_chain: list = []
        self.output = output
    
    def reset(self) -> None:
        """重置状态（新步骤开始时调用）"""
        self.state = RecoveryState.IDLE
        self.retry_count = 0
        self.error_chain = []
    
    def is_recoverable(self, error: str) -> bool:
        """判断错误是否可恢复"""
        # 权限不足等直接不可恢复
        non_recoverable = ["permission denied", "forbidden", "unauthorized"]
        return not any(kw in error.lower() for kw in non_recoverable)
    
    def record_error(self, error: str) -> None:
        """记录错误到错误链"""
        self.error_chain.append({
            "error": error,
            "state": self.state.value,
            "retry_count": self.retry_count
        })
    
    def handle_error(
        self,
        error: str,
        retry_fn: Optional[Callable] = None,
        self_fix_fn: Optional[Callable] = None
    ) -> str:
        """
        处理工具执行错误，返回处理结果
        
        Args:
            error: 错误信息
            retry_fn: 重试执行函数（无参数，返回结果字符串）
            self_fix_fn: 模型自修复函数（接收错误信息，返回结果字符串）
            
        Returns:
            处理结果: "recovered" | "self_fix" | "escalated"
        """
        self.record_error(error)
        
        # 检查是否可恢复
        if not self.is_recoverable(error):
            self.state = RecoveryState.ESCALATE
            self.output.error_escalated(error)
            return "escalated"
        
        # 第一级：自动重试
        if self.retry_count < config.MAX_RETRIES:
            self.state = RecoveryState.RETRY
            self.retry_count += 1
            self.output.retry(self.retry_count, config.MAX_RETRIES, error)
            time.sleep(config.RETRY_DELAY)
            
            if retry_fn:
                result = retry_fn()
                if not result.startswith("错误"):
                    self.state = RecoveryState.IDLE
                    self.retry_count = 0
                    return "recovered"
                # 重试仍然失败，继续记录
                self.record_error(result)
            
            # 如果还有重试机会，继续重试
            if self.retry_count < config.MAX_RETRIES:
                return self.handle_error(error, retry_fn, self_fix_fn)
        
        # 第二级：模型自修复
        if self_fix_fn:
            self.state = RecoveryState.SELF_FIX
            self.output.self_fix(error)
            result = self_fix_fn(error)
            if not result.startswith("错误") and "无法修复" not in result:
                self.state = RecoveryState.IDLE
                self.retry_count = 0
                return "self_fix"
        
        # 第三级：上报
        self.state = RecoveryState.ESCALATE
        self.output.error_escalated(error)
        return "escalated"
    
    def get_error_summary(self) -> str:
        """获取错误摘要"""
        if not self.error_chain:
            return "无错误"
        
        last_error = self.error_chain[-1]["error"]
        return (
            f"错误摘要: 共 {len(self.error_chain)} 个错误\n"
            f"最后错误: {last_error}\n"
            f"状态: {self.state.value}"
        )
