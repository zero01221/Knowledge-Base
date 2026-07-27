import time
import os

import streamlit as st
from agent.react_agent import ReactAgent
from utils.path_tool import get_abs_path

# ---------- 页面配置 ----------
st.set_page_config(
    page_title='企业智慧转型智能助手',
    page_icon='🏛️',
    layout='wide',
)

# ---------- 侧边栏 ----------
with st.sidebar:
    st.title('🏛️ 企业智慧转型助手')
    st.caption('基于 TOGAF 理论 · 企业架构治理')
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

    for f in kb_files:
        ext_icon = '📄' if f.endswith('.txt') else '📕'
        st.write(f'{ext_icon} {f}')

    if not kb_files:
        st.warning('未找到知识库文件')

    st.caption(f'共 {len(kb_files)} 个文件')

    st.divider()

    # 清空对话按钮
    if st.button('🗑️ 清空对话', use_container_width=True):
        st.session_state['messages'] = []
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
st.title('🏛️ 企业智慧转型智能助手')
st.caption('基于 TOGAF 理论，回答企业架构治理工作台的产品功能、业务流程和 TOGAF 方法论相关问题')
st.divider()

# ---------- Agent 初始化 ----------
if 'agent' not in st.session_state:
    st.session_state['agent'] = ReactAgent()

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

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
    st.rerun()
