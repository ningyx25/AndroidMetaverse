# AndroidMetaverse

基于 [LangGraph](https://github.com/langchain-ai/langgraph) 的 Android 虚拟环境 Agent 框架。通过三层 Agent 协作，在模拟的 Android UI 环境中自主规划并执行操作，自动完成指定任务目标。

## 架构

三个 Agent 通过 LangGraph 状态图协作：

```
SuiteAgent   ──  任务管理（初始化 UI、设定目标、流程路由、评分）
GUIAgent     ──  感知当前 UI，规划下一步动作
AndroidAgent ──  模拟执行动作，返回更新后的 UI 状态
```

执行流程：

```
START
  → initialize_task       # 初始化 UI 环境
  → get_task_goal         # 设定任务目标
  → plan_action           # GUIAgent 规划动作
      ├── [status/answer] → get_task_score → END
      └── [其他动作]      → execute_action → plan_action (循环)
```

## 目录结构

```
AndroidMetaverse/
├── agent/
│   ├── config.py           # LLM 初始化
│   ├── state.py            # 状态类型定义（UIElement / Action / SuiteState 等）
│   ├── prompt.py           # 各 Agent 系统提示词与输出 Schema
│   ├── suite_agent.py      # 任务管理与流程控制
│   ├── gui_agent.py        # UI 感知与动作规划
│   ├── android_agent.py    # 动作执行与 UI 状态更新
│   ├── graph.py            # LangGraph 图构建
│   ├── run.py              # 入口
│   └── UI_ELEM.json        # UI 元素 Schema 示例
├── scripts/
│   ├── describe_first_images.py   # 批量调用 VLM 描述任务首帧截图
│   ├── describe_all_images.py     # 批量调用 VLM 描述所有步骤截图
│   └── prompt.py                  # 图像描述用提示词
├── data/                   # 任务 metadata（含多版本 LLM 生成结果，已 gitignore）
├── image/                  # 任务步骤截图（已 gitignore）
├── diff_pages.py           # 对比两个 UI 页面元素差异，生成结构化 prompt
└── .env                    # API Key 配置（已 gitignore）
```

## 快速开始

**安装依赖**

```bash
pip install langchain langchain-openai langgraph python-dotenv openai
```

**配置环境变量**

复制 `.env.example` 并填入 API Key：

```bash
cp .env.example .env
```

`.env` 内容示例：

```
ZENMUX_API_KEY=<your_api_key>
ZENMUX_BASE_UR=https://zenmux.ai/api/v1
```

**运行**

```bash
cd agent
python run.py
```

## 数据处理

`scripts/` 目录提供批量图像描述脚本，用于从任务截图生成 UI 元素 metadata：

```bash
cd scripts
# 仅描述每个任务的首帧截图
python describe_first_images.py

# 描述所有步骤截图
python describe_all_images.py
```

输出写入 `data/` 目录，供 Agent 加载使用。

## 扩展

| 扩展点 | 说明 |
|---|---|
| `SuiteAgent.initialize_task` | 替换为真实设备 UI 数据（如 ADB dump） |
| `SuiteAgent.get_task_goal` | 从数据集或外部配置加载任务目标 |
| `AndroidAgent.execute_action` | 对接真实 ADB 指令执行 |
| `config.py` | 切换不同 LLM（DeepSeek / GLM / Qwen 等） |

## 支持的动作类型

`click` / `long_press` / `double_tap` / `input_text` / `keyboard_enter` / `scroll` / `swipe` / `navigate_back` / `navigate_home` / `open_app` / `wait` / `answer` / `status`

## 技术栈

- Python 3.11+
- [LangChain](https://github.com/langchain-ai/langchain) + [LangGraph](https://github.com/langchain-ai/langgraph)
- LLM：通过 OpenAI 兼容接口接入（DeepSeek / GLM / Qwen / MiniMax 等）
- 任务基准参考：[AndroidWorld](https://github.com/google-research/android_world)
