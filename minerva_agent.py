import requests
import streamlit as st
import datetime as dt
import dashscope
from firecrawl import FirecrawlApp
import os
import json
from openai import OpenAI 
from apify_client import ApifyClient  # Added for X/Twitter scraping
import time
from datetime import datetime, timedelta
import csv
import pickle

# Create data directory if it doesn't exist
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# File paths for persistent data storage
WEBSITE_DATA_PATH = os.path.join(DATA_DIR, "website_data.json")
TWITTER_DATA_PATH = os.path.join(DATA_DIR, "twitter_data.json")
TWITTER_INSIGHTS_PATH = os.path.join(DATA_DIR, "twitter_insights.json")
RAG_DATA_PATH = os.path.join(DATA_DIR, "rag_data.pkl")

# Helper functions for data persistence
def save_website_data(domain, analysis):
    """Save website analysis data to a JSON file"""
    # Load existing data if available
    if os.path.exists(WEBSITE_DATA_PATH):
        with open(WEBSITE_DATA_PATH, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    
    # Add timestamp to track when the data was scraped
    data[domain] = {
        "analysis": analysis,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save updated data
    with open(WEBSITE_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return data

def load_website_data():
    """Load website analysis data from JSON file"""
    if os.path.exists(WEBSITE_DATA_PATH):
        with open(WEBSITE_DATA_PATH, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_twitter_data(all_tweets, all_analyses):
    """Save Twitter data to JSON files"""
    # Save tweets and analyses
    twitter_data = {
        "tweets": all_tweets,
        "analyses": all_analyses,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(TWITTER_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(twitter_data, f, ensure_ascii=False, indent=4)
    
    return twitter_data

def save_twitter_insights(ai_insights, top_engaging_tweets):
    """Save Twitter insights to a JSON file"""
    insights_data = {
        "ai_insights": ai_insights,
        "top_engaging_tweets": top_engaging_tweets,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(TWITTER_INSIGHTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(insights_data, f, ensure_ascii=False, indent=4)
    
    return insights_data

def load_twitter_data():
    """Load Twitter data from JSON file"""
    if os.path.exists(TWITTER_DATA_PATH):
        with open(TWITTER_DATA_PATH, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"tweets": [], "analyses": [], "timestamp": None}
    return {"tweets": [], "analyses": [], "timestamp": None}

def load_twitter_insights():
    """Load Twitter insights from JSON file"""
    if os.path.exists(TWITTER_INSIGHTS_PATH):
        with open(TWITTER_INSIGHTS_PATH, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"ai_insights": None, "top_engaging_tweets": None, "timestamp": None}
    return {"ai_insights": None, "top_engaging_tweets": None, "timestamp": None}

def save_rag_data(local_facts, local_files):
    """Save RAG data using pickle for better handling of complex data structures"""
    rag_data = {
        "local_facts": local_facts,
        "local_files": local_files,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(RAG_DATA_PATH, 'wb') as f:
        pickle.dump(rag_data, f)
    
    return rag_data

def load_rag_data():
    """Load RAG data from pickle file"""
    if os.path.exists(RAG_DATA_PATH):
        with open(RAG_DATA_PATH, 'rb') as f:
            try:
                return pickle.load(f)
            except (pickle.PickleError, EOFError):
                return {"local_facts": [], "local_files": [], "timestamp": None}
    return {"local_facts": [], "local_files": [], "timestamp": None}

# Initialize session state variables with persistent data if available
if "local_facts" not in st.session_state:
    rag_data = load_rag_data()
    st.session_state["local_facts"] = rag_data["local_facts"]
if "local_files" not in st.session_state:
    if "local_facts" in st.session_state:  # Already loaded above
        rag_data = load_rag_data()
        st.session_state["local_files"] = rag_data["local_files"]
    else:
        st.session_state["local_files"] = []
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "twitter_results" not in st.session_state:
    twitter_data = load_twitter_data()
    st.session_state["twitter_results"] = {
        "tweets": twitter_data["tweets"],
        "analyses": twitter_data["analyses"]
    }
if "ai_insights" not in st.session_state:
    insights_data = load_twitter_insights()
    st.session_state["ai_insights"] = insights_data["ai_insights"]
if "top_engaging_tweets" not in st.session_state and "top_engaging_tweets" in load_twitter_insights():
    st.session_state["top_engaging_tweets"] = load_twitter_insights()["top_engaging_tweets"]

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
        Use current date: {dt.datetime.today().date()}.
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

# Function to translate tweet text using Qwen
def translate_tweet_with_qwen(tweet_text):
    messages = [
        {'role': 'system', 'content': 'You are a professional translator. Translate the following text from English to Chinese.'},
        {'role': 'user', 'content': f'''
        Translate the following tweet from English to Chinese:
        
        {tweet_text}
        '''}
    ]
    
    response = dashscope.Generation.call(
        api_key="sk-1a28c3fcc7e044cbacd6faf47dc89755",
        model="qwen-turbo",
        messages=messages,
        result_format='message'
    )
    
    return response['output']['choices'][0]['message']['content']

# Function to batch translate tweets - MODIFIED to use Qwen for translation
def batch_translate_tweets(tweets):
    if not tweets:
        return tweets  # Return empty list if no tweets
    
    # Process each tweet individually
    for tweet in tweets:
        if 'text' in tweet and tweet['text'].strip():
            # Translate the text with Qwen
            translation = translate_tweet_with_qwen(tweet['text'])
            tweet['translation'] = translation
        else:
            tweet['translation'] = "无文本可翻译"
    
    return tweets

# Function to get top engaging tweets
def get_top_engaging_tweets(all_tweets):
    # Get top 5 by retweets, replies, and likes
    top_retweets = sorted(all_tweets, key=lambda x: x.get('retweets', 0), reverse=True)[:5]
    top_replies = sorted(all_tweets, key=lambda x: x.get('replies', 0), reverse=True)[:5]
    top_likes = sorted(all_tweets, key=lambda x: x.get('likes', 0), reverse=True)[:5]
    
    # Translate each category
    st.info("正在翻译热门推文...")
    translated_retweets = batch_translate_tweets(top_retweets)
    translated_replies = batch_translate_tweets(top_replies)
    translated_likes = batch_translate_tweets(top_likes)
    
    top_tweets = {
        'top_retweets': translated_retweets,
        'top_replies': translated_replies,
        'top_likes': translated_likes
    }
    
    # Save the top tweets data for persistence
    save_twitter_insights(st.session_state.get("ai_insights"), top_tweets)
    
    return top_tweets

# Function to scrape AI influencer tweets from X (Twitter)
def scrape_ai_influencer_tweets():
    # Initialize the ApifyClient with your API token
    client = ApifyClient("apify_api_kbKxE4fYwbZOMBA30gS7DkbjinZqy91SEHb9")
    
    # Twitter handles of AI researchers and professionals
    twitter_handles = [
        "sama",               # Sam Altman
        "ylecun",             # Yann LeCun
        "AndrewYNg",          # Andrew Ng
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
                        # Get the author's full name from the first tweet or use handle as fallback
                        author_full_name = author_tweets[0]["author"] if author_tweets else handle
                        all_analyses.append({
                            "handle": handle,
                            "author_name": author_full_name,
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
    
    # After collecting all tweets, analyze them collectively for AI insights
    if all_tweets:
        # Changed to use Deepseek for AI insights
        ai_insights = extract_ai_insights_with_deepseek(all_tweets)
        st.session_state["ai_insights"] = ai_insights
        
        # Get and translate top engaging tweets
        st.info("正在获取和翻译最具互动性的推文...")
        top_tweets = get_top_engaging_tweets(all_tweets)
        st.session_state["top_engaging_tweets"] = top_tweets
        
        # Save all Twitter data for persistence
        save_twitter_data(all_tweets, all_analyses)
        save_twitter_insights(ai_insights, top_tweets)
    
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
        Analyze the following tweets from AI influencer @{handle} and provide in Chinese:
        1. key topics or trends in Chinese
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

# New function to extract AI insights from collected tweets using Deepseek
def extract_ai_insights_with_deepseek(tweets_data):
    # Organize tweets by their importance (using likes, retweets as indicators)
    sorted_tweets = sorted(
        tweets_data, 
        key=lambda x: (x.get('likes', 0) + x.get('retweets', 0)), 
        reverse=True
    )
    
    # Take top 100 tweets or all if less than 100
    top_tweets = sorted_tweets[:min(100, len(sorted_tweets))]
    
    # Prepare tweet content for analysis
    tweet_content = ""
    for tweet in top_tweets:
        tweet_content += f"Author: @{tweet['handle']} ({tweet['author']})\nTweet: {tweet['text']}\nLikes: {tweet['likes']}, Retweets: {tweet['retweets']}\nDate: {tweet['date']}\n\n"
    
    # Use OpenAI client with Deepseek model
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    messages = [
        {"role": "system", "content": "You are an expert AI researcher and analyst. Your task is to identify emerging trends, groundbreaking research, and industry shifts in artificial intelligence by analyzing tweets from leading AI professionals."},
        {"role": "user", "content": f'''
        Analyze the following collection of tweets from leading AI professionals and provide a comprehensive analysis of his/her AI insights:
        1. 最新AI技术趋势 (Latest AI Technology Trends): Identify emerging technologies or approaches that appear to be gaining momentum in the AI community.
        
        2. 研究方向前沿 (Research Frontiers): Extract research areas that seem to be at the cutting edge based on researcher discussions.
        
        3. 行业发展动态 (Industry Developments): Summarize key business or industry shifts that are evident from these tweets.
                
        4. 未来AI展望 (Future AI Outlook): Based on these experts' tweets, provide insights on where AI might be heading in the near future.
        
        Current date: {datetime.now().strftime('%Y-%m-%d')}.
        
        Tweets:
        {tweet_content}
        
        Provide your analysis in Chinese, with clear section headers and bullet points where appropriate, do not use Markdown format.
        '''}
    ]
    
    completion = client.chat.completions.create(
        model="deepseek-r1",
        messages=messages
    )
    
    # 获取思考过程和最终答案
    thinking_process = completion.choices[0].message.reasoning_content
    ai_insights = completion.choices[0].message.content
    
    # Save AI insights for persistence
    save_twitter_insights(ai_insights, st.session_state.get("top_engaging_tweets"))
    
    return {
        "思考过程": thinking_process,
        "分析结果": ai_insights
    }

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

# Function for chat using local factual knowledge (RAG)
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
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_message},
    ]
    completion = client.chat.completions.create(
        model="deepseek-r1",
        messages=messages
    )
    
    # 通过reasoning_content字段获取思考过程
    thinking_process = completion.choices[0].message.reasoning_content
    final_answer = completion.choices[0].message.content
    
    return {
        "思考过程": thinking_process,
        "最终答案": final_answer
    }

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
        
        # Load existing website data
        website_data = load_website_data()
        if website_data:
            st.info(f"已加载 {len(website_data)} 个网站的历史数据。上次更新时间: {list(website_data.values())[0].get('timestamp', '未知')}")
        
        default_websites = ["lilianweng.github.io",
        "www.jasonwei.net/blog",
        "muennighoff.github.io/",
        "thomwolf.io/",
        "dennyzhou.github.io/",
        "aiera.com.cn/news/",
        "www.jiqizhixin.com/",
        "foresightnews.pro/column/detail/101",
        ]
        input_websites = st.text_area("网站域名 (逗号分隔),从www开始, 例如（www.jasonwei.net/blog）:", value=', '.join(default_websites), height=100)
        websites = [site.strip() for site in input_websites.split(',')]
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("开始网站监控", key="scrape_websites"):
                for site in websites:
                    st.write(f"### 正在拉取 {site} 的数据...")
                    raw_html = get_raw_html(site)
                    if isinstance(raw_html, str) and ('Error' in raw_html or 'Failed' in raw_html):
                        st.error(raw_html)
                    else:
                        st.write("数据拉取成功，正在分析热点内容...")
                        analysis = analyze_with_qwen(site, raw_html)
                        # Save the analysis for this website
                        save_website_data(site, analysis)
                        st.text_area(f"{site} 热点分析", analysis, height=300)
                    st.markdown("---")
        
        with col2:
            if st.button("重新抓取", key="rescrape_websites"):
                st.warning("正在重新抓取所有网站数据...")
                # Clear existing data
                if os.path.exists(WEBSITE_DATA_PATH):
                    os.remove(WEBSITE_DATA_PATH)
                
                # Perform scraping as in the "开始网站监控" button
                for site in websites:
                    st.write(f"### 正在重新拉取 {site} 的数据...")
                    raw_html = get_raw_html(site)
                    if isinstance(raw_html, str) and ('Error' in raw_html or 'Failed' in raw_html):
                        st.error(raw_html)
                    else:
                        st.write("数据拉取成功，正在分析热点内容...")
                        analysis = analyze_with_qwen(site, raw_html)
                        # Save the analysis for this website
                        save_website_data(site, analysis)
                        st.text_area(f"{site} 热点分析", analysis, height=300)
                    st.markdown("---")
        
        # Display cached data if not scraping
        if website_data and not st.button("隐藏历史数据", key="hide_website_data"):
            st.subheader("已加载的网站数据")
            for site, data in website_data.items():
                with st.expander(f"{site} - 上次更新: {data.get('timestamp', '未知')}"):
                    st.text_area(f"{site} 缓存热点分析", data.get('analysis', '没有数据'), height=300)
    
    # X/Twitter monitoring tab
    with monitoring_tabs[1]:
        st.write("监控AI领域专家X动态")
        
        # Display information about the scraper
        st.info("这个功能会抓取AI领域专家的X动态，并用Deepseek进行分析，提取insights。")
        
        # Load existing Twitter data
        twitter_data = load_twitter_data()
        twitter_insights = load_twitter_insights()
        
        if twitter_data.get("tweets"):
            st.info(f"已加载 {len(twitter_data.get('tweets', []))} 条推文数据。上次更新时间: {twitter_data.get('timestamp', '未知')}")
        
        # Options for scraping
        top_influencers = [
            "sama",  # Sam Altman
            "ylecun",  # Yann LeCun
            "AndrewYNg",  # Andrew Ng
            "fchollet",  # François Chollet
            "karpathy",  # Andrej Karpathy
            "ilyasut",  # Ilya Sutskever
        ]
        selected_handles = st.multiselect("选择要监控的X账号:", options=top_influencers, default=top_influencers[:3])
        
        # Limit the number of selected handles
        max_handles = min(len(selected_handles) if selected_handles else 3, 10)
        
        col1, col2 = st.columns(2)
        with col1:
            # Scrape button
            if st.button("开始抓取X数据", key="scrape_twitter"):
                if selected_handles:
                    st.session_state["twitter_handles"] = selected_handles[:max_handles]
                    st.write(f"### 正在抓取 {len(selected_handles[:max_handles])} 个AI专家的Twitter数据...")
                    
                    # Call the function to scrape and analyze tweets
                    all_tweets, all_analyses = scrape_ai_influencer_tweets()
                    
                    # Store in session state for persistence
                    st.session_state["twitter_results"] = {
                        "tweets": all_tweets,
                        "analyses": all_analyses
                    }
                    
                    # Display analyses
                    if all_analyses:
                        # First display the collective AI insights
                        if st.session_state["ai_insights"]:
                            st.subheader("🔍 AI行业综合洞察")
                            st.text_area("AI行业洞察分析", st.session_state["ai_insights"], height=400)
                        
                        # Display top engaging tweets with translations
                        if "top_engaging_tweets" in st.session_state:
                            st.subheader("🔝 最具互动性的推文")
                            
                            top_tweets_tabs = st.tabs(["热门转发", "热门回复", "热门点赞"])
                            
                            # Display top retweets
                            with top_tweets_tabs[0]:
                                st.write("### 最高转发量推文")
                                for i, tweet in enumerate(st.session_state["top_engaging_tweets"]["top_retweets"], 1):
                                    with st.expander(f"{i}. @{tweet['handle']} (转发: {tweet['retweets']})"):
                                        st.markdown(f"""
                                        **作者：** {tweet['author']} (@{tweet['handle']})  
                                        **日期：** {tweet['date']}  
                                        **原文：** {tweet['text']}  
                                        **中文翻译：** {tweet['translation']}  
                                        **互动：** 👍 {tweet['likes']} | 🔁 {tweet['retweets']} | 💬 {tweet['replies']}  
                                        **链接：** [查看原文]({tweet['url']})
                                        """)
                            
                            # Display top replies
                            with top_tweets_tabs[1]:
                                st.write("### 最高回复量推文")
                                for i, tweet in enumerate(st.session_state["top_engaging_tweets"]["top_replies"], 1):
                                    with st.expander(f"{i}. @{tweet['handle']} (回复: {tweet['replies']})"):
                                        st.markdown(f"""
                                        **作者：** {tweet['author']} (@{tweet['handle']})  
                                        **日期：** {tweet['date']}  
                                        **原文：** {tweet['text']}  
                                        **中文翻译：** {tweet['translation']}  
                                        **互动：** 👍 {tweet['likes']} | 🔁 {tweet['retweets']} | 💬 {tweet['replies']}  
                                        **链接：** [查看原文]({tweet['url']})
                                        """)
                            
                            # Display top likes
                            with top_tweets_tabs[2]:
                                st.write("### 最高点赞量推文")
                                for i, tweet in enumerate(st.session_state["top_engaging_tweets"]["top_likes"], 1):
                                    with st.expander(f"{i}. @{tweet['handle']} (点赞: {tweet['likes']})"):
                                        st.markdown(f"""
                                        **作者：** {tweet['author']} (@{tweet['handle']})  
                                        **日期：** {tweet['date']}  
                                        **原文：** {tweet['text']}  
                                        **中文翻译：** {tweet['translation']}  
                                        **互动：** 👍 {tweet['likes']} | 🔁 {tweet['retweets']} | 💬 {tweet['replies']}  
                                        **链接：** [查看原文]({tweet['url']})
                                        """)
                        
                        # Then display individual analyses
                        st.subheader("个人推文分析")
                        for analysis_item in all_analyses:
                            handle = analysis_item["handle"]
                            author_name = analysis_item.get("author_name", handle)
                            analysis = analysis_item["analysis"]
                            
                            # Get tweets for this handle
                            handle_tweets = [t for t in all_tweets if t["handle"] == handle]
                            
                            # Create a container for each author
                            author_container = st.container()
                            with author_container:
                                st.markdown(f"### {author_name} (@{handle})")
                                
                                # Display analysis in the container
                                st.text_area(f"{handle} 推文分析", analysis, height=250)
                                
                                # Display tweets for this author
                                if handle_tweets:
                                    # Display raw tweets in a simple list format to avoid nesting expanders
                                    st.markdown(f"#### @{handle} 的原始推文 ({len(handle_tweets)} 条)")
                                    for tweet in handle_tweets:
                                        st.markdown(f"""
                                        **日期：** {tweet['date']}  
                                        **内容：** {tweet['text']}  
                                        **互动：** 👍 {tweet['likes']} | 🔁 {tweet['retweets']} | 💬 {tweet['replies']}  
                                        **链接：** [查看原文]({tweet['url']})
                                        ---
                                        """)
                                else:
                                    st.info(f"未找到 @{handle} 的推文数据")
                else:
                    st.warning("请选择至少一个X账号进行监控。")
        
        with col2:
            if st.button("重新抓取", key="rescrape_twitter"):
                if selected_handles:
                    st.warning("正在重新抓取所有X数据...")
                    # Clear existing data
                    if os.path.exists(TWITTER_DATA_PATH):
                        os.remove(TWITTER_DATA_PATH)
                    if os.path.exists(TWITTER_INSIGHTS_PATH):
                        os.remove(TWITTER_INSIGHTS_PATH)
                    
                    st.session_state["twitter_handles"] = selected_handles[:max_handles]
                    st.write(f"### 正在重新抓取这2天内 {len(selected_handles[:max_handles])} 个AI专家的Twitter数据，并用Deepseek分析（会有些慢）...")
                    
                    # Call the function to scrape and analyze tweets
                    all_tweets, all_analyses = scrape_ai_influencer_tweets()
                    
                    # Store in session state for persistence
                    st.session_state["twitter_results"] = {
                        "tweets": all_tweets,
                        "analyses": all_analyses
                    }
                    
                    # Similar display code as above
                else:
                    st.warning("请选择至少一个X账号进行监控。")
        
        # Display cached Twitter data if available and not scraping
        if (twitter_data.get("tweets") or twitter_insights.get("ai_insights")) and not st.button("隐藏历史数据", key="hide_twitter_data"):
            st.subheader("已加载的X数据")
            
            # Display AI insights
            if twitter_insights.get("ai_insights"):
                with st.expander(f"AI行业综合洞察 - 上次更新: {twitter_insights.get('timestamp', '未知')}"):
                    st.text_area("缓存AI行业洞察分析", twitter_insights.get("ai_insights", "没有数据"), height=400)
            
            # Display top engaging tweets if available
            if twitter_insights.get("top_engaging_tweets"):
                with st.expander("最具互动性的推文"):
                    top_engaging_tweets = twitter_insights.get("top_engaging_tweets", {})
                    
                    if "top_retweets" in top_engaging_tweets:
                        st.markdown("#### 最高转发量推文")
                        for i, tweet in enumerate(top_engaging_tweets["top_retweets"], 1):
                            st.markdown(f"""
                            **{i}. @{tweet['handle']} (转发: {tweet['retweets']})** - {tweet['text']}
                            """)
                    
                    if "top_likes" in top_engaging_tweets:
                        st.markdown("#### 最高点赞量推文")
                        for i, tweet in enumerate(top_engaging_tweets["top_likes"], 1):
                            st.markdown(f"""
                            **{i}. @{tweet['handle']} (点赞: {tweet['likes']})** - {tweet['text']}
                            """)

                    if "top_replies" in top_engaging_tweets:
                        st.markdown("#### 最高回复量推文")
                        for i, tweet in enumerate(top_engaging_tweets["top_replies"], 1):
                            st.markdown(f"""
                            **{i}. @{tweet['handle']} (回复: {tweet['replies']})** - {tweet['text']}
                            """)

            
            # Display individual analyses if available
            if twitter_data.get("analyses"):
                with st.expander("个人推文分析"):
                    for analysis_item in twitter_data.get("analyses", []):
                        handle = analysis_item["handle"]
                        author_name = analysis_item.get("author_name", handle)
                        st.markdown(f"**{author_name} (@{handle})**")
                        st.markdown(analysis_item["analysis"])
                        st.markdown("---")

# ----------------------- Tab 2: Scheduled Reports -----------------------
with tabs[1]:
    st.header("定时汇报")
    st.write("定时整合汇报各大信息网站的重要内容")
    st.info("开发中")
    scheduled_time = st.time_input("选择汇报时间（例如每日定时）", dt.time(hour=12, minute=0))
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
            # Save to persistent storage
            save_rag_data(st.session_state["local_facts"], st.session_state["local_files"])
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
                    # Save to persistent storage
                    save_rag_data(st.session_state["local_facts"], st.session_state["local_files"])
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
    
    # Add a clear button to reset the RAG database
    if st.button("清空所有本地信息"):
        st.session_state["local_facts"] = []
        st.session_state["local_files"] = []
        save_rag_data([], [])
        if os.path.exists(RAG_DATA_PATH):
            os.remove(RAG_DATA_PATH)
        st.success("已清空所有本地信息！")

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
    
    # Clear chat history button
    if st.button("清空聊天记录"):
        st.session_state["chat_history"] = []
        st.success("聊天记录已清空！")