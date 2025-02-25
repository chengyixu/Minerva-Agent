# -*- coding: utf-8 -*-

import streamlit as st
import datetime
import dashscope
from firecrawl import FirecrawlApp

# Initialize the Firecrawl app with API key
fire_api = "fc-343fd362814545f295a89dc14ec4ee09"
app = FirecrawlApp(api_key=fire_api)

# Function to get raw HTML content from the websites using Firecrawl
def get_raw_html(domain):
    try:
        # Use Firecrawl to crawl the website
        crawl_status = app.crawl_url(
            f'https://{domain}', 
            params={'limit': 100, 'scrapeOptions': {'formats': ['markdown', 'links']}},
            poll_interval=30
        )
        if crawl_status['success'] and crawl_status['status'] == 'completed':
            # Firecrawl response contains markdown content, you can retrieve it
            markdown_content = crawl_status['data'][0]['markdown']
            return markdown_content
        else:
            return f"Failed to retrieve content from {domain}. Status: {crawl_status['status']}"
    except Exception as e:
        return f"Error while fetching content from {domain}: {str(e)}"

# Function to prepare the message for Qwen LLM analysis
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
        model="qwen-max",
        messages=messages,
        enable_search=True,
        result_format='message'
    )
    return response['output']['choices'][0]['message']['content']

# Streamlit UI components
st.title("Minerva Agent - 信息监控与知识库")

# Create three tabs for different functionalities
tabs = st.tabs(["热点监控", "定时汇报", "事实知识库"])

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
            # Get raw HTML using Firecrawl
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
    # Placeholder for scheduling settings
    st.info("定时汇报功能开发中，敬请期待！")
    # Example placeholder: scheduling time input
    scheduled_time = st.time_input("选择汇报时间（例如每日定时）", datetime.time(hour=12, minute=0))
    st.write(f"当前设置的汇报时间为：{scheduled_time}")

# ----------------------- Tab 3: Local Factual Knowledge Base -----------------------
with tabs[2]:
    st.header("事实知识库")
    st.write("作为本地的事实知识库，您可以随时添加各种类型的信息源，并支持可验证的 cross check")
    # Placeholder for adding new sources
    with st.form("add_source_form"):
        new_source = st.text_input("输入新信息源网址:")
        source_desc = st.text_area("信息源描述:")
        submitted = st.form_submit_button("添加信息源")
        if submitted:
            # Placeholder for adding the new source to the knowledge base
            st.success(f"信息源 {new_source} 已添加！")
            st.write("（此处可实现将新信息源保存到数据库或本地存储的功能）")