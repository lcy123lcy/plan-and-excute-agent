## 1. 项目初始化

- [x] 1.1 创建项目目录结构（agent/, agent/tools/, 以及所有 __init__.py）
- [x] 1.2 创建 config.py（模型名 qwen3.6:35b、超时配置、工作目录等）
- [x] 1.3 创建 requirements.txt（ollama Python SDK）
- [x] 1.4 创建 main.py CLI 入口（argparse 解析用户任务参数）

## 2. LLM 客户端封装

- [x] 2.1 实现 agent/llm.py：封装 Ollama chat 调用，支持 messages + tools 参数
- [x] 2.2 实现流式输出支持（stream=True），逐 token 打印模型响应
- [x] 2.3 添加超时控制和错误处理（连接失败、模型未加载等）

## 3. 工具注册表与内置工具

- [x] 3.1 实现 agent/tools/base.py：Tool 基类（name, description, parameters, execute 方法）
- [x] 3.2 实现 agent/tools/__init__.py：ToolRegistry 类（register, get_tool, get_tool_schemas, execute 方法）
- [x] 3.3 实现 agent/tools/file_tools.py：ReadFileTool 和 WriteFileTool（含路径安全检查）
- [x] 3.4 实现 agent/tools/shell_tools.py：RunShellTool（含命令黑名单和 30s 超时）
- [x] 3.5 实现 agent/tools/code_tools.py：RunCodeTool（子进程执行 Python/Node.js 代码）
- [x] 3.6 在 ToolRegistry 中自动注册所有内置工具

## 4. 规划引擎

- [x] 4.1 实现 agent/planner.py：PlanEngine 类，接收用户任务描述，调用 LLM 生成 JSON 计划
- [x] 4.2 编写规划 system prompt（约束输出为 {"goal": "...", "steps": [...]} 格式）
- [x] 4.3 实现 JSON 输出校验和重试逻辑（最多 3 次，失败则提示用户）
- [x] 4.4 实现 60 秒规划超时处理

## 5. 执行循环

- [x] 5.1 实现 agent/executor.py：Executor 类，接收计划，按步骤依次执行
- [x] 5.2 实现执行步骤的 tool call 循环（while 循环检测 tool_calls，调用工具，追加结果到 messages）
- [x] 5.3 实现步骤间上下文传递（上一步结果作为下一步的输入上下文）
- [x] 5.4 实现执行步骤的 system prompt（告知模型当前步骤信息和可用工具）

## 6. 错误恢复

- [x] 6.1 实现 agent/recovery.py：ErrorRecovery 类，管理三级降级状态机
- [x] 6.2 实现第一级：工具调用失败自动重试（最多 3 次，间隔 1s）
- [x] 6.3 实现第二级：重试耗尽后将错误返回模型，让模型自主修复
- [x] 6.4 实现第三级：模型修复失败后终止步骤，输出错误摘要
- [x] 6.5 实现可恢复/不可恢复错误分类（权限不足等直接跳至第三级）
- [x] 6.6 实现错误链记录（保留完整错误上下文用于上报）

## 7. 进度输出

- [x] 7.1 实现 agent/output.py：ProgressOutput 类，统一进度展示接口
- [x] 7.2 实现各阶段状态图标输出（📋 规划、🔧 执行、✅ 完成、⚠️ 重试、❌ 失败）
- [x] 7.3 实现步骤耗时统计和显示
- [x] 7.4 实现最终汇总输出（总步骤数、成功/失败数、总耗时）
- [x] 7.5 实现工具调用时的实时参数展示

## 8. 集成与入口

- [x] 8.1 在 main.py 中串联完整流程：解析输入 → 规划 → 逐步骤执行 → 输出汇总
- [x] 8.2 将 ProgressOutput 集成到 planner、executor、recovery 各模块
- [x] 8.3 实现命令行参数：任务描述（必填）、工作目录（可选，默认当前目录）
- [x] 8.4 添加全局异常处理（KeyboardInterrupt 优雅退出、未捕获异常友好提示）

## 9. 验证与测试

- [x] 9.1 端到端测试：输入简单任务（如"创建一个 hello.py 文件"），验证完整流程
- [x] 9.2 测试工具调用：验证 read_file、write_file、run_shell、run_code 四个工具正常工作
- [x] 9.3 测试错误恢复：故意触发文件不存在错误，验证三级降级流程
- [x] 9.4 测试安全限制：验证危险路径和危险命令被正确拦截
