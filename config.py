"""Agent 配置文件"""

# 模型配置
MODEL_NAME = "qwen3.6:35b"

# 超时配置（秒）
LLM_TIMEOUT = 120          # LLM 调用总超时
PLANNER_TIMEOUT = 60       # 规划阶段超时
SHELL_TIMEOUT = 30         # Shell 命令执行超时
CODE_TIMEOUT = 30          # 代码执行超时

# 错误恢复配置
MAX_RETRIES = 3            # 自动重试次数
RETRY_DELAY = 1.0          # 重试间隔（秒）

# 规划配置
MAX_PLAN_RETRIES = 3       # 规划 JSON 解析失败重试次数

# 安全配置
WORK_DIR = "."             # 默认工作目录
DANGEROUS_PATHS = [
    "/etc", "/System", "/usr", "/var", "/private",
    "/boot", "/dev", "/proc", "/sys"
]
DANGEROUS_COMMANDS = [
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=", 
    ":(){:|:&};:", "chmod -R 777 /", "sudo rm"
]
