import requests
import streamlit as st
import datetime
import dashscope
from firecrawl import FirecrawlApp
import os
from openai import OpenAI 
import json
import time
import random
import pandas as pd
import re
from urllib.parse import urlparse
from tqdm import tqdm

# Initialize session state variables
if "local_facts" not in st.session_state:
    st.session_state["local_facts"] = []
if "local_files" not in st.session_state:
    st.session_state["local_files"] = []
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Initialize the Firecrawl app with API key
fire_api = "fc-343fd362814545f295a89dc14ec4ee09"
app = FirecrawlApp(api_key=fire_api)
jina_api = "jina_26a656e516224ce28e71cc3b28fa7b07zUchXe4_MJ_935m8SpS9-TNGL--w"

# WeChat accounts with their fakeids
weixin_accounts = {
    "量子位": "MzIzNjc1NzUzMw==",
    "机器之心": "MzA3MzI4MjgzMw==",
    "海外独角兽": "Mzg2OTY0MDk0NQ==",
    "五源资本": "MzkwMDI2ODE0OQ==",
    "Z Lives": "MzkxMzY0NzU3Mg==",
    "Z Potentials": "MzI4NTgxMDk1NA==",
    "晚点Auto": "MzkzMDMyNDIxNQ==",
    "硅兔赛跑": "MzI4MDUzMTc3Mg==",
    "纪源资本": "MjM5MTk3NTYyMA==",
    "Founder Park": "Mzg5NTc0MjgwMw==",
    "甲子光年": "MzU5OTI0NTc3Mg==",
    "新智元": "MzI3MTA0MTk1MA==",
    "M小姐研习录": "MzUzNTEyNjc0OA==",
    "吴说Real": "MzI0ODgzMDE5MA==",
    "小丸子酱聊商业": "Mzg4ODkwNjA3OQ==",
    "林坤的学习思考": "Mzg3ODU2OTMzMA==",
    "线性资本": "MzAwNTAyMDAyNQ==",
    "36氪pro": "MzUxOTA3MzMzOQ==",
    "乌鸦智能说": "MzkyNTY1MjE2OA==",
    "Redbot": "Mzg5ODg0ODMyMg==",
    "AI寒武纪": "Mzg3MTkxMjYzOA==",
    "数字生命卡兹克": "MzIyMzA5NjEyMA==",
    "AI-paperdaily": "MzAxMzQyMzU5Nw=="
}

# Function to get raw HTML content from websites using Firecrawl
def get_raw_html(domain):
    try:
        # Use Jina to get the raw HTML
        url = f'https://r.jina.ai/https://{domain}'
        headers = {
            'Authorization': f'Bearer {jina_api}'
        }
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        response.raise_for_status()  # Raises an exception for 4XX/5XX responses
        
        # Return the raw HTML content
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error while fetching content from {domain}: {str(e)}"

# Function to get raw HTML for WeChat articles
def get_raw_html_for_weixin(full_url):
    try:
        # Use Jina to get the raw HTML
        jina_url = f'https://r.jina.ai/{full_url}'
        headers = {
            'Authorization': f'Bearer {jina_api}'
        }
        response = requests.get(jina_url, headers=headers)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Return the raw HTML content
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error while fetching content from {full_url}: {str(e)}"

# Function to get WeChat articles for a specific fakeid
def get_weixin_articles(fakeid, account_name):
    # 目标url
    url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
    cookie = "appmsglist_action_3918520287=card; rewardsn=; wxtokenkey=777; pac_uid=0_WFRCchx025Cww; *qimei*uuid42=191090f32121004a40ded1e5e650d9677d9210f8fb; *qimei*h38=e963446740ded1e5e650d96703000003119109; *qimei*q36=; ua_id=fIxXt1qo3N1AkUI9AAAAAE7bKLDM8dls2W8RivxiLs4=; wxuin=36409384414630; suid=user_0_WFRCchx025Cww; mm_lang=zh_CN; sig=h016ff31a4a1ff5262376ab723fd8d807ea82f9552e933b7d087ca0bd6cd2ce703cdaaf9f90ae8c1544; ab.storage.deviceId.f9c2b69f-2136-44e0-a55a-dff72d99aa19=g%3AYoJZqng6gcdvly5aBDxZqgiJ1GZ2%7Ce%3Aundefined%7Cc%3A1739462526631%7Cl%3A1739462526631; ab.storage.sessionId.f9c2b69f-2136-44e0-a55a-dff72d99aa19=g%3A7bafc696-6715-6e6b-565d-5695541d32ca%7Ce%3A1739464326655%7Cc%3A1739462526656%7Cl%3A1739462526656; *qimei*fingerprint=d91ba6f60a0e30a68c3644052fa00145; uuid=fa6efb10c0815d39c692922e8b0421d3; *clck=1mr2pfh|1|ftw|0; xid=dac261de760022f125b820a3532dd7e8; slave*sid=bUdyR0VlenBWcFNaeGt6T25uWEhYUXd1VTBheWtUVWxFdWZIVHhWSE1rTnRtaEtBUGlQb0hDMmV1NzRoS29qOXVjREJoZlBfckdtNGpNTk4xS1YxeEF3WTdrZGpKU01HelFNZm94VTFBeVFYSXhPWVN1MUJPNGdwWTJPVXR1SkFwcnJGR3RqR3JFTE1UVkgz; slave_user=gh_b89c7dbe2d0d; rand_info=CAESIIrl/lpNzhAVVw0EkwiG8FU/r1+wtjeHfL3PXReBWbqM; slave_bizuin=3918520287; bizuin=3918520287; _clsk=1332kwo|1740969186856|5|1|mp.weixin.qq.com/weheat-agent/payload/record"
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Mobile Safari/537.36",
    }
    data = {
        "token": "232435096",
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1",
        "action": "list_ex",
        "begin": "0",
        "count": "5",  # Only get the latest 5 articles
        "query": "",
        "fakeid": fakeid,
        "type": "9",
    }
    
    results_list = []
    
    try:
        content_json = requests.get(url, headers=headers, params=data).json()
        
        if "app_msg_list" not in content_json:
            return f"Error: Unable to fetch articles for {account_name}. Check the fakeid and cookie."
        
        content_list = content_json["app_msg_list"]
        
        # Get current time for comparison (3 days ago)
        three_days_ago = time.time() - (3 * 24 * 60 * 60)
        
        # Filter for articles within the last 3 days
        recent_articles = []
        for item in content_list:
            if item.get("create_time", 0) >= three_days_ago:
                recent_articles.append(item)
        
        st.write(f"找到 {len(recent_articles)} 篇过去3天内的文章")
        
        for item in recent_articles:
            title = item["title"]
            link = item["link"]
            create_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(item["create_time"]))
            
            # Get raw HTML using the full URL
            with st.spinner(f"获取文章内容: {title}"):
                html_content = get_raw_html_for_weixin(link)
            
            results_list.append({
                "title": title,
                "link": link,
                "create_time": create_time,
                "html_content": html_content
            })
            
            # Add a delay between requests
            time.sleep(random.randint(1, 2))
        
        return results_list
    
    except Exception as e:
        return f"Error fetching WeChat articles: {str(e)}"

# Function to analyze WeChat articles using Qwen
def analyze_weixin_article(article_info):
    title = article_info["title"]
    link = article_info["link"]
    create_time = article_info["create_time"]
    html_content = article_info["html_content"]
    
    messages = [
        {'role': 'system', 'content': 'You are a professional AI researcher. Analyze the WeChat article content and provide a concise summary.'},
        {'role': 'user', 'content': f'''
        Analyze this WeChat article and provide:
        1. A concise summary (150-200 words)
        2. Key points (3-5 bullet points)
        3. Relevance to AI, technology or investment trends
        
        Article Title: {title}
        Published: {create_time}
        Link: {link}
        
        HTML Content: {html_content[:30000]}  # Limit content to avoid token limits
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

# Function to prepare the message for Qwen LLM analysis
def analyze_with_qwen(domain, raw_html):
    messages = [
        {'role': 'system', 'content': 'You are a professional AI researcher. Analyze the raw HTML content and extract key topics in the following format: "1. Description | Website"'},
        {'role': 'user', 'content': f'''
        Analyze the raw HTML content from {domain} and provide the latest 10 topics with:
        1. Article titles in Chinese
        2. One-line descriptions in Chinese
        3. Website name
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
    
    # Create two sections with different tabs within the Trending Topics tab
    monitor_tabs = st.tabs(["网站监控", "微信公众号监控"])
    
    # Website monitoring section
    with monitor_tabs[0]:
        default_websites = ["lilianweng.github.io"]
        input_websites = st.text_area("网站域名 (逗号分隔):", value=', '.join(default_websites), height=100)
        websites = [site.strip() for site in input_websites.split(',')]
        
        if st.button("开始网站监控"):
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
    
    # WeChat public accounts monitoring section
    with monitor_tabs[1]:
        st.subheader("微信公众号监控")
        st.write("监控选定的微信公众号的最新文章 (仅获取过去3天的内容)")
        
        # Multi-select for WeChat accounts
        selected_accounts = st.multiselect(
            "选择要监控的微信公众号",
            options=list(weixin_accounts.keys()),
            default=["量子位", "机器之心"]
        )
        
        if st.button("开始微信监控"):
            if not selected_accounts:
                st.warning("请至少选择一个微信公众号进行监控。")
            else:
                for account_name in selected_accounts:
                    fakeid = weixin_accounts[account_name]
                    st.write(f"### 正在拉取 {account_name} 的最新文章...")
                    
                    # Get WeChat articles
                    articles = get_weixin_articles(fakeid, account_name)
                    
                    if isinstance(articles, str):  # Error occurred
                        st.error(articles)
                    else:
                        # Create an expander for each account
                        with st.expander(f"{account_name} - {len(articles)} 篇文章", expanded=True):
                            for idx, article in enumerate(articles):
                                # Display article info
                                st.write(f"**{idx+1}. {article['title']}**")
                                st.write(f"发布时间: {article['create_time']}")
                                st.write(f"链接: {article['link']}")
                                
                                # Analyze article content
                                with st.spinner(f"正在分析文章 {idx+1}..."):
                                    analysis = analyze_weixin_article(article)
                                    st.text_area(f"文章分析", analysis, height=200)
                                
                                st.markdown("---")
                    
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
    st.header("事实知识库")
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
    if len(st.session_state["local_facts"]) > 0:
        st.write("#### 网站信息")
        for idx, fact in enumerate(st.session_state["local_facts"], start=1):
            st.write(f"**{idx}.** {fact['url']} — {fact['desc']}")
    else:
        st.info("还没有添加任何网站信息。")
    
    if len(st.session_state["local_files"]) > 0:
        st.write("#### 上传的文件")
        for idx, file_info in enumerate(st.session_state["local_files"], start=1):
            st.write(f"**{idx}.** {file_info['file_name']}")
    else:
        st.info("还没有上传任何文件。")

# ----------------------- Tab 4: Direct Chat -----------------------
with tabs[3]:
    st.header("直接聊天")
    st.write("基于 Qwen、大模型、本地信息库以及 Deepseek 模型，您可以直接与 AI 进行对话。")
    
    # 选择聊天模式：包含 Qwen、本地知识库 (RAG) 和 Deepseek 聊天选项
    chat_mode = st.radio("选择聊天模式", ("Qwen聊天", "本地知识聊天(Qwen)", "Deepseek聊天"))
    
    # Chat input form (clears on submit)
    with st.form("chat_form", clear_on_submit=True):
        chat_input = st.text_input("输入您的消息：")
        submitted = st.form_submit_button("发送")
        if submitted and chat_input:
            st.session_state["chat_history"].append({"role": "user", "content": chat_input})
            if chat_mode == "Qwen聊天":
                reply = chat_with_qwen(chat_input)
            elif chat_mode == "本地知识聊天(Qwen)":
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