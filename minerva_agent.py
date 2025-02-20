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
st.title("Minerva Agent")   

# List of default websites
default_websites = [
    "lilianweng.github.io",
    "qbitai.com",
    "jiqizhixin.com",
    "x.com/deepseek_ai"
]

# Input for user to add websites
input_websites = st.text_area("Website Domains(, Seperated)", 
                              value=', '.join(default_websites), 
                              height=100)

# Convert input string to a list of websites
websites = [site.strip() for site in input_websites.split(',')]

# Display results
for site in websites:
    st.write(f"### Pulling {site}...")
    
    # Get raw HTML using Firecrawl
    raw_html = get_raw_html(site)
    
    # Check if there was an error
    if isinstance(raw_html, str) and ('Error' in raw_html or 'Failed' in raw_html):
        st.error(raw_html)
    else:
        st.write(f"Raw HTML retrieved from {site}. Analyzing with Qwen LLM...\n")
        
        # Perform Qwen analysis
        qwen_analysis = analyze_with_qwen(site, raw_html)
        
        # Display results
        st.write(f"### {site} Summary:\n")
        st.text_area(f" {site}", qwen_analysis, height=300)

    st.markdown("\n---\n")