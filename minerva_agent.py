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
st.title("Minerva Agent - ��Ϣ�����֪ʶ��")

# Create three tabs for different functionalities
tabs = st.tabs(["�ȵ���", "��ʱ�㱨", "��ʵ֪ʶ��"])

# ----------------------- Tab 1: Trending Topics Monitoring -----------------------
with tabs[0]:
    st.header("�ȵ���")
    st.write("��������ĸ�����Ϣ��վ���ȵ�")
    default_websites = ["lilianweng.github.io"]
    input_websites = st.text_area("��վ���� (���ŷָ�):", value=', '.join(default_websites), height=100)
    websites = [site.strip() for site in input_websites.split(',')]
    
    if st.button("��ʼ���"):
        for site in websites:
            st.write(f"### ������ȡ {site} ������...")
            # Get raw HTML using Firecrawl
            raw_html = get_raw_html(site)
            if isinstance(raw_html, str) and ('Error' in raw_html or 'Failed' in raw_html):
                st.error(raw_html)
            else:
                st.write("������ȡ�ɹ������ڷ����ȵ�����...")
                analysis = analyze_with_qwen(site, raw_html)
                st.text_area(f"{site} �ȵ����", analysis, height=300)
            st.markdown("---")

# ----------------------- Tab 2: Scheduled Reports -----------------------
with tabs[1]:
    st.header("��ʱ�㱨")
    st.write("��ʱ���ϻ㱨������Ϣ��վ����Ҫ����")
    # Placeholder for scheduling settings
    st.info("��ʱ�㱨���ܿ����У������ڴ���")
    # Example placeholder: scheduling time input
    scheduled_time = st.time_input("ѡ��㱨ʱ�䣨����ÿ�ն�ʱ��", datetime.time(hour=12, minute=0))
    st.write(f"��ǰ���õĻ㱨ʱ��Ϊ��{scheduled_time}")

# ----------------------- Tab 3: Local Factual Knowledge Base -----------------------
with tabs[2]:
    st.header("��ʵ֪ʶ��")
    st.write("��Ϊ���ص���ʵ֪ʶ�⣬��������ʱ���Ӹ������͵���ϢԴ����֧�ֿ���֤�� cross check")
    # Placeholder for adding new sources
    with st.form("add_source_form"):
        new_source = st.text_input("��������ϢԴ��ַ:")
        source_desc = st.text_area("��ϢԴ����:")
        submitted = st.form_submit_button("������ϢԴ")
        if submitted:
            # Placeholder for adding the new source to the knowledge base
            st.success(f"��ϢԴ {new_source} �����ӣ�")
            st.write("���˴���ʵ�ֽ�����ϢԴ���浽���ݿ�򱾵ش洢�Ĺ��ܣ�")