"""规划引擎 - 将用户任务拆解为结构化 JSON 计划"""

import json
from typing import Dict, Any, List
from .llm import LLMClient
from .output import ProgressOutput
import config


# 规划 system prompt
PLAN_SYSTEM_PROMPT = """你是一个任务规划器。将用户的任务描述拆解为结构化的 JSON 计划。

输出格式必须严格遵守以下 JSON 格式：
{
  "goal": "任务目标的一句话描述",
  "steps": [
    {
      "id": 1,
      "action": "动作类型（create_file/edit_file/run_shell/run_code/read_file）",
      "target": "操作目标（文件路径或命令）",
      "purpose": "这一步要达成什么目的"
    }
  ]
}

规则：
1. 只输出 JSON，不要输出任何其他内容
2. 步骤必须按执行顺序排列
3. 每个步骤必须可独立执行
4. action 必须是以下之一：create_file, edit_file, run_shell, run_code, read_file
5. 步骤数量应与任务复杂度匹配

示例：
用户任务："创建一个 hello.py 文件，内容打印 Hello World"
输出：
{"goal": "创建并运行 hello.py", "steps": [{"id": 1, "action": "create_file", "target": "hello.py", "purpose": "创建包含打印 Hello World 代码的 Python 文件"}, {"id": 2, "action": "run_shell", "target": "python3 hello.py", "purpose": "运行文件验证输出"}]}
"""


class PlanEngine:
    """规划引擎"""
    
    def __init__(self, llm: LLMClient, output: ProgressOutput):
        self.llm = llm
        self.output = output
    
    def generate_plan(self, task: str) -> Dict[str, Any]:
        """
        生成执行计划
        
        Args:
            task: 用户任务描述
            
        Returns:
            计划字典，包含 goal 和 steps
            
        Raises:
            ValueError: 规划失败
        """
        self.output.start_planning()
        
        messages = [
            {"role": "system", "content": PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": task}
        ]
        
        last_error = None
        for attempt in range(config.MAX_PLAN_RETRIES):
            try:
                response = self.llm.chat(messages)
                content = response.message.content
                
                # 尝试解析 JSON
                plan = self._parse_plan(content)
                self.output.planning_done(len(plan.get("steps", [])))
                return plan
                
            except json.JSONDecodeError as e:
                last_error = f"JSON 解析失败: {e}"
                # 追加格式修正提示
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user", 
                    "content": f"你的输出不是合法的 JSON。请严格按格式重新输出。错误: {e}"
                })
            except Exception as e:
                last_error = str(e)
                break
        
        raise ValueError(f"规划失败（重试 {config.MAX_PLAN_RETRIES} 次）: {last_error}")
    
    def _parse_plan(self, content: str) -> Dict[str, Any]:
        """解析模型输出为计划"""
        # 尝试提取 JSON（模型可能输出多余文字）
        content = content.strip()
        
        # 尝试找到 JSON 块
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        plan = json.loads(content)
        
        # 校验必要字段
        if "goal" not in plan:
            raise ValueError("计划缺少 'goal' 字段")
        if "steps" not in plan or not isinstance(plan["steps"], list):
            raise ValueError("计划缺少 'steps' 数组")
        
        for step in plan["steps"]:
            for key in ["id", "action", "target", "purpose"]:
                if key not in step:
                    raise ValueError(f"步骤缺少 '{key}' 字段: {step}")
        
        return plan
