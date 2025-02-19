import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# Function to fetch and parse the webpage
def fetch_website_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for request errors
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the latest topics by extracting titles and summaries
        # For simplicity, assuming articles are in <article> or <h2> tags. Adjust as needed.
        articles = soup.find_all(['h2', 'article'])

        content = []
        for idx, article in enumerate(articles[:10]):  # Only fetch the latest 10 articles
            title = article.get_text().strip()
            one_liner = article.find_next('p').get_text().strip() if article.find_next('p') else "No summary available"
            content.append(f"{idx + 1}. \"{title}\", \"{one_liner}\", {url}")
        
        return content
    except Exception as e:
        return f"Error fetching content: {e}"

# Function to summarize the content using LLM
def summarize_content(content):
    api_key = os.getenv("DASHSCOPE_API_KEY")  # Replace with your API key if needed
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # Send the content to LLM for summarization
    try:
        completion = client.chat.completions.create(
            model="qwen-plus",  # Example model
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': f"Please summarize the following content into the latest 10 key ideas in the format: '1. title, one-liner description, website name': {content}"}
            ],
            extra_body={
                "enable_search": True
            }
        )
        
        # Correctly access the content from the response using model_dump_json()
        summarized_content = completion.model_dump_json()  # Get the response as JSON
        return summarized_content

    except Exception as e:
        print(f"Error: {e}")  # Catch any other errors
        return f"Error summarizing content: {e}"

# Streamlit UI
import streamlit as st

st.title("Website Content Analyzer and Summarizer")

# URL selection
st.sidebar.header("Select Websites to Analyze")
website_choices = [
    "https://www.qbitai.com/",
    "https://www.jiqizhixin.com/",
    "https://lilianweng.github.io/",
    "https://x.com/deepseek_ai"
]
selected_websites = st.sidebar.multiselect(
    "Choose websites to analyze:",
    website_choices,
    default=website_choices  # Default to analyzing all websites
)

if st.button("Analyze Websites"):
    # Loop through selected websites and fetch content
    all_content = []
    for website in selected_websites:
        st.subheader(f"Latest Topics from {website}")
        website_content = fetch_website_content(website)
        
        if isinstance(website_content, str) and website_content.startswith("Error"):
            st.error(website_content)
        else:
            for topic in website_content:
                st.write(topic)
            all_content.append("\n".join(website_content))
    
    # Combine all content from the websites
    combined_content = "\n\n".join(all_content)
    
    # Summarize the content using LLM
    st.subheader("Summarized Key Ideas from Each Website")
    summarized_content = summarize_content(combined_content)
    st.write(summarized_content)