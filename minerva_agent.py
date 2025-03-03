import requests
import streamlit as st
import datetime
import dashscope
from firecrawl import FirecrawlApp
import os
from openai import OpenAI 
import time
import random
import json
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

# WeChat scraping setup
weixin_url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
weixin_cookie = "appmsglist_action_3918520287=card; rewardsn=; wxtokenkey=777; pac_uid=0_WFRCchx025Cww; qimeiuuid42=191090f32121004a40ded1e5e650d9677d9210f8fb; qimeih38=e963446740ded1e5e650d96703000003119109; qimeiq36=; ua_id=fIxXt1qo3N1AkUI9AAAAAE7bKLDM8dls2W8RivxiLs4=; wxuin=36409384414630; suid=user_0_WFRCchx025Cww; mm_lang=zh_CN; sig=h016ff31a4a1ff5262376ab723fd8d807ea82f9552e933b7d087ca0bd6cd2ce703cdaaf9f90ae8c1544; ab.storage.deviceId.f9c2b69f-2136-44e0-a55a-dff72d99aa19=g%3AYoJZqng6gcdvly5aBDxZqgiJ1GZ2%7Ce%3Aundefined%7Cc%3A1739462526631%7Cl%3A1739462526631; ab.storage.sessionId.f9c2b69f-2136-44e0-a55a-dff72d99aa19=g%3A7bafc696-6715-6e6b-565d-5695541d32ca%7Ce%3A1739464326655%7Cc%3A1739462526656%7Cl%3A1739462526656; qimeifingerprint=d91ba6f60a0e30a68c3644052fa00145; uuid=fa6efb10c0815d39c692922e8b0421d3; clck=1mr2pfh|1|ftw|0; xid=dac261de760022f125b820a3532dd7e8; slavesid=bUdyR0VlenBWcFNaeGt6T25uWEhYUXd1VTBheWtUVWxFdWZIVHhWSE1rTnRtaEtBUGlQb0hDMmV1NzRoS29qOXVjREJoZlBfckdtNGpNTk4xS1YxeEF3WTdrZGpKU01HelFNZm94VTFBeVFYSXhPWVN1MUJPNGdwWTJPVXR1SkFwcnJGR3RqR3JFTE1UVkgz; slave_user=gh_b89c7dbe2d0d; rand_info=CAESIIrl/lpNzhAVVw0EkwiG8FU/r1+wtjeHfL3PXReBWbqM; slave_bizuin=3918520287; bizuin=3918520287; _clsk=1332kwo|1740969186856|5|1|mp.weixin.qq.com/weheat-agent/payload/record"
weixin_headers = {
    "Cookie": weixin_cookie,
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Mobile Safari/537.36",
}
weixin_data = {
    "token": "232435096",
    "lang": "zh_CN",
    "f": "json",
    "ajax": "1",
    "action": "list_ex",
    "begin": "0",
    "count": "5",
    "query": "",
    "fakeid": "",  # Will be set dynamically
    "type": "9",
}

# WeChat fakeid mapping
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

# Function to get raw HTML content from the websites using Firecrawl
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

# New function to analyze WeChat articles with Qwen
def analyze_weixin_articles(account_name, articles_data):
    # Prepare the article information for the LLM
    article_info = []
    for article in articles_data:
        article_info.append({
            "title": article.get("title", "无标题"),
            "link": article.get("link", ""),
            "publish_date": time.strftime("%Y-%m-%d %H:%M", time.localtime(article.get("create_time", 0))),
            "content": article.get("html_content", "")[:2000] if "html_content" in article else "无内容"
        })
    
    # Create a message for the LLM
    articles_summary = "\n".join([
        f"标题: {a['title']}\n发布日期: {a['publish_date']}\n链接: {a['link']}\n内容预览: {a['content'][:300]}...\n"
        for a in article_info
    ])
    
    messages = [
        {'role': 'system', 'content': 'You are a professional AI researcher analyzing WeChat articles.'},
        {'role': 'user', 'content': f'''
        分析以下来自微信公众号 "{account_name}" 的文章，提取关键主题并给出简短总结。
        对每篇文章，提供：
        1. 文章标题
        2. 发布日期
        3. 一句话中文摘要
        4. 关键观点（1-3个要点）
        
        当前日期: {datetime.date.today()}
        
        文章信息：
        {articles_summary}
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

# Function to get the raw HTML of a WeChat article
def get_weixin_article_html(url):
    try:
        # Use Jina to get the raw HTML
        jina_url = f'https://r.jina.ai/{url}'
        headers = {
            'Authorization': f'Bearer {jina_api}'
        }
        response = requests.get(jina_url, headers=headers)
        # Check if the request was successful
        response.raise_for_status()
        # Return the raw HTML content
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error while fetching content from {url}: {str(e)}"

# Function to get WeChat articles from the past 3 days
def get_weixin_recent_articles(account_name, fakeid):
    # Update the fakeid in the data
    weixin_data["fakeid"] = fakeid
    
    try:
        # Get the latest 5 articles (potentially covering 3 days)
        weixin_data["begin"] = 0
        weixin_data["count"] = 5
        
        content_json = requests.get(weixin_url, headers=weixin_headers, params=weixin_data).json()
        
        if "app_msg_list" not in content_json:
            return f"Error: Could not retrieve articles for {account_name}. Response: {content_json}"
        
        content_list = content_json["app_msg_list"]
        
        # Filter to only include articles from the last 3 days
        three_days_ago = time.time() - (3 * 24 * 60 * 60)
        recent_articles = [article for article in content_list if article.get("create_time", 0) >= three_days_ago]
        
        # Get the HTML content for each article
        for article in recent_articles:
            print(f"Fetching HTML for: {article['title']}")
            article["html_content"] = get_weixin_article_html(article["link"])
            # Add a delay between requests to avoid rate limiting
            time.sleep(random.randint(2, 4))
        
        return recent_articles
    
    except Exception as e:
        return f"Error while fetching WeChat articles for {account_name}: {str(e)}"

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
    
    # Create two sections with columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("网站监控")
        st.write("监控推流的各大信息网站的热点")
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
    
    with col2:
        st.subheader("微信公众号监控")
        st.write("监控微信公众号最近3天的文章")
        
        # Selection for WeChat accounts
        default_accounts = ["机器之心", "量子位", "新智元"]
        selected_accounts = st.multiselect(
            "选择要监控的微信公众号:",
            options=list(weixin_accounts.keys()),
            default=default_accounts
        )
        
        if st.button("开始微信监控"):
            if not selected_accounts:
                st.warning("请选择至少一个微信公众号")
            else:
                for account in selected_accounts:
                    st.write(f"### 正在拉取 {account} 的最近文章...")
                    fakeid = weixin_accounts.get(account)
                    
                    if not fakeid:
                        st.error(f"未找到 {account} 的fakeid")
                        continue
                    
                    articles = get_weixin_recent_articles(account, fakeid)
                    
                    if isinstance(articles, str) and ('Error' in articles):
                        st.error(articles)
                    else:
                        # Display basic article info
                        st.write(f"获取了 {len(articles)} 篇最近的文章")
                        
                        # Create a simple table with article info
                        article_table = []
                        for article in articles:
                            create_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(article.get("create_time", 0)))
                            article_table.append([article.get("title", "无标题"), create_time])
                        
                        st.table(pd.DataFrame(article_table, columns=["标题", "发布时间"]))
                        
                        # Analyze articles with Qwen
                        st.write("正在分析文章内容...")
                        analysis = analyze_weixin_articles(account, articles)
                        st.text_area(f"{account} 文章分析", analysis, height=300)
                    
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