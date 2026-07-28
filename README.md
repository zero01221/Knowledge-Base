# 基于本地知识库的问答助手

基于 LangChain 和 ChromaDB 的智能问答 Agent 系统，采用 ReAct（思考-行动-观察）模式，融合 RAG 知识检索，服务于公司基于 TOGAF 理论定制开发企业智慧转型软件的咨询场景。

## 功能特性

- **智能问答**：基于 ReAct Agent 的自主思考与工具调用能力，先判断问题类型再决定是否需要检索知识库
- **RAG 知识检索**：集成 ChromaDB 向量数据库，支持对企业架构治理工作台产品文档、TOGAF 术语定义、业务流程规范等专有知识进行精准检索
- **来源标注**：回答中自动标注信息来源文件，用户可追溯信息出处
- **流式对话**：Streamlit Web 界面实时流式响应，打字机效果
- **文件在线阅读**：侧边栏文件列表点击即可在新标签页中打开原件，借助浏览器原生阅读能力，与对话同时进行互不干扰
- **对话持久化**：对话自动保存到本地，刷新页面不丢失，支持清空重置
- **侧边栏面板**：展示知识库文件列表、文件上传、对话清空、系统状态等信息
- **日志监控**：完整的工具调用监控和日志记录
- **MD5 去重**：知识库文件自动 MD5 去重，避免重复索引

## 技术栈

| 类别 | 技术 |
|------|------|
| **核心框架** | LangChain, LangGraph |
| **向量数据库** | ChromaDB |
| **大模型** | 通义千问（qwen3.7-max） |
| **Embedding** | 通义千问（qwen3.7-text-embedding） |
| **Web 界面** | Streamlit |
| **文档处理** | PyPDF, LangChain Document Loaders |
| **配置管理** | YAML |
| **日志系统** | Python logging |

## 项目结构

```
agent-project/
├── agent/                          # Agent 核心模块
│   ├── react_agent.py              # ReAct Agent 实现（思考-行动-观察循环）
│   └── tools/                      # 工具定义和中间件
│       ├── agent_tools.py          # 工具函数实现（RAG 检索）
│       └── middleware.py           # 中间件（监控、日志）
│
├── rag/                            # RAG（检索增强生成）模块
│   ├── rag_service.py              # RAG 服务（检索、总结、生成）
│   └── vector_store.py             # 向量存储管理（文档加载、分片、存储）
│
├── model/                          # 模型工厂
│   └── factory.py                  # 聊天模型和 Embedding 模型工厂
│
├── config/                         # 配置文件
│   ├── agent.yml                   # Agent 配置
│   ├── chroma.yml                  # ChromaDB 配置（集合名、分片参数等）
│   ├── rag.yml                     # 模型配置
│   └── prompts.yml                 # 提示词路径配置
│
├── prompts/                        # 提示词模板
│   ├── main_prompt.txt             # 主提示词（ReAct Agent 指令）
│   └── rag_summarize.txt           # RAG 总结提示词
│
├── data/                           # 知识库数据
│   ├── TOGAF术语定义.txt            # TOGAF 定制化术语定义
│   ├── 企业架构治理工作台设计.pdf    # 产品功能与架构设计文档
│   └── 原版流程.txt                 # 业务流程与操作规范
│
├── utils/                          # 工具函数
│   ├── config_handler.py           # 配置文件加载器
│   ├── conversation_handler.py     # 对话持久化（保存/加载/清空）
│   ├── file_handler.py             # 文件处理（PDF、TXT 加载器、Data URI 转换）
│   ├── logger_handler.py           # 日志处理器
│   ├── path_tool.py                # 路径工具（绝对路径转换）
│   └── prompt_loader.py            # 提示词加载器
│
├── conversations/                  # 对话存档目录（自动生成）
├── logs/                           # 日志文件（按日期记录）
├── app.py                          # Streamlit Web 应用
└── .gitignore                      # Git 忽略文件配置
```

## 快速开始

### 环境要求

- Python >= 3.10
- pip >= 21.0

### 安装依赖

```bash
pip install langchain langchain-chroma langchain-community langgraph \
            streamlit chromadb pypdf pyyaml dashscope
```

### 配置 API Key

通过环境变量设置通义千问 API 密钥：

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY="your-api-key-here"

# Windows CMD
set DASHSCOPE_API_KEY=your-api-key-here

# Linux/macOS
export DASHSCOPE_API_KEY="your-api-key-here"
```

> 建议将环境变量持久化到系统环境变量中，避免每次启动都需要手动设置。

### 初始化知识库

首次使用需要将 `data/` 目录下的知识文档加载到向量数据库：

```bash
python -m rag.vector_store
```

执行流程：
1. 扫描 `data/` 目录下的 `.txt` 和 `.pdf` 文件
2. 计算文件 MD5，跳过已加载的文件
3. 文档加载与文本分片（chunk_size=200, chunk_overlap=20）
4. 调用 Embedding API 向量化（每批 ≤20 条）
5. 存储到 ChromaDB（集合名: `togaf_assistant`）

### 运行

#### Web 界面（推荐）

```bash
streamlit run app.py
```

访问 http://localhost:8501 即可使用。

#### 命令行测试

```bash
# 测试 ReAct Agent
python agent/react_agent.py

# 测试 RAG 检索
python -m rag.rag_service

# 测试向量库
python -m rag.vector_store
```

### 使用示例

#### 1. TOGAF 通用知识问答（模型直接回答，无需检索）

```
用户：TOGAF 的 ADM 方法有几个阶段？
AI：[基于模型知识直接回答，列出预备阶段和 A-H 八个核心阶段]
```

#### 2. 产品功能咨询（自动触发 RAG 检索）

```
用户：企业架构治理工作台怎么配置干系人？
AI：[思考：需要查询产品文档 → 调用 rag_summarize("治理工作台 干系人 配置")
     → 基于检索结果回答，标注来源 📄《企业架构治理工作台设计.pdf》]
```

#### 3. 业务流程咨询（自动触发 RAG 检索）

```
用户：企业架构治理的标准业务流程是什么？
AI：[思考：需要查询流程文档 → 调用 rag_summarize("企业架构治理 业务流程")
     → 基于检索结果回答，标注来源 📄《原版流程.txt》]
```

## 配置说明

### ChromaDB 配置（config/chroma.yml）

```yaml
collection_name: togaf_assistant      # 向量集合名称
persist_directory: rag/chroma_db      # 持久化路径
k: 3                                  # 检索返回的最相似文档数
data_path: data                       # 知识库目录
md5_hex_store: md5.txt                # MD5 去重记录
allow_knowledge_file_type: ["txt","pdf"]

chunk_size: 200                       # 文本分片大小（字符数）
chunk_overlap: 20                     # 分片重叠大小
separators: ["\n\n","。",".","?","？","!"," ",""]
```

### 模型配置（config/rag.yml）

```yaml
chat_model_name: qwen3.7-max              # 对话模型
embedding_model_name: qwen3.7-text-embedding  # Embedding 模型
```

### 提示词配置（config/prompts.yml）

```yaml
main_prompt_path: prompts/main_prompt.txt
rag_summarize_prompt_path: prompts/rag_summarize.txt
```

## 核心模块说明

### 1. ReAct Agent（agent/react_agent.py）

实现思考-行动-观察循环：

```
思考 → 判断是否需要检索 → 调用 rag_summarize → 观察结果 → 生成最终回答
```

**工作流程**：
- 对于 TOGAF 通用概念（如 ADM 方法、四大架构域等），模型有足够知识，直接回答
- 对于公司专有信息（产品功能、业务流程、定制化术语），自动调用 `rag_summarize` 检索知识库
- 最多检索 3 次，若仍信息不足则诚实告知

**中间件**：
- `monitor_tool`: 监控工具调用（记录工具名、参数、结果）
- `log_before_model`: 记录每次模型调用前的消息状态

### 2. RAG 服务（rag/rag_service.py）

检索增强生成流程：

1. **检索**：根据用户查询从 ChromaDB 检索最相关的 top-k 文档
2. **构建上下文**：将检索结果格式化为参考资料，包含来源文件名
3. **生成**：结合用户问题和参考资料，使用 LLM 生成带来源标注的回答

### 3. 工具集（agent/tools/agent_tools.py）

| 工具名 | 功能 | 入参 | 出参 |
|--------|------|------|------|
| rag_summarize | RAG 知识检索 | query: str | str（带来源标注的检索结果） |

### 4. 向量存储（rag/vector_store.py）

知识库文档管理：
- **load_document()**: 加载 `data/` 目录文档到向量库，含 MD5 去重和分批提交
- **get_retriever()**: 获取检索器实例

## 常见问题

### 1. API Key 未配置

**症状**：`Value error, Did not find dashscope_api_key`

**解决**：设置环境变量 `DASHSCOPE_API_KEY`

### 2. 知识库检索无结果

**原因**：知识库未加载或查询不在知识范围内

**解决**：
```bash
# 确认知识文件存在
ls data/

# 重新加载知识库
rm -rf rag/chroma_db md5.txt
python -m rag.vector_store
```

### 3. Embedding 批量大小超限

**症状**：`batch size is invalid, it should not be larger than 20`

**解决**：当前代码已将每批提交量限制为 20 条，如仍有此问题请检查 `rag/vector_store.py` 中的 `batch_size` 参数。

### 4. Windows 编码错误

**症状**：`UnicodeEncodeError: 'gbk' codec can't encode character`

**解决**：代码中已移除 emoji 打印的调试函数，如终端仍报错可执行 `chcp 65001` 切换到 UTF-8。

### 5. Streamlit 端口占用

**症状**：`Port 8501 is already in use`

**解决**：
```bash
streamlit run app.py --server.port 8502
```

### 6. 对话刷新后丢失

**原因**：`conversations/current.json` 可能损坏或被删除。

**解决**：正常情况下对话自动保存和恢复；如异常可手动删除 `conversations/current.json`，下次对话会自动重建。

### 7. 知识库文件无法在线查看

**原因**：文件可能过大导致 base64 编码超时或文件格式不支持浏览器渲染。

**解决**：超大文件（>10MB）建议下载后本地查看；非浏览器原生支持格式（如 `.docx`）会触发下载。

## 开发指南

### 添加新工具

1. 在 `agent/tools/agent_tools.py` 中定义：

```python
@tool(description="工具描述")
def new_tool(param: str) -> str:
    """工具实现"""
    return f"结果: {param}"
```

2. 在 `agent/react_agent.py` 中注册：

```python
from agent.tools.agent_tools import new_tool

self.agent = create_agent(
    ...
    tools=[rag_summarize, new_tool],
    ...
)
```

3. 在 `prompts/main_prompt.txt` 中添加工具使用说明

### 添加知识库文档

1. 将 `.txt` 或 `.pdf` 文件放入 `data/` 目录
2. 删除 `md5.txt` 以触发重新加载（或新增文件会自动加载）
3. 运行 `python -m rag.vector_store`

> **💡 在线查看**：文件加载后，侧边栏文件名即变为可点击链接，点击即可在新标签页中查看文件原件（支持任意格式，由浏览器原生渲染）。

### 修改提示词

提示词文件位于 `prompts/` 目录：
- `main_prompt.txt`: ReAct Agent 主提示词（工具定义、思考准则、输出规则）
- `rag_summarize.txt`: RAG 总结提示词（来源标注、准确性约束）

修改后重启 Streamlit 生效。

### 调整检索参数

编辑 `config/chroma.yml`：
- `k`: 增加可获取更多上下文（但会消耗更多 token）
- `chunk_size`: 减小可获得更精准的片段，增大可获得更完整的上下文
- `chunk_overlap`: 增大可减少信息断裂

## 部署建议

### 开发环境

```bash
streamlit run app.py
```

### 生产环境

1. **Docker 容器化部署**
2. **配置持久化环境变量**：
   - `DASHSCOPE_API_KEY`: 通义千问 API 密钥
3. **反向代理**：使用 Nginx 代理 Streamlit 服务

### 性能优化

1. **知识库预加载**：启动时预先将文档向量化
2. **调整分片参数**：根据文档特征优化 `chunk_size` 和 `chunk_overlap`
3. **向量库持久化**：`rag/chroma_db/` 目录持久化保存，避免重复 Embedding 调用

## 许可证

MIT License

---

**项目版本**: v2.0.0  
**最后更新**: 2026-07-27  
**维护者**: zero01221
