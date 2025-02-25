import streamlit as st
import datetime
import dashscope
from firecrawl import FirecrawlApp
import os
from openai import OpenAI 

# Initialize the Firecrawl app with API key
fire_api = "fc-343fd362814545f295a89dc14ec4ee09"
app = FirecrawlApp(api_key=fire_api)

# Initialize local factual knowledge storage if not already set
if "local_facts" not in st.session_state:
    st.session_state["local_facts"] = []  # Will store dicts for websites with keys: type, url, desc, content
if "local_files" not in st.session_state:
    st.session_state["local_files"] = []  # Will store dicts for files with keys: type, file_name, content

# Function to get raw HTML content from a website using Firecrawl
def get_raw_html(domain):
    try:
        crawl_status = app.crawl_url(
            f'https://{domain}',
            params={'limit': 100, 'scrapeOptions': {'formats': ['markdown', 'links']}},
            poll_interval=30
        )
        if crawl_status['success'] and crawl_status['status'] == 'completed':
            # Assuming the first data entry holds the content in markdown
            markdown_content = crawl_status['data'][0]['markdown']
            return markdown_content
        else:
            return f"Failed to retrieve content from {domain}. Status: {crawl_status['status']}"
    except Exception as e:
        return f"Error while fetching content from {domain}: {str(e)}"

# Function to analyze content with Qwen model (for topics analysis)
def analyze_with_qwen(domain, raw_html):
    messages = [
        {'role': 'system', 'content': 'You are a professional AI researcher. Analyze the raw HTML content and extract key topics in the following format: "1. Description | Website"'},
        {'role': 'user', 'content': f'''
        Analyze the raw HTML content from {domain} and provide the latest 10 topics with:
        1. Article titles in English
        2. Article titles in Chinese
        3. One-line descriptions in English
        4. One-line descriptions in Chinese
        5. Website name
        Use current date: {datetime.date.today()}.
        HTML Content: {raw_html}
        '''}
    ]
    response = dashscope.Generation.call(
        api_key="sk-1a28c3fcc7e044cbacd6faf47dc89755",
        model="qwen-turbo",
        messages=messages,
        enable_search=True,
        result_format='message'
    )
    return response['output']['choices'][0]['message']['content']

# Function for direct chat using Qwen (standard mode)
def chat_with_qwen(user_message):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_message},
    ]
    response = dashscope.Generation.call(
        api_key="sk-1a28c3fcc7e044cbacd6faf47dc89755",
        model="qwen-turbo",
        messages=messages,
        enable_search=True,
        result_format='message'
    )
    return response['output']['choices'][0]['message']['content']

# UPDATED: Function for chat using local factual knowledge (RAG)
def chat_with_local_facts(user_message):
    local_facts = st.session_state.get("local_facts", [])
    local_files = st.session_state.get("local_files", [])
    
    # Build a context string from each stored source – here we simply take the first 1000 characters per source
    context_text = ""
    for source in local_facts:
        context_text += f"【网站】 {source['url']}\n{source['content'][:1000]}\n"
    for file_info in local_files:
        context_text += f"【文件】 {file_info['file_name']}\n{file_info['content'][:1000]}\n"
    
    if not context_text:
        context_text = "当前没有本地信息。"
        
    messages = [
        {"role": "system", "content": f"你是一个基于本地事实知识库的智能助手。以下是部分文档内容用于辅助回答问题：\n{context_text}\n请基于这些内容回答用户问题。"},
        {"role": "user", "content": user_message},
    ]
    response = dashscope.Generation.call(
        api_key="sk-1a28c3fcc7e044cbacd6faf47dc89755",
        model="qwen-turbo",
        messages=messages,
        enable_search=True,
        result_format='message'
    )
    return response['output']['choices'][0]['message']['content']

# Function for direct chat using Deepseek model
def chat_with_deepseek(user_message):
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY", "sk-1a28c3fcc7e044cbacd6faf47dc89755"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_message},
    ]
    completion = client.chat.completions.create(
        model="deepseek-r1",  # 使用 deepseek 模型
        messages=messages
    )
    return completion.choices[0].message.content

# ----------------------- Streamlit UI -----------------------
st.title("Minerva Agent")

# Create four tabs for different functionalities
tabs = st.tabs(["热点监控", "定时汇报", "事实知识库 (RAG)", "直接聊天"])

# ----------------------- Tab 1: Trending Topics Monitoring -----------------------
with tabs[0]:
    st.header("热点监控")
    st.write("监控推流的各大信息网站的热点")
    default_websites = ["lilianweng.github.io"]
    input_websites = st.text_area("网站域名 (逗号分隔):", value=', '.join(default_websites), height=100)
    websites = [site.strip() for site in input_websites.split(',')]
    
    if st.button("开始监控"):
        for site in websites:
            st.write(f"### 正在拉取 {site} 的数据...")
            raw_html = get_raw_html(site)
            if isinstance(raw_html, str) and ('Error' in raw_html or 'Failed' in raw_html):
                st.error(raw_html)
            else:
                st.write("数据拉取成功，正在分析热点内容...")
                analysis = analyze_with_qwen(site, raw_html)
                st.text_area(f"{site} 热点分析", analysis, height=300)
            st.markdown("---")

# ----------------------- Tab 2: Scheduled Reports -----------------------
with tabs[1]:
    st.header("定时汇报")
    st.write("定时整合汇报各大信息网站的重要内容")
    st.info("开发中")
    scheduled_time = st.time_input("选择汇报时间（例如每日定时）", datetime.time(hour=12, minute=0))
    st.write(f"当前设置的汇报时间为：{scheduled_time}")

# ----------------------- Tab 3: Local Factual Knowledge Base (RAG) -----------------------
with tabs[2]:
    st.header("事实知识库 (RAG)")
    st.write("上传文件或添加网站，系统会提取内容，并在聊天时基于这些信息进行回答。")
    
    # Form to add a new website source – it immediately fetches and stores content.
    with st.form("add_source_form"):
        new_source = st.text_input("输入新信息源网址:")
        source_desc = st.text_area("信息源描述:")
        submitted = st.form_submit_button("添加信息源")
        if submitted and new_source:
            st.info(f"正在从 {new_source} 抓取内容...")
            # Remove potential protocol parts for get_raw_html function
            domain = new_source.replace("https://", "").replace("http://", "").strip()
            raw_content = get_raw_html(domain)
            st.session_state["local_facts"].append({
                "type": "website",
                "url": new_source,
                "desc": source_desc,
                "content": raw_content
            })
            st.success(f"信息源 {new_source} 已添加，并提取内容！")
    
    st.markdown("---")
    # Form to upload files – the app processes and extracts text content.
    with st.form("upload_file_form", clear_on_submit=True):
        uploaded_files = st.file_uploader("选择要上传的文件（支持所有格式）", accept_multiple_files=True)
        file_submitted = st.form_submit_button("上传文件")
        if file_submitted and uploaded_files:
            for file in uploaded_files:
                try:
                    file_bytes = file.getvalue()
                    # 尝试解码为 UTF-8 文本
                    try:
                        file_text = file_bytes.decode("utf-8")
                    except Exception:
                        file_text = str(file_bytes)
                    st.session_state["local_files"].append({
                        "type": "file",
                        "file_name": file.name,
                        "content": file_text
                    })
                    st.success(f"文件 {file.name} 已上传并处理！")
                except Exception as e:
                    st.error(f"处理文件 {file.name} 时出错：{e}")
    
    st.markdown("### 当前本地信息")
    if st.session_state["local_facts"]:
        st.write("#### 网站信息")
        for idx, fact in enumerate(st.session_state["local_facts"], start=1):
            st.write(f"**{idx}.** {fact['url']} — {fact['desc']}")
    else:
        st.info("还没有添加任何网站信息。")
    
    if st.session_state["local_files"]:
        st.write("#### 上传的文件")
        for idx, file_info in enumerate(st.session_state["local_files"], start=1):
            st.write(f"**{idx}.** {file_info['file_name']}")
    else:
        st.info("还没有上传任何文件。")

# ----------------------- Tab 4: Direct Chat -----------------------
with tabs[3]:
    st.header("直接聊天")
    st.write("基于 Qwen、大模型、本地知识库 (RAG) 以及 Deepseek 模型，您可以直接与 AI 进行对话。")
    
    # 选择聊天模式：包含 Qwen、本地知识库 (RAG) 和 Deepseek 聊天选项
    chat_mode = st.radio("选择聊天模式", ("Qwen聊天", "本地知识聊天", "Deepseek聊天"))
    
    # Maintain conversation history in session state
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    
    # Chat input form (clears on submit)
    with st.form("chat_form", clear_on_submit=True):
        chat_input = st.text_input("输入您的消息：")
        submitted = st.form_submit_button("发送")
        if submitted and chat_input:
            st.session_state["chat_history"].append({"role": "user", "content": chat_input})
            if chat_mode == "Qwen聊天":
                reply = chat_with_qwen(chat_input)
            elif chat_mode == "本地知识聊天":
                reply = chat_with_local_facts(chat_input)
            elif chat_mode == "Deepseek聊天":
                reply = chat_with_deepseek(chat_input)
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})
    
    st.markdown("### 聊天记录")
    for message in st.session_state["chat_history"]:
        if message["role"] == "user":
            st.markdown(f"**您:** {message['content']}")
        else:
            st.markdown(f"**AI:** {message['content']}")