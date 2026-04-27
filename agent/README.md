# AndroidMetaverse

基于 LangGraph 的 Android 虚拟环境 Agent 框架，通过多 Agent 协作模拟 Android 设备交互，自动完成指定任务目标。

## 架构

```
SuiteAgent
├── initialize_task   初始化 UI 环境
├── get_task_goal     设定任务目标
├── should_continue   路由判断（继续执行 or 结束评分）
└── get_task_score    评估任务完成情况

GUIAgent
└── plan_action       根据当前 UI 和任务目标规划下一步动作

AndroidAgent
└── execute_action    模拟执行动作，返回新的 UI 状态
```

执行流程：

```
START
  → initialize_task
  → get_task_goal
  → plan_action
      ├── [status/answer] → get_task_score → END
      └── [其他动作]      → execute_action → plan_action (循环)
```

## 项目结构

```
AndroidMetaverse/
├── config.py        # LLM 初始化
├── state.py         # 状态类型定义（SuiteState / GUIState / AndroidState）
├── prompt.py        # Agent 系统提示词
├── android_agent.py # Android 环境模拟
├── gui_agent.py     # GUI 动作规划
├── suite_agent.py   # 任务管理与流程控制
├── graph.py         # LangGraph 图构建
└── run.py           # 入口
```

## 快速开始

**安装依赖**

```bash
pip install langchain langchain-openai langgraph python-dotenv
```

**配置环境变量**

复制 `.env` 并填入 API Key：

```
MODELSCOPE_API_KEY=<your_api_key>
MODELSCOPE_BASE_UR=https://api-inference.modelscope.cn/v1
```

**运行**

```bash
python run.py
```

## 扩展

- 替换 `SuiteAgent.initialize_task` 以接入真实设备 UI 数据
- 替换 `SuiteAgent.get_task_goal` 以从数据集或外部配置加载任务
- 替换 `AndroidAgent.execute_action` 以对接真实 ADB 指令执行
- 在 `config.py` 中切换不同的 LLM 模型
