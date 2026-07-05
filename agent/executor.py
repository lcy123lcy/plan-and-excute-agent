"""执行循环 - 按计划逐步执行"""

from typing import Dict, Any, List, Optional
from .llm import LLMClient
from .tools import ToolRegistry
from .recovery import ErrorRecovery
from .output import ProgressOutput


# 执行步骤 system prompt
EXEC_STEP_PROMPT = """你是一个任务执行助手。当前正在执行一个步骤，你需要通过调用工具来完成它。

当前步骤信息：
- 步骤 ID: {step_id}
- 动作: {action}
- 目标: {target}
- 目的: {purpose}

可用工具：read_file, write_file, run_shell, run_code

规则：
1. 通过调用工具来完成当前步骤
2. 如果一步需要多次工具调用，依次调用
3. 完成后输出一句简短的完成总结
4. 如果遇到无法解决的错误，输出错误描述
"""


class Executor:
    """执行循环"""
    
    def __init__(
        self, 
        llm: LLMClient, 
        registry: ToolRegistry, 
        output: ProgressOutput
    ):
        self.llm = llm
        self.registry = registry
        self.output = output
        self.recovery = ErrorRecovery(output)
    
    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整计划
        
        Args:
            plan: 包含 goal 和 steps 的计划字典
            
        Returns:
            执行结果摘要
        """
        goal = plan["goal"]
        steps = plan["steps"]
        
        self.output.start_task(goal, len(steps))
        
        results = []
        for step in steps:
            result = self._execute_step(step, previous_results=results)
            results.append(result)
        
        self.output.finish()
        
        return {
            "goal": goal,
            "total_steps": len(steps),
            "results": results
        }
    
    def _execute_step(
        self, 
        step: Dict[str, Any], 
        previous_results: List[Dict]
    ) -> Dict[str, Any]:
        """执行单个步骤"""
        step_id = step["id"]
        description = f"{step['action']} {step['target']}"
        
        self.output.start_step(step_id, description)
        self.recovery.reset()
        
        # 构建消息，包含上下文
        messages = self._build_step_messages(step, previous_results)
        tools = self.registry.get_tool_schemas()
        
        step_success = True
        max_tool_calls = 10  # 防止无限循环
        
        for _ in range(max_tool_calls):
            try:
                response = self.llm.chat_with_tools(messages, tools)
                msg = response.message
                
                # 检查是否有工具调用
                if not hasattr(msg, 'tool_calls') or not msg.tool_calls:
                    # 没有工具调用，步骤完成
                    break
                
                # 处理工具调用
                # 先追加 assistant 消息
                messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in msg.tool_calls
                    ]
                })
                
                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    arguments = tc.function.arguments
                    
                    self.output.tool_calling(tool_name, arguments)
                    
                    # 执行工具（带错误恢复）
                    result = self._execute_tool_with_recovery(
                        tool_name, arguments, messages, tools
                    )
                    
                    # 追加工具结果
                    messages.append({
                        "role": "tool",
                        "name": tool_name,
                        "content": result
                    })
            
            except Exception as e:
                step_success = False
                break
        
        self.output.step_done(step_id, success=step_success)
        
        return {
            "step_id": step_id,
            "success": step_success,
            "description": description
        }
    
    def _execute_tool_with_recovery(
        self, 
        tool_name: str, 
        arguments: Dict,
        messages: List,
        tools: List
    ) -> str:
        """带错误恢复的工具执行"""
        def retry_fn():
            return self.registry.execute(tool_name, arguments)
        
        def self_fix_fn(error: str):
            # 将错误返回给模型，让它提出修复方案
            fix_messages = messages + [
                {"role": "user", "content": f"工具 {tool_name} 执行失败: {error}。请提出修复方案并重新调用工具。"}
            ]
            try:
                resp = self.llm.chat_with_tools(fix_messages, tools)
                if hasattr(resp.message, 'tool_calls') and resp.message.tool_calls:
                    tc = resp.message.tool_calls[0]
                    return self.registry.execute(tc.function.name, tc.function.arguments)
                return "无法修复"
            except:
                return "无法修复"
        
        # 首次执行
        result = self.registry.execute(tool_name, arguments)
        
        if result.startswith("错误"):
            status = self.recovery.handle_error(result, retry_fn, self_fix_fn)
            if status == "recovered":
                return self.registry.execute(tool_name, arguments)
            elif status == "self_fix":
                return result  # 模型已处理
            else:
                return result  # escalated
        
        return result
    
    def _build_step_messages(
        self, 
        step: Dict[str, Any], 
        previous_results: List[Dict]
    ) -> List[Dict]:
        """构建步骤执行的消息列表"""
        system_content = EXEC_STEP_PROMPT.format(
            step_id=step["id"],
            action=step["action"],
            target=step["target"],
            purpose=step["purpose"]
        )
        
        messages = [{"role": "system", "content": system_content}]
        
        # 添加前序步骤结果作为上下文
        if previous_results:
            context_parts = []
            for r in previous_results[-3:]:  # 只取最近 3 步
                status = "成功" if r["success"] else "失败"
                context_parts.append(f"步骤 {r['step_id']}: {r['description']} [{status}]")
            messages.append({
                "role": "user",
                "content": "前序步骤执行情况:\n" + "\n".join(context_parts)
            })
        
        # 当前步骤指令
        messages.append({
            "role": "user",
            "content": f"请执行步骤 {step['id']}: {step['purpose']}（目标: {step['target']}）"
        })
        
        return messages
