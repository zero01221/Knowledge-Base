# CLAUDE.md

## 项目概述

企业智慧转型智能助手 — 基于 LangChain + ChromaDB 的 RAG 智能问答系统。采用 ReAct（思考-行动-观察）Agent 模式，服务于基于 TOGAF 理论的企业架构治理咨询场景。

- **Web 框架**: Streamlit
- **LLM**: 通义千问 qwen3.7-max
- **Embedding**: 通义千问 qwen3.7-text-embedding
- **向量库**: ChromaDB（本地持久化）
- **启动方式**: `streamlit run app.py`

---

## 项目结构

```
Knowledge-Base/
├── app.py                           # Streamlit 前端入口（标题、上传、对话）
├── CLAUDE.md                        # 本文件
├── README.md                        # 项目详细文档
├── requirements.txt                 # Python 依赖
├── md5.txt                          # 已加载文件的 MD5 去重记录
├── .gitignore
│
├── agent/                           # Agent 核心
│   ├── react_agent.py               # ReAct Agent 实现（stream 模式输出）
│   └── tools/
│       ├── agent_tools.py           # 工具定义（rag_summarize）
│       └── middleware.py            # 中间件（工具监控、模型调用日志）
│
├── rag/                             # RAG 检索增强生成
│   ├── rag_service.py               # RAG 服务（检索→构建上下文→LLM 生成）
│   └── vector_store.py              # 向量库管理（文档加载、分片、MD5去重、入库）
│
├── model/                           # 模型工厂
│   └── factory.py                   # ChatModel + Embedding 工厂（单例）
│
├── config/                          # YAML 配置
│   ├── agent.yml                    # Agent 配置（当前未启用外部数据）
│   ├── chroma.yml                   # ChromaDB 配置（集合名、分片、检索参数）
│   ├── rag.yml                      # 模型名称配置
│   └── prompts.yml                  # 提示词文件路径配置
│
├── prompts/                         # 提示词模板
│   ├── main_prompt.txt              # ReAct Agent 系统提示词
│   └── rag_summarize.txt            # RAG 总结提示词
│
├── data/                            # 知识库文件目录
│   ├── TOGAF术语定义.txt
│   ├── 企业架构治理工作台设计.pdf
│   ├── 原版流程.txt
│   └── external/                    # 外部数据（预留）
│
├── utils/                           # 工具函数
│   ├── config_handler.py            # YAML 配置加载器（模块级单例）
│   ├── conversation_handler.py      # 对话持久化（保存/加载/清空）
│   ├── file_handler.py              # 文件处理（PDF/TXT 加载、MD5、Data URI）
│   ├── logger_handler.py            # 日志系统（控制台 + 按日滚动文件）
│   ├── path_tool.py                 # 路径工具（项目根目录 + 相对→绝对转换）
│   └── prompt_loader.py             # 提示词文件加载器
│
├── conversations/                   # 对话存档目录（自动生成）
├── rag/chroma_db/                   # ChromaDB 持久化目录（自动生成）
└── logs/                            # 日志文件目录（按日生成）
```

---

## 调用链路

```
用户输入 (app.py)
  → ReactAgent.execute_stream(query)
    → ReAct Agent 思考（main_prompt.txt 指导）
      → 判断是否需要检索
        → 调用 rag_summarize(query) 工具
          → RagSummarizeService.rag_summarize(query)
            → ChromaDB 向量检索（top-3）
            → 构建上下文 + 调用 LLM 生成总结
        → Agent 基于工具结果继续思考
    → 流式输出最终回答
  → Streamlit write_stream 渲染（打字机效果）
```

---

## 关键设计决策

### 1. MD5 去重机制
- 文件加载到向量库后，MD5 写入 `md5.txt`
- 下次 `load_document()` 时自动跳过已有 MD5 的文件
- 如需强制重新加载：删除 `md5.txt` 和 `rag/chroma_db/` 后重跑

### 2. Embedding 批量限制
- DashScope Embedding API 单批限制 ≤20 条
- `vector_store.py` 中 `batch_size = 20` 分批提交

### 3. 工具调用限制
- Agent 最多调用 `rag_summarize` 3 次
- 超过 3 次仍信息不足则诚实告知用户

### 4. 配置模块使用模块级单例
- `config_handler.py` 中的 `rag_conf`、`chroma_conf` 等在 import 时即初始化
- `model/factory.py` 中的 `chat_model`、`embed_model` 同理
- 整个应用共享同一套配置和模型实例

### 5. 日志系统
- 控制台输出 INFO 级别以上
- 文件记录 DEBUG 级别以上，按日滚动：`logs/agent_YYYYMMDD.log`
- 通过 `logger_handler.py` 的 `get_logger()` 获取，自动去重 handler

### 6. 对话持久化
- 对话自动保存到 `conversations/current.json`，每次对话更新后写入
- 页面刷新/重启后自动恢复上次对话
- 后续可扩展为账号密码登录 + 多会话历史记录

### 7. 知识库文件在线阅读
- 启动时通过 `@st.cache_resource` 在 daemon 线程启动静态文件服务器（`http.server` + `ThreadingTCPServer`）
- 服务器绑定 `127.0.0.1:0`（随机端口），仅本机可访问
- 侧边栏文件名渲染为 `<a target="_blank">` 链接，指向文件服务器 URL
- 浏览器按需拉取文件，页面 HTML 不嵌入任何文件内容，文件数量和大小不影响前端性能
- 浏览器原生渲染，支持任意文件格式，后续新增类型无需改代码

---

## 常用命令

```bash
# 启动 Web 应用
streamlit run app.py

# 初始化/更新向量知识库（也支持直接运行）
python -m rag.vector_store

# 测试 Agent
python agent/react_agent.py

# 测试 RAG 检索
python -m rag.rag_service

# 安装依赖
pip install -r requirements.txt
```

---

## 最近变更（2026-07-27）

### 新增知识库文件在线阅读
- 侧边栏文件名改为可点击链接，点击后在浏览器新标签页中打开文件原件
- 通过后台静态文件服务器（daemon 线程，随机端口）+ 浏览器原生渲染实现
- 页面只放轻量链接，文件内容按需由浏览器拉取，不嵌入页面 HTML，文件再多也不影响性能
- 新增工具函数 `file_to_data_uri()`（`utils/file_handler.py`，备用）
- 文件阅读与对话主功能互不干扰，可同时进行

### 新增对话持久化
- 对话自动保存到 `conversations/current.json`，刷新页面不丢失
- 新增 `utils/conversation_handler.py` 模块（save/load/clear）
- 「清空对话」按钮同步清除磁盘存档
- 模块设计为后续账号系统预留扩展接口

### 前端标题修改
- 页面标题、侧边栏标题、主界面标题均改为 **"问答助手"**（原"企业智慧转型智能助手"）
- 图标从 🏛️ 改为 🤖

### 新增文件上传功能
- 位置：侧边栏顶部（知识库文件列表上方）
- 组件：`st.file_uploader`，接受 `.txt` 和 `.pdf` 格式
- 流程：用户选择文件 → 保存到 `data/` 目录 → 自动调用 `VectorStoreService().load_document()` 加载到向量库
- 已存在的文件会被覆盖，MD5 去重机制确保不会重复索引

---

## 维护指南

### 添加新知识库文件
- **前端上传**：通过 Web 界面上传按钮直接上传
- **手动添加**：放入 `data/` 目录 → 运行 `python -m rag.vector_store`
- 注意文件格式必须是 `.txt` 或 `.pdf`，否则不会被向量化（`config/chroma.yml` 中 `allow_knowledge_file_type` 控制）

### 添加新工具
1. 在 `agent/tools/agent_tools.py` 中用 `@tool` 装饰器定义
2. 在 `agent/react_agent.py` 的 `tools=[rag_summarize, new_tool]` 中注册
3. 在 `prompts/main_prompt.txt` 中添加工具使用说明

### 修改提示词
- `prompts/main_prompt.txt`：控制 Agent 的思考准则、工具使用策略、输出格式
- `prompts/rag_summarize.txt`：控制 RAG 总结的回答风格、来源标注格式
- 修改后重启 Streamlit 生效，无需重新加载向量库

### 调整检索参数
编辑 `config/chroma.yml`：
- `k`：检索返回数量（默认 3）
- `chunk_size`：文本分片大小（默认 200 字符）
- `chunk_overlap`：分片重叠大小（默认 20 字符）

### 排查问题
- **API Key 错误**：检查环境变量 `DASHSCOPE_API_KEY` 是否设置
- **向量库为空**：确认 `data/` 下有文件且已运行过 `python -m rag.vector_store`
- **日志查看**：`logs/agent_YYYYMMDD.log` 包含完整的工具调用和模型交互记录
- **强制重建向量库**：删除 `md5.txt` 和 `rag/chroma_db/` 目录后重新运行加载命令
- **对话未恢复**：确认 `conversations/current.json` 存在且未被损坏，删除后重启会创建新对话
- **文件无法在线查看**：确认文件在 `data/` 目录下存在且可读；超大文件（>10MB）base64 编码可能影响浏览器性能
