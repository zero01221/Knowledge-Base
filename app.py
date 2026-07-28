import time
import os
import http.server
import mimetypes
import socketserver
import threading
import urllib.parse
from functools import partial

import streamlit as st
from agent.react_agent import ReactAgent
from utils.path_tool import get_abs_path
from rag.vector_store import VectorStoreService
from utils.conversation_handler import save_conversation, load_conversation, clear_conversation


# ---------- 后台文件服务器（仅启动一次）----------
class _UTF8FileHandler(http.server.SimpleHTTPRequestHandler):
    """静态文件处理器：对 text/* 类型强制声明 UTF-8 编码，解决中文乱码。"""

    def guess_type(self, path):
        mime, _ = mimetypes.guess_type(path)
        if mime and mime.startswith('text/'):
            return mime + '; charset=utf-8'
        return mime or 'application/octet-stream'

    def log_message(self, format, *args):
        pass  # 关闭访问日志，保持控制台整洁


@st.cache_resource
def _start_file_server() -> str:
    """在 daemon 线程启动静态文件服务器，返回访问前缀 URL。

    文件按需由浏览器拉取，页面上只放轻量链接，不嵌入文件内容。
    """
    data_path = get_abs_path('data')
    os.makedirs(data_path, exist_ok=True)

    with socketserver.TCPServer(('127.0.0.1', 0), None) as s:
        port = s.server_address[1]

    handler = partial(_UTF8FileHandler, directory=data_path)
    server = socketserver.ThreadingTCPServer(('127.0.0.1', port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    return f'http://127.0.0.1:{port}'


# ---------- 页面配置 ----------
st.set_page_config(
    page_title='问答助手',
    page_icon='🤖',
    layout='wide',
)

# ---------- 侧边栏 ----------
with st.sidebar:
    st.title('🤖 问答助手')
    st.caption('基于 TOGAF 理论 · 企业架构治理')
    st.divider()

    # ---------- 文件上传 ----------
    st.subheader('📤 上传知识库文件')
    uploaded_file = st.file_uploader(
        '选择文件上传到知识库',
        type=['txt', 'pdf'],
        accept_multiple_files=False,
        help='支持 .txt 和 .pdf 格式的文件，上传后将自动加载到向量知识库',
    )

    if uploaded_file is not None:
        data_path = get_abs_path('data')
        save_path = os.path.join(data_path, uploaded_file.name)

        # 保存文件到 data 目录
        with open(save_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        st.success(f'✅ {uploaded_file.name} 上传成功！')

        # 自动加载到向量知识库
        with st.spinner('🔄 正在将文件加载到向量知识库...'):
            try:
                vs = VectorStoreService()
                vs.load_document()
                st.success('✅ 已加载到向量知识库')
            except Exception as e:
                st.error(f'加载到向量知识库失败: {str(e)}')

        st.rerun()

    st.divider()

    # 知识库信息
    st.subheader('📚 知识库文件')
    data_path = get_abs_path('data')
    kb_files = []
    if os.path.isdir(data_path):
        for f in sorted(os.listdir(data_path)):
            full_path = os.path.join(data_path, f)
            if os.path.isfile(full_path) and f.endswith(('.txt', '.pdf')):
                kb_files.append(f)

    if kb_files:
        base_url = _start_file_server()
        for f in kb_files:
            ext_icon = '📄' if f.endswith('.txt') else '📕'
            encoded_name = urllib.parse.quote(f)
            st.markdown(
                f'{ext_icon} <a href="{base_url}/{encoded_name}" target="_blank">{f}</a>',
                unsafe_allow_html=True,
            )
    else:
        st.warning('未找到知识库文件')

    st.caption(f'共 {len(kb_files)} 个文件')

    st.divider()

    # 清空对话按钮
    if st.button('🗑️ 清空对话', use_container_width=True):
        st.session_state['messages'] = []
        clear_conversation()
        st.rerun()

    st.divider()

    # 状态信息
    st.subheader('⚙️ 状态')
    st.caption(f'向量集合: togaf_assistant')
    st.caption(f'检索数量: Top-3')
    st.caption(f'模型: Qwen3.7-Max')

    st.divider()
    st.caption('💡 提示：问题涉及产品功能或业务流程时，会自动检索知识库')

# ---------- 主界面 ----------
st.title('🤖 问答助手')
st.caption('基于 TOGAF 理论，回答企业架构治理工作台的产品功能、业务流程和 TOGAF 方法论相关问题')
st.divider()

# ---------- Agent 初始化 ----------
if 'agent' not in st.session_state:
    st.session_state['agent'] = ReactAgent()

if 'messages' not in st.session_state:
    st.session_state['messages'] = load_conversation()

# ---------- 对话历史 ----------
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.write(message['content'])

# ---------- 用户输入 ----------
prompt = st.chat_input('请输入您的问题...')

if prompt:
    with st.chat_message('user'):
        st.write(prompt)
    st.session_state['messages'].append({'role': 'user', 'content': prompt})

    response_messages = []
    with st.spinner('🤔 正在思考并检索知识库...'):
        res_stream = st.session_state['agent'].execute_stream(prompt)

        def capture(generator, cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                for char in chunk:
                    time.sleep(0.01)
                    yield char

        with st.chat_message('ai'):
            st.write_stream(capture(res_stream, response_messages))

    st.session_state['messages'].append({'role': 'ai', 'content': response_messages[-1]})
    save_conversation(st.session_state['messages'])
    st.rerun()
