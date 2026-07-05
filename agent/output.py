"""进度输出模块 - 统一进度展示"""

import time
from typing import Optional


class ProgressOutput:
    """统一进度输出接口"""
    
    # 状态图标
    ICON_PLAN = "📋"
    ICON_EXEC = "🔧"
    ICON_DONE = "✅"
    ICON_RETRY = "⚠️"
    ICON_FAIL = "❌"
    ICON_INFO = "ℹ️"
    ICON_TOOL = "🔨"
    
    def __init__(self):
        self._step_start_time: Optional[float] = None
        self._total_start_time: Optional[float] = None
        self._step_count = 0
        self._success_count = 0
        self._fail_count = 0
    
    def start_task(self, goal: str, step_count: int) -> None:
        """任务开始"""
        self._total_start_time = time.time()
        self._step_count = step_count
        self._success_count = 0
        self._fail_count = 0
        print(f"\n{self.ICON_PLAN} 开始任务: {goal}")
        print(f"   共 {step_count} 个步骤\n")
    
    def start_planning(self) -> None:
        """规划阶段开始"""
        print(f"{self.ICON_PLAN} 规划中...")
    
    def planning_done(self, step_count: int) -> None:
        """规划完成"""
        print(f"{self.ICON_DONE} 规划完成，生成 {step_count} 个步骤\n")
    
    def start_step(self, step_id: int, description: str) -> None:
        """步骤开始"""
        self._step_start_time = time.time()
        print(f"{self.ICON_EXEC} 步骤 {step_id}: {description}")
    
    def step_done(self, step_id: int, success: bool = True) -> None:
        """步骤完成"""
        elapsed = time.time() - self._step_start_time if self._step_start_time else 0
        icon = self.ICON_DONE if success else self.ICON_FAIL
        print(f"{icon} 步骤 {step_id} 完成 ({elapsed:.1f}s)")
        if success:
            self._success_count += 1
        else:
            self._fail_count += 1
    
    def tool_calling(self, tool_name: str, arguments: dict) -> None:
        """工具调用中"""
        args_str = ", ".join(f"{k}={v!r:.30}" for k, v in arguments.items())
        print(f"  {self.ICON_TOOL} 调用工具: {tool_name}({args_str})")
    
    def retry(self, attempt: int, max_retries: int, error: str) -> None:
        """重试中"""
        print(f"  {self.ICON_RETRY} 重试 {attempt}/{max_retries}: {error}")
    
    def self_fix(self, error: str) -> None:
        """模型自修复中"""
        print(f"  {self.ICON_RETRY} 模型尝试修复: {error}")
    
    def error_escalated(self, error: str) -> None:
        """错误已上报"""
        print(f"  {self.ICON_FAIL} 错误无法自动恢复: {error}")
    
    def finish(self) -> None:
        """任务结束汇总"""
        total_time = time.time() - self._total_start_time if self._total_start_time else 0
        print(f"\n{'='*50}")
        print(f"{self.ICON_DONE} 任务完成")
        print(f"   总步骤: {self._step_count}")
        print(f"   成功: {self._success_count}")
        print(f"   失败: {self._fail_count}")
        print(f"   总耗时: {total_time:.1f}s")
        print(f"{'='*50}\n")
