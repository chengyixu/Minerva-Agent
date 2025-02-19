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

        # Extract text from paragraphs or other relevant elements
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs])
        return content
    except Exception as e:
        return f"Error fetching content: {e}"

# Streamlit UI
st.title("Website Content Analyzer")

# Input URL
url = st.text_input("Enter the website URL:", "https://lilianweng.github.io/")

if st.button("Analyze Website"):
    # Fetch content from the provided URL
    website_content = fetch_website_content(url)

    if website_content.startswith("Error"):
        st.error(website_content)
    else:
        # Initialize the OpenAI client
        api_key = "sk-1a28c3fcc7e044cbacd6faf47dc89755"
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        # Pass the website content to the OpenAI model for further processing
        completion = client.chat.completions.create(
            model="qwen-plus",  # Example model
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': f"Here is some content from the website: {website_content}. How can I help you with it?"}
            ],
            extra_body={
                "enable_search": True
            }
        )

        # Display result
        st.subheader("Response from AI")
        st.json(completion.model_dump_json())