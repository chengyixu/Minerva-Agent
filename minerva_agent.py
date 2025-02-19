import streamlit as st
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

# Function to translate the content into Chinese using LLM
def translate_to_chinese(content):
    api_key = "sk-1a28c3fcc7e044cbacd6faf47dc89755"
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # Send the content to LLM for translation
    completion = client.chat.completions.create(
        model="qwen-plus",  # Example model
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': f"Please translate the following text into Chinese: {content}"}
        ]
    )
    
    # Correctly access the content from the response
    translated_content = completion['choices'][0]['message']['content']
    return translated_content

# Streamlit UI
st.title("Website Content Analyzer")

# URL selection
st.sidebar.header("Select Websites to Analyze")
website_choices = [
    "https://www.qbitai.com/",
    "https://www.jiqizhixin.com/",
    "https://lilianweng.github.io/"
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
    
    # Translate the combined contents into Chinese
    st.subheader("Translated Content to Chinese")
    translated_content = translate_to_chinese(combined_content)
    st.write(translated_content)