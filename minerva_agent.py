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
    
    # 注意：WeChat cookies经常过期，可能需要定期更新
    cookie = "appmsglist_action_3918520287=card; rewardsn=; wxtokenkey=777; pac_uid=0_WFRCchx025Cww; *qimei*uuid42=191090f32121004a40ded1e5e650d9677d9210f8fb; *qimei*h38=e963446740ded1e5e650d96703000003119109; *qimei*q36=; ua_id=fIxXt1qo3N1AkUI9AAAAAE7bKLDM8dls2W8RivxiLs4=; wxuin=36409384414630; suid=user_0_WFRCchx025Cww; mm_lang=zh_CN; sig=h016ff31a4a1ff5262376ab723fd8d807ea82f9552e933b7d087ca0bd6cd2ce703cdaaf9f90ae8c1544; ab.storage.deviceId.f9c2b69f-2136-44e0-a55a-dff72d99aa19=g%3AYoJZqng6gcdvly5aBDxZqgiJ1GZ2%7Ce%3Aundefined%7Cc%3A1739462526631%7Cl%3A1739462526631; ab.storage.sessionId.f9c2b69f-2136-44e0-a55a-dff72d99aa19=g%3A7bafc696-6715-6e6b-565d-5695541d32ca%7Ce%3A1739464326655%7Cc%3A1739462526656%7Cl%3A1739462526656; *qimei*fingerprint=d91ba6f60a0e30a68c3644052fa00145; uuid=fa6efb10c0815d39c692922e8b0421d3; *clck=1mr2pfh|1|ftw|0; xid=dac261de760022f125b820a3532dd7e8; slave*sid=bUdyR0VlenBWcFNaeGt6T25uWEhYUXd1VTBheWtUVWxFdWZIVHhWSE1rTnRtaEtBUGlQb0hDMmV1NzRoS29qOXVjREJoZlBfckdtNGpNTk4xS1YxeEF3WTdrZGpKU01HelFNZm94VTFBeVFYSXhPWVN1MUJPNGdwWTJPVXR1SkFwcnJGR3RqR3JFTE1UVkgz; slave_user=gh_b89c7dbe2d0d; rand_info=CAESIIrl/lpNzhAVVw0EkwiG8FU/r1+wtjeHfL3PXReBWbqM; slave_bizuin=3918520287; bizuin=3918520287; _clsk=1332kwo|1740969186856|5|1|mp.weixin.qq.com/weheat-agent/payload/record"
    
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10&lang=zh_CN&token=232435096",
    }
    
    # 参考原始参数，但可能需要更新token
    data = {
        "token": "232435096", # 这个token可能需要更新
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1",
        "action": "list_ex",
        "begin": "0",
        "count": "5",  # 获取最新5篇文章
        "query": "",
        "fakeid": fakeid,
        "type": "9",
    }
    
    results_list = []
    
    try:
        # 记录请求信息便于调试
        st.write(f"正在请求微信公众号文章，fakeid: {fakeid}")
        
        # 发送请求获取数据
        response = requests.get(url, headers=headers, params=data)
        
        # 检查HTTP响应状态
        if response.status_code != 200:
            return f"Error: HTTP status {response.status_code} for {account_name}. 请求失败。"
        
        # 尝试解析JSON
        try:
            content_json = response.json()
        except Exception as json_error:
            return f"Error: JSON解析失败: {str(json_error)}. 响应内容: {response.text[:200]}..."
        
        # 显示完整的响应内容供调试
        st.write("API响应内容(前200字符):", response.text[:200])
        
        # 检查API返回的错误码
        if content_json.get("base_resp", {}).get("ret") != 0:
            error_msg = content_json.get("base_resp", {}).get("err_msg", "未知错误")
            return f"Error: API错误 {account_name}. 错误代码: {content_json.get('base_resp', {}).get('ret')}, 错误信息: {error_msg}"
        
        # 检查是否有文章列表
        if "app_msg_list" not in content_json:
            # 输出完整的JSON以便调试
            st.write("完整响应(用于调试):", content_json)
            return f"Error: 无法获取 {account_name} 的文章列表。app_msg_list 字段缺失。"
        
        content_list = content_json["app_msg_list"]
        
        # 检查文章列表是否为空
        if not content_list:
            return f"提示: {account_name} 的文章列表为空，没有可获取的文章。"
        
        # 计算3天前的时间戳
        three_days_ago = time.time() - (3 * 24 * 60 * 60)
        
        # 过滤最近3天的文章
        recent_articles = []
        for item in content_list:
            if item.get("create_time", 0) >= three_days_ago:
                recent_articles.append(item)
        
        st.write(f"找到 {len(recent_articles)} 篇过去3天内的文章")
        
        # 如果没有最近3天的文章，返回最新的一篇作为样例
        if not recent_articles and content_list:
            st.write("注意: 没有找到3天内的文章，将展示最新的一篇文章作为示例")
            recent_articles = [content_list[0]]
        
        # 处理每篇文章
        for item in recent_articles:
            title = item["title"]
            link = item["link"]
            create_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(item["create_time"]))
            
            # 获取文章HTML
            with st.spinner(f"获取文章内容: {title}"):
                html_content = get_raw_html_for_weixin(link)
            
            results_list.append({
                "title": title,
                "link": link,
                "create_time": create_time,
                "html_content": html_content
            })
            
            # 添加随机延迟，避免请求过于频繁
            time.sleep(random.randint(1, 2))
        
        return results_list
    
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        st.error(f"获取微信文章时出错: {str(e)}")
        st.code(error_traceback)
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
        
        # 添加调试和帮助信息
        with st.expander("常见问题与故障排除", expanded=False):
            st.markdown("""
            ### 常见问题与故障排除
            
            1. **无法获取文章**
               - WeChat cookies可能已过期：这些通常在1-2周后过期
               - Token可能需要更新：公众号平台更新后token会变化
               - 请求频率过高：添加延迟或减少批量请求数量
            
            2. **API错误代码**
               - 错误码-3: 通常表示cookie或token无效
               - 错误码200013: 可能是请求频率受限
               - 错误码200003: 可能是无权限访问
               
            3. **调试建议**
               - 使用最新的cookie和token
               - 确保使用正确的fakeid
               - 检查网络连接状态
            """)
            
            # 添加手动测试表单
            st.subheader("手动测试接口")
            with st.form("test_api_form"):
                test_account = st.selectbox("选择账号测试", options=list(weixin_accounts.keys()))
                update_cookie = st.text_area("更新Cookie (可选):", height=100)
                update_token = st.text_input("更新Token (可选):", value="232435096")
                submitted = st.form_submit_button("测试接口")
                
                if submitted:
                    fakeid = weixin_accounts[test_account]
                    st.write(f"测试账号: {test_account}")
                    st.write(f"Fakeid: {fakeid}")
                    
                    # 构建测试请求
                    url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
                    
                    headers = {
                        "Cookie": update_cookie if update_cookie else "appmsglist_action_3918520287=card; rewardsn=; wxtokenkey=777; pac_uid=0_WFRCchx025Cww; *qimei*uuid42=191090f32121004a40ded1e5e650d9677d9210f8fb; *qimei*h38=e963446740ded1e5e650d96703000003119109; *qimei*q36=; ua_id=fIxXt1qo3N1AkUI9AAAAAE7bKLDM8dls2W8RivxiLs4=; wxuin=36409384414630; suid=user_0_WFRCchx025Cww; mm_lang=zh_CN; sig=h016ff31a4a1ff5262376ab723fd8d807ea82f9552e933b7d087ca0bd6cd2ce703cdaaf9f90ae8c1544",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    }
                    
                    data = {
                        "token": update_token,
                        "lang": "zh_CN",
                        "f": "json",
                        "ajax": "1",
                        "action": "list_ex",
                        "begin": "0",
                        "count": "5",
                        "query": "",
                        "fakeid": fakeid,
                        "type": "9",
                    }
                    
                    try:
                        response = requests.get(url, headers=headers, params=data)
                        st.write(f"HTTP状态码: {response.status_code}")
                        
                        try:
                            json_response = response.json()
                            st.json(json_response)
                        except:
                            st.write("无法解析JSON响应")
                            st.write(response.text)
                    except Exception as e:
                        st.error(f"测试请求失败: {str(e)}")
        
        # 提示用户当前接口状态
        st.info("注意：在微信公众平台的API更新后，当前的cookie和token可能需要更新。如果遇到问题，请使用上方的调试工具测试并更新接口参数。")
        
        # Multi-select for WeChat accounts
        selected_accounts = st.multiselect(
            "选择要监控的微信公众号",
            options=list(weixin_accounts.keys()),
            default=["量子位", "机器之心"]
        )
        
        # 添加每次只监控一个账号的选项
        monitor_mode = st.radio(
            "监控模式",
            ["批量监控所有选中账号", "单独监控每个账号(推荐)"]
        )
        
        if st.button("开始微信监控"):
            if not selected_accounts:
                st.warning("请至少选择一个微信公众号进行监控。")
            else:
                if monitor_mode == "单独监控每个账号(推荐)":
                    # 创建账号选择器
                    account_to_monitor = st.selectbox(
                        "选择要监控的账号",
                        options=selected_accounts
                    )
                    
                    if st.button(f"监控 {account_to_monitor}"):
                        fakeid = weixin_accounts[account_to_monitor]
                        st.write(f"### 正在拉取 {account_to_monitor} 的最新文章...")
                        
                        # 获取文章
                        articles = get_weixin_articles(fakeid, account_to_monitor)
                        
                        if isinstance(articles, str):  # 出错
                            st.error(articles)
                        else:
                            # 为每个账号创建一个可展开部分
                            with st.expander(f"{account_to_monitor} - {len(articles)} 篇文章", expanded=True):
                                for idx, article in enumerate(articles):
                                    # 显示文章信息
                                    st.write(f"**{idx+1}. {article['title']}**")
                                    st.write(f"发布时间: {article['create_time']}")
                                    st.write(f"链接: {article['link']}")
                                    
                                    # 分析文章内容
                                    with st.spinner(f"正在分析文章 {idx+1}..."):
                                        analysis = analyze_weixin_article(article)
                                        st.text_area(f"文章分析", analysis, height=200)
                                    
                                    st.markdown("---")
                else:
                    # 批量监控所有选中账号
                    for account_name in selected_accounts:
                        fakeid = weixin_accounts[account_name]
                        st.write(f"### 正在拉取 {account_name} 的最新文章...")
                        
                        # 获取微信文章
                        articles = get_weixin_articles(fakeid, account_name)
                        
                        if isinstance(articles, str):  # 出错
                            st.error(articles)
                        else:
                            # 为每个账号创建一个可展开部分
                            with st.expander(f"{account_name} - {len(articles)} 篇文章", expanded=True):
                                for idx, article in enumerate(articles):
                                    # 显示文章信息
                                    st.write(f"**{idx+1}. {article['title']}**")
                                    st.write(f"发布时间: {article['create_time']}")
                                    st.write(f"链接: {article['link']}")
                                    
                                    # 分析文章内容
                                    with st.spinner(f"正在分析文章 {idx+1}..."):
                                        analysis = analyze_weixin_article(article)
                                        st.text_area(f"文章分析", analysis, height=200)
                                    
                                    st.markdown("---")
                        
                        # 添加延迟，避免批量请求被封
                        time.sleep(5)
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