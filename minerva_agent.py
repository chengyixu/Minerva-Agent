import streamlit as st
import requests
import datetime
import dashscope

# Function to get raw HTML content from the websites
def get_raw_html(domain):
    try:
        # Send request to the website and get the raw HTML content
        response = requests.get(f'http://{domain}')
        if response.status_code == 200:
            return response.content
        else:
            return f"Failed to retrieve content from {domain}. HTTP Status Code: {response.status_code}"
    except Exception as e:
        return f"Error while fetching content from {domain}: {str(e)}"

# Function to prepare the message for Qwen LLM analysis
def analyze_with_qwen(domain, raw_html):
    messages = [
        {'role': 'system', 'content': 'You are a web researcher. Analyze the raw HTML content and extract key topics in the following format: "1. Title | Description | Website"'},
        {'role': 'user', 'content': f'''
        Analyze the raw HTML content from {domain} and provide the latest 10 topics with:
        1. Article titles in English
        2. Article titles in Chinese
        3. One-line descriptions in English
        4. One-line descriptions in Chinese
        5. Website name
        Use current date: {datetime.date.today()}.
        HTML Content: {raw_html.decode('utf-8')}
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
st.title("Website Content Scraper & Analyzer")

# List of default websites
default_websites = [
    "qbitai.com",
    "jiqizhixin.com",
    "lilianweng.github.io",
    "x.com/deepseek_ai"
]

# Input for user to add websites
input_websites = st.text_area("Enter websites (comma separated)", 
                              value=', '.join(default_websites), 
                              height=100)

# Convert input string to a list of websites
websites = [site.strip() for site in input_websites.split(',')]

# Display results
for site in websites:
    st.write(f"### Scraping raw HTML from {site}...")
    
    # Get raw HTML
    raw_html = get_raw_html(site)
    
    # Check if there was an error
    if isinstance(raw_html, str) and ('Error' in raw_html or 'Failed' in raw_html):
        st.error(raw_html)
    else:
        st.write(f"Raw HTML retrieved from {site}. Analyzing with Qwen LLM...\n")
        
        # Perform Qwen analysis
        qwen_analysis = analyze_with_qwen(site, raw_html)
        
        # Display results
        st.write(f"### Analysis from {site}:\n")
        st.text_area(f"Analysis of {site}", qwen_analysis, height=300)

    st.markdown("\n---\n")