from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService

rag = RagSummarizeService()


@tool(description='从知识库中检索TOGAF理论、企业架构治理工作台产品文档、业务流程等相关资料')
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)
