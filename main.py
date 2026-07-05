"""Plan-Execute Agent CLI 入口"""

import sys
import os
import argparse

# 将项目根目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.llm import LLMClient
from agent.tools import ToolRegistry
from agent.planner import PlanEngine
from agent.executor import Executor
from agent.output import ProgressOutput
import config


def main():
    parser = argparse.ArgumentParser(
        description="Plan-Execute Agent - 基于 Ollama 的本地 AI Agent"
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="任务描述（如果不提供，进入交互模式）"
    )
    parser.add_argument(
        "--work-dir", "-w",
        default=config.WORK_DIR,
        help=f"工作目录（默认: {config.WORK_DIR}）"
    )
    parser.add_argument(
        "--model", "-m",
        default=config.MODEL_NAME,
        help=f"模型名称（默认: {config.MODEL_NAME}）"
    )
    
    args = parser.parse_args()
    
    # 设置工作目录
    config.WORK_DIR = os.path.abspath(args.work_dir)
    os.makedirs(config.WORK_DIR, exist_ok=True)
    
    # 获取任务描述
    task = args.task
    if not task:
        print("Plan-Execute Agent")
        print("=" * 40)
        task = input("请输入任务描述: ").strip()
        if not task:
            print("任务描述不能为空")
            sys.exit(1)
    
    # 初始化组件
    output = ProgressOutput()
    llm = LLMClient(model=args.model)
    registry = ToolRegistry()
    planner = PlanEngine(llm, output)
    executor = Executor(llm, registry, output)
    
    try:
        # 1. 规划阶段
        plan = planner.generate_plan(task)
        
        # 2. 执行阶段
        result = executor.execute_plan(plan)
        
        # 3. 输出最终结果
        success_count = sum(1 for r in result["results"] if r["success"])
        fail_count = result["total_steps"] - success_count
        
        if fail_count > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断，正在退出...")
        sys.exit(130)
    except ConnectionError as e:
        print(f"\n❌ 连接错误: {e}")
        print("请确保 Ollama 服务正在运行，且模型已下载。")
        print("  ollama serve")
        print(f"  ollama pull {args.model}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ 规划错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未预期的错误: {e}")
        print("请检查输入和配置后重试。")
        sys.exit(1)


if __name__ == "__main__":
    main()
