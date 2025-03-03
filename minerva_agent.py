import requests
import streamlit as st
import datetime
import dashscope
from firecrawl import FirecrawlApp
import os
from openai import OpenAI 

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
    
    # Build a context string from each stored source �C here we simply take the first 1000 characters per source
    context_text = ""
    for source in local_facts:
        context_text += f"����վ�� {source['url']}\n{source['content'][:1000]}\n"
    for file_info in local_files:
        context_text += f"���ļ��� {file_info['file_name']}\n{file_info['content'][:1000]}\n"
    
    if not context_text:
        context_text = "��ǰû�б�����Ϣ��"
        
    messages = [
        {"role": "system", "content": f"����һ�����ڱ�����ʵ֪ʶ����������֡������ǲ����ĵ��������ڸ����ش����⣺\n{context_text}\n�������Щ���ݻش��û����⡣"},
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
        model="deepseek-r1",  # ʹ�� deepseek ģ��
        messages=messages
    )
    return completion.choices[0].message.content

# ----------------------- Streamlit UI -----------------------
st.title("Minerva Agent")

# Create four tabs for different functionalities
tabs = st.tabs(["�ȵ���", "��ʱ�㱨", "��ʵ֪ʶ�� (RAG)", "ֱ������"])

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
    st.info("������")
    scheduled_time = st.time_input("ѡ��㱨ʱ�䣨����ÿ�ն�ʱ��", datetime.time(hour=12, minute=0))
    st.write(f"��ǰ���õĻ㱨ʱ��Ϊ��{scheduled_time}")

# ----------------------- Tab 3: Local Factual Knowledge Base (RAG) -----------------------
with tabs[2]:
    st.header("��ʵ֪ʶ��")
    st.write("�ϴ��ļ���������վ��ϵͳ����ȡ���ݣ���������ʱ������Щ��Ϣ���лش�")
    
    # Form to add a new website source �C it immediately fetches and stores content.
    with st.form("add_source_form"):
        new_source = st.text_input("��������ϢԴ��ַ:")
        source_desc = st.text_area("��ϢԴ����:")
        submitted = st.form_submit_button("������ϢԴ")
        if submitted and new_source:
            st.info(f"���ڴ� {new_source} ץȡ����...")
            # Remove potential protocol parts for get_raw_html function
            domain = new_source.replace("https://", "").replace("http://", "").strip()
            raw_content = get_raw_html(domain)
            st.session_state["local_facts"].append({
                "type": "website",
                "url": new_source,
                "desc": source_desc,
                "content": raw_content
            })
            st.success(f"��ϢԴ {new_source} �����ӣ�����ȡ���ݣ�")
    
    st.markdown("---")
    # Form to upload files �C the app processes and extracts text content.
    with st.form("upload_file_form", clear_on_submit=True):
        uploaded_files = st.file_uploader("ѡ��Ҫ�ϴ����ļ���֧�����и�ʽ��", accept_multiple_files=True)
        file_submitted = st.form_submit_button("�ϴ��ļ�")
        if file_submitted and uploaded_files:
            for file in uploaded_files:
                try:
                    file_bytes = file.getvalue()
                    # ���Խ���Ϊ UTF-8 �ı�
                    try:
                        file_text = file_bytes.decode("utf-8")
                    except Exception:
                        file_text = str(file_bytes)
                    st.session_state["local_files"].append({
                        "type": "file",
                        "file_name": file.name,
                        "content": file_text
                    })
                    st.success(f"�ļ� {file.name} ���ϴ���������")
                except Exception as e:
                    st.error(f"�����ļ� {file.name} ʱ������{e}")
    
    st.markdown("### ��ǰ������Ϣ")
    if st.session_state["local_facts"]:
        st.write("#### ��վ��Ϣ")
        for idx, fact in enumerate(st.session_state["local_facts"], start=1):
            st.write(f"**{idx}.** {fact['url']} �� {fact['desc']}")
    else:
        st.info("��û�������κ���վ��Ϣ��")
    
    if st.session_state["local_files"]:
        st.write("#### �ϴ����ļ�")
        for idx, file_info in enumerate(st.session_state["local_files"], start=1):
            st.write(f"**{idx}.** {file_info['file_name']}")
    else:
        st.info("��û���ϴ��κ��ļ���")

# ----------------------- Tab 4: Direct Chat -----------------------
with tabs[3]:
    st.header("ֱ������")
    st.write("���� Qwen����ģ�͡�������Ϣ���Լ� Deepseek ģ�ͣ�������ֱ���� AI ���жԻ���")
    
    # ѡ������ģʽ������ Qwen������֪ʶ�� (RAG) �� Deepseek ����ѡ��
    chat_mode = st.radio("ѡ������ģʽ", ("Qwen����", "����֪ʶ����(Qwen)", "Deepseek����"))
    
    # Maintain conversation history in session state
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    
    # Chat input form (clears on submit)
    with st.form("chat_form", clear_on_submit=True):
        chat_input = st.text_input("����������Ϣ��")
        submitted = st.form_submit_button("����")
        if submitted and chat_input:
            st.session_state["chat_history"].append({"role": "user", "content": chat_input})
            if chat_mode == "Qwen����":
                reply = chat_with_qwen(chat_input)
            elif chat_mode == "����֪ʶ����(Qwen)":
                reply = chat_with_local_facts(chat_input)
            elif chat_mode == "Deepseek����":
                reply = chat_with_deepseek(chat_input)
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})
    
    st.markdown("### �����¼")
    for message in st.session_state["chat_history"]:
        if message["role"] == "user":
            st.markdown(f"**��:** {message['content']}")
        else:
            st.markdown(f"**AI:** {message['content']}")