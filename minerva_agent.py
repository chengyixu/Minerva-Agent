import requests
import streamlit as st
import datetime
import dashscope
from firecrawl import FirecrawlApp
import os
from openai import OpenAI 
from apify_client import ApifyClient  # Added for X/Twitter scraping
import json
import time
from datetime import datetime, timedelta

# Initialize session state variables
if "local_facts" not in st.session_state:
    st.session_state["local_facts"] = []
if "local_files" not in st.session_state:
    st.session_state["local_files"] = []
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "twitter_results" not in st.session_state:  # New state for Twitter results
    st.session_state["twitter_results"] = []

# Initialize the Firecrawl app with API key
fire_api = "fc-343fd362814545f295a89dc14ec4ee09"
app = FirecrawlApp(api_key=fire_api)
jina_api = "jina_26a656e516224ce28e71cc3b28fa7b07zUchXe4_MJ_935m8SpS9-TNGL--w"

# Function to get raw HTML content from the websites using Firecrawl
def get_raw_html(domain):
    try:
        # Use Jina to get the raw HTML
        url = f'https://r.jina.ai/https://{domain}'
        headers = {
            'Authorization': 'Bearer jina_26a656e516224ce28e71cc3b28fa7b07zUchXe4_MJ_935m8SpS9-TNGL--w'
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

# Function to scrape AI influencer tweets from X (Twitter)
def scrape_ai_influencer_tweets():
    # Initialize the ApifyClient with your API token
    client = ApifyClient("apify_api_kbKxE4fYwbZOMBA30gS7DkbjinZqy91SEHb9")
    
    # Twitter handles of AI researchers and professionals
    twitter_handles = [
        "sama",               # Sam Altman
        "ylecun",             # Yann LeCun
        "AndrewYNg",          # Andrew Ng
        "fchollet",           # François Chollet
        "_KarenHao",          # Karen Hao
        "karpathy",           # Andrej Karpathy
        "SchmidhuberAI",      # Jürgen Schmidhuber
        "sarahookr",          # Sara Hooker
        "demishassabis",      # Demis Hassabis
        "saranormous",        # Sarah Guo
        "hardmaru",           # David Hardmaru
        "lilianweng",         # Lilian Weng
        "OriolVinyalsML",     # Oriol Vinyals
        "Michael_J_Black",    # Michael Black
        "JeffDean",           # Jeff Dean
        "goodfellow_ian",     # Ian Goodfellow
        "achowdhery",         # Aakanksha Chowdhery
        "PeterDiamandis",     # Peter H. Diamandis
        "GaryMarcus",         # Gary Marcus
        "giffmana",           # Lucas Beyer
        "rasbt",              # Sebastian Raschka
        "quaesita",           # Cassie Kozyrkov
        "KateKayeReports",    # Kate Kaye
        "EMostaque",          # Emad
        "drfeifei",           # Fei-Fei Li
        "DrJimFan",           # Jim Fan
        "omarsar0",           # Elvis Saravia
        "conniechan",         # Connie Chan
        "hugo_larochelle",    # Hugo Larochelle
        "benjedwards",        # Benj Edwards
        "rebecca_szkutak",    # Becca Szkutak
        "svlevine",           # Sergey Levine
        "ericschmidt",        # Eric Schmidt
        "ilyasut",            # Ilya Sutskever
        "patrickmineault",    # Patrick Mineault
        "natashajaques",      # Natasha Jaques
        "pabbeel",            # Pieter Abbeel
        "ESYudkowsky",        # Eliezer Yudkowsky
        "geoffreyhinton",     # Geoffrey Hinton
        "wintonARK",          # Brett Winton
        "jeffclune",          # Jeff Clune
        "RamaswmySridhar",    # Sridhar Ramaswamy
        "bentossell",         # Ben Tossell
        "johnschulman2",      # John Schulman
        "_akhaliq",           # Ahsen Khaliq
        "quocleix",           # Quoc Le
        "jackclarkSF",        # Jack Clark
        "mervenoyann",        # merve
        "DavidSHolz",         # David
        "natolambert",        # Nathan Lambert
        "RichardSocher",      # Richard Socher
        "mustafasuleymn",     # Mustafa Suleyman
        "ZoubinGhahrama1",    # Zoubin Ghahramani
        "nathanbenaich",      # Nathan Benaich
        "johnvmcdonnell",     # John McDonnell
        "tunguz",             # Bojan Tunguz
        "bengoertzel",        # Ben Goertzel
        "ch402",              # Chris Olah
        "Kseniase_",          # Ksenia Se
        "paulg",              # Paul Graham
        "rsalakhu",           # Russ Salakhutdinov
        "gdb",                # Greg Brockman
        "vivnat",             # Vivek Natarajan
        "bxchen",             # Brian X. Chen
        "AnimaAnandkumar",    # Anima Anandkumar
        "JeffreyTowson",      # Jeffrey Towson
        "Thom_Wolf",          # Thomas Wolf
        "johnplattml",        # John Platt
        "SamanyouGarg",       # Samanyou Garg
        "KirkDBorne",         # Kirk Bourne
        "Alber_RomGar",       # Alberto Romero
        "SilverJacket",       # Matthew Hutson
        "ecsquendor",         # Tim Scarfe
        "jordnb",             # Jordan Burgess
        "jluan",              # David Luan
        "NPCollapse",         # Connor Leahy
        "NaveenGRao",         # Naveen Rao
        "azeem",              # Azeem Azhar
        "Suhail",             # Suhail Doshi
        "maxjaderberg",       # Max Jaderberg
        "Kyle_L_Wiggers",     # Kyle Wiggers
        "cocoweixu",          # Wei Xu
        "aidangomezzz",       # Aidan Gomez
        "alexandr_wang",      # Alexandr Wang
        "CaimingXiong",       # Caiming Xiong
        "YiMaTweets",         # Yi Ma
        "notmisha",           # Misha Denil
        "peteratmsr",         # Peter Lee
        "shivon",             # Shivon Zilis
        "jackyliang42",       # Jacky Liang
        "v_vashishta",        # Vin Vashishta
        "xdh",                # Xuedong Huang
        "FryRsquared",        # Hannah Fry
        "ravi_lsvp",          # Ravi Mhatre
        "ClementDelangue",    # clem
        "oh_that_hat",        # Hattie Zhou
        "sapna",              # Sapna Maheshwari
        "VRLalchand",         # Vidhi Lalchand
        "svpino",             # Santiago L Valdarrama
        "ceobillionaire",     # Vincent Boucher
        "ykilcher",           # Yannic Kilcher
        "BornsteinMatt",      # Matt Bornstein
        "lachygroom",         # Lachy Groom
        "goodside",           # Riley Goodside
        "amasad",             # Amjad Masad
        "polynoamial",        # Noam Brown
        "sytelus",            # Shital Shah
    ]
    
    # Calculate date range for the last 2 days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    
    st.write(f"Scraping tweets from {start_date} to {end_date}")
    
    # Create directory for results if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    # Initialize results storage
    all_tweets = []
    all_analyses = []
    
    # Progress tracking for Streamlit
    progress = st.progress(0)
    status_text = st.empty()
    
    # CSV for structured data
    with open("results/ai_influencer_tweets.csv", "w", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write header
        csv_writer.writerow(["Author", "Twitter Handle", "text", "createdAt", "replyCount", "likeCount", "retweetCount", "url"])
        
        # Iterate through each Twitter handle
        for i, handle in enumerate(twitter_handles):
            status_text.text(f"[{i+1}/{len(twitter_handles)}] Scraping tweets for @{handle}...")
            progress.progress((i+1) / len(twitter_handles))
            
            # Prepare the Actor input
            run_input = {
                "maxItems": 100,  # Limit to 100 tweets per author
                "sort": "Latest",
                "author": handle,
                "start": start_date,
                "end": end_date,
            }
            
            # Implement retry logic
            max_retries = 3
            retries = 0
            success = False
            
            while retries < max_retries and not success:
                try:
                    # Run the Actor and wait for it to finish
                    run = client.actor("61RPP7dywgiy0JPD0").call(run_input=run_input)
                    
                    # Track tweets for this author
                    author_tweets = []
                    
                    # Fetch tweets from the dataset
                    for tweet in client.dataset(run["defaultDatasetId"]).iterate_items():
                        # Extract relevant data
                        author_name = tweet.get("authorName", "")
                        text = tweet.get("text", "")
                        date = tweet.get("createdAt", "")
                        replies = tweet.get("replyCount", 0)
                        likes = tweet.get("likeCount", 0)
                        retweets = tweet.get("retweetCount", 0)
                        url = tweet.get("url", "")
                        
                        # Create tweet object
                        tweet_data = {
                            "author": author_name,
                            "handle": handle,
                            "text": text,
                            "date": date,
                            "replies": replies,
                            "likes": likes,
                            "retweets": retweets,
                            "url": url
                        }
                        
                        # Add to collections
                        author_tweets.append(tweet_data)
                        all_tweets.append(tweet_data)
                        
                        # Write to CSV
                        csv_writer.writerow([author_name, handle, text, date, replies, likes, retweets, url])
                    
                    # Save individual author results to JSON
                    if author_tweets:
                        with open(f"results/{handle}_tweets.json", "w", encoding="utf-8") as f:
                            json.dump(author_tweets, f, indent=4)
                        
                        # Analyze tweets with Qwen
                        analysis = analyze_tweets_with_qwen(handle, author_tweets)
                        all_analyses.append({
                            "handle": handle,
                            "analysis": analysis
                        })
                    
                    st.write(f"  Scraped {len(author_tweets)} tweets for @{handle}")
                    success = True
                    
                except Exception as e:
                    retries += 1
                    st.error(f"  Error (attempt {retries}/{max_retries}): {e}")
                    if retries < max_retries:
                        st.info(f"  Retrying in 10 seconds...")
                        time.sleep(10)
                    else:
                        st.error(f"  Failed to scrape tweets for @{handle} after {max_retries} attempts.")
            
            # Add a delay between authors to respect rate limits
            if i < len(twitter_handles) - 1:  # Don't delay after the last author
                time.sleep(3)
    
    # Final summary
    progress.empty()
    status_text.empty()
    st.success(f"Scraped a total of {len(all_tweets)} tweets from {len(twitter_handles)} AI influencers")
    
    return all_tweets, all_analyses

# Function to analyze tweets with Qwen
def analyze_tweets_with_qwen(handle, tweets_data):
    # Prepare tweet text for analysis
    tweet_content = ""
    for tweet in tweets_data:
        tweet_content += f"Tweet: {tweet['text']}\nDate: {tweet['date']}\nURL: {tweet['url']}\n\n"
    
    messages = [
        {'role': 'system', 'content': 'You are a professional AI researcher. Analyze the tweets and extract key insights and topics.'},
        {'role': 'user', 'content': f'''
        Analyze the following tweets from AI influencer @{handle} and provide:
        1. 5 key topics or trends in Chinese
        2. Brief summary of main points in Chinese
        3. Any significant announcements or news in Chinese
        
        Current date: {datetime.now().strftime('%Y-%m-%d')}.
        
        Tweets:
        {tweet_content}
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
    
    # Create subtabs for different monitoring sources
    monitoring_tabs = st.tabs(["网站监控", "X/Twitter监控"])
    
    # Website monitoring tab
    with monitoring_tabs[0]:
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
    
    # X/Twitter monitoring tab (NEW)
    with monitoring_tabs[1]:
        st.write("监控AI领域专家Twitter动态")
        
        # Display information about the scraper
        st.info("这个功能会抓取AI领域专家的Twitter动态，并通过同样的Qwen模型进行分析，提取关键见解。")
        
        # Options for scraping
        top_influencers = ["sama", "ylecun", "AndrewYNg", "fchollet", "karpathy", "demishassabis", "drfeifei", "geoffreyhinton", "goodside", "EMostaque"]
        selected_handles = st.multiselect("选择要监控的Twitter账号 (最多10个):", options=top_influencers, default=top_influencers[:3])
        
        # Limit the number of selected handles
        max_handles = min(len(selected_handles) if selected_handles else 3, 10)
        
        # Scrape button
        if st.button("开始抓取X/Twitter数据"):
            if selected_handles:
                st.session_state["twitter_handles"] = selected_handles[:max_handles]
                st.write(f"### 正在抓取 {len(st.session_state['twitter_handles'])} 个AI专家的Twitter数据...")
                
                # Call the function to scrape and analyze tweets
                all_tweets, all_analyses = scrape_ai_influencer_tweets()
                
                # Store in session state for persistence
                st.session_state["twitter_results"] = {
                    "tweets": all_tweets,
                    "analyses": all_analyses
                }
                
                # Display analyses
                if all_analyses:
                    for analysis_item in all_analyses:
                        handle = analysis_item["handle"]
                        analysis = analysis_item["analysis"]
                        
                        st.subheader(f"@{handle} 分析")
                        st.text_area(f"{handle} 推文分析", analysis, height=250)
                        
                        # Get tweets for this handle
                        handle_tweets = [t for t in all_tweets if t["handle"] == handle]
                        
                        with st.expander(f"查看 @{handle} 的原始推文 ({len(handle_tweets)} 条)"):
                            for tweet in handle_tweets:
                                st.markdown(f"""
                                **日期：** {tweet['date']}  
                                **内容：** {tweet['text']}  
                                **互动：** 👍 {tweet['likes']} | 🔁 {tweet['retweets']} | 💬 {tweet['replies']}  
                                **链接：** [查看原文]({tweet['url']})
                                ---
                                """)
            else:
                st.warning("请选择至少一个Twitter账号进行监控。")
        
        # Display previously fetched results if available
        elif "twitter_results" in st.session_state and st.session_state["twitter_results"]:
            st.write("### 最近一次分析结果")
            
            for analysis_item in st.session_state["twitter_results"]["analyses"]:
                handle = analysis_item["handle"]
                analysis = analysis_item["analysis"]
                
                st.subheader(f"@{handle} 分析")
                st.text_area(f"{handle} 推文分析", analysis, height=250)
                
                # Get tweets for this handle
                handle_tweets = [t for t in st.session_state["twitter_results"]["tweets"] if t["handle"] == handle]
                
                with st.expander(f"查看 @{handle} 的原始推文 ({len(handle_tweets)} 条)"):
                    for tweet in handle_tweets:
                        st.markdown(f"""
                        **日期：** {tweet['date']}  
                        **内容：** {tweet['text']}  
                        **互动：** 👍 {tweet['likes']} | 🔁 {tweet['retweets']} | 💬 {tweet['replies']}  
                        **链接：** [查看原文]({tweet['url']})
                        ---
                        """)

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