## 上下文

本项目从零开始构建一个 Plan-Execute Agent，使用 Python 编写，通过 Ollama 调用本地部署的 qwen3.6:35b 模型。运行环境为 Apple M4 / 32GB 统一内存，模型占用约 23GB。项目采用单模型架构（所有角色由同一模型承担），通过混合控制模式（规划受控 + 执行自主）实现任务从拆解到执行的完整闭环。

核心约束：
- 单模型（qwen3.6:35b），不支持运行时切换模型
- 23GB 内存常驻，无额外模型加载开销
- qwen3.6:35b 原生支持 tool calling、vision 和 thinking
- MVP 阶段仅实现自治式交互（用户输入任务 → agent 自动完成）

## 目标 / 非目标

**目标：**
- 实现完整的 Plan-Execute 闭环：用户输入自然语言任务 → 自动生成结构化计划 → 逐步自主执行 → 输出结果
- 通过 tool calling 机制让模型能够操作文件系统、执行 Shell 命令和运行代码
- 实现三级错误恢复，保证 agent 在遇到失败时能自主尝试修复
- 提供清晰的流式进度输出，让用户实时了解 agent 工作状态
- 代码结构简单清晰，核心代码控制在 500 行以内

**非目标：**
- 多模型协作和动态模型切换（后续迭代）
- 审批式交互和对话式交互（后续迭代）
- 分布式执行或远程工具调用
- 持久化记忆和跨会话上下文
- Web UI 或 API 服务化

## 决策

### 决策 1: 项目结构 — 单模块扁平结构

**选择：** 采用扁平的 Python 包结构，所有核心模块放在 `agent/` 目录下

```
agent_demo/
├── agent/
│   ├── __init__.py
│   ├── llm.py          # Ollama 客户端封装
│   ├── planner.py       # 规划引擎
│   ├── executor.py      # 执行循环
│   ├── tools/
│   │   ├── __init__.py  # ToolRegistry
│   │   ├── base.py      # Tool 基类
│   │   ├── file_tools.py
│   │   ├── shell_tools.py
│   │   └── code_tools.py
│   ├── recovery.py      # 错误恢复
│   └── output.py        # 进度输出
├── main.py              # CLI 入口
├── requirements.txt
└── config.py            # 配置（模型名、超时等）
```

**理由：** 项目规模小（核心 <500 行），扁平结构降低认知负担。tools/ 子目录单独拆分是因为工具数量会增长，需要独立组织。

**替代方案：** 单文件实现 — 过于拥挤，工具扩展困难。

### 决策 2: LLM 调用 — ollama Python SDK + 原生 tool calling

**选择：** 使用 `ollama` Python 官方 SDK 的 `chat()` 方法，通过 `tools` 参数传递工具 schema，利用 qwen3.6:35b 的原生 tool calling 能力

```python
from ollama import chat

response = chat(
    model='qwen3.6:35b',
    messages=messages,
    tools=registry.get_tool_schemas()
)
```

**理由：** qwen3.6:35b 原生支持 tool calling，无需额外的 function calling 适配层。Ollama SDK 是最轻量的集成方式。

**替代方案：** 
- 直接调用 Ollama REST API — 更底层但需要手动处理流式和 JSON 解析
- LangChain — 过重，引入大量不必要的抽象

### 决策 3: 规划输出 — JSON 格式 + 代码校验

**选择：** 规划引擎通过 system prompt 约束模型输出 JSON 格式的计划，代码层面对输出进行 JSON 解析校验，失败则重试

```python
# System prompt 关键约束
PLAN_PROMPT = """你是一个任务规划器。将用户任务拆解为 JSON 计划。
输出格式必须为：
{"goal": "任务目标", "steps": [{"id": 1, "action": "...", "target": "...", "purpose": "..."}]}
只输出 JSON，不要其他内容。"""

# 代码校验
import json
plan = json.loads(model_response)  # 失败则重试
```

**理由：** JSON 是结构化数据的标准格式，易于解析和验证。qwen3.6:35b 的 JSON 输出能力足够可靠。代码校验确保下游执行模块收到的数据格式正确。

**替代方案：**
- 自然语言计划 — 执行阶段需要二次理解，容易歧义
- YAML 格式 — 模型输出 YAML 的稳定性不如 JSON

### 决策 4: 执行循环 — while 循环 + tool call 检测

**选择：** 执行循环通过检测模型响应中是否包含 `tool_calls` 来决定继续调用工具还是结束当前步骤

```python
while True:
    response = chat(model, messages, tools)
    if response.message.tool_calls:
        for tool_call in response.message.tool_calls:
            result = registry.execute(tool_call)
            messages.append({"role": "tool", ...})
    else:
        break  # 模型认为步骤完成
```

**理由：** 这是 Ollama tool calling 的标准模式，简洁且符合模型的工作方式。模型自主决定调用次数和顺序，代码只负责循环框架和工具执行。

**替代方案：**
- 固定步骤执行（每步一次模型调用）— 不够灵活，模型无法在一个步骤内多次调用工具
- 状态机驱动 — 过于复杂，对于 MVP 不必要

### 决策 5: 工具安全 — 路径白名单 + 命令黑名单

**选择：** 
- 文件工具：禁止访问 `/etc`、`/System`、`/usr` 等系统目录，工作目录限定在项目根目录及其子目录
- Shell 工具：黑名单匹配 `rm -rf /`、`mkfs`、`dd if=` 等危险命令模式
- 代码工具：在子进程中执行，设置超时和资源限制

**理由：** MVP 阶段采用简单的规则匹配而非沙箱，平衡安全性和实现复杂度。后续可升级为容器沙箱。

### 决策 6: 错误恢复 — 状态机驱动三级降级

**选择：** 用简单的状态机管理错误恢复流程

```
TOOL_CALL_FAILED
    │
    ├─ retry_count < 3 → RETRY (等待 1s 后重试)
    │
    ├─ retry_count >= 3 → SELF_FIX (将错误返回模型)
    │      │
    │      ├─ 模型提出修复方案 → 重新执行 → 回到 TOOL_CALL_FAILED
    │      │
    │      └─ 模型无法修复 → ESCALATE
    │
    └─ 不可恢复错误 → ESCALATE (直接上报)
```

**理由：** 状态机清晰表达了三级降级的流转逻辑，每个状态的处理逻辑独立，易于测试和调试。

## 风险 / 权衡

**[qwen3.6:35b 的 JSON 输出不稳定]** → 规划阶段增加 JSON 校验和重试机制（最多 3 次），system prompt 中强化格式约束

**[模型 tool calling 能力不足]** → qwen3.6:35b 官方标注支持 tools，但实际效果需验证。若 tool calling 失败率高，fallback 到让模型输出 JSON 格式的工具调用指令，由代码解析执行

**[23GB 内存占用影响系统性能]** → Ollama 支持模型自动卸载，非活跃时释放内存。用户可在 config.py 中调整 `num_gpu` 参数控制显存占用

**[Shell/代码执行的安全风险]** → MVP 阶段限定工作目录 + 命令黑名单。明确告知用户 agent 具有本地执行能力，建议在隔离环境中运行敏感任务

**[单模型承担所有角色的质量瓶颈]** → qwen3.6:35b 是 35B 参数模型，综合能力强。若规划质量不足，后续可引入 deepseek-r1:14b 做专职规划（需要解决内存问题）
