from zhipuai import ZhipuAI
import streamlit as st
from pathlib import Path
import os
import numpy as np
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from pathlib import Path

api_key="e4ba1f8270cc29fef6fbf1693a4737fd.Cy9L1vRKT6WJ6rId"
base_dir = './面试题'

system_prompt = """# Role: 专业面试官

## Profile
- 资深HR和技术面试官
- 擅长结构化面试和人才评估
- 注重考察候选人的综合素质

## Background
你正在对一位候选人进行面试。你需要基于以下信息进行面试：

候选人的简历：
<简历>
{resume_content}
</简历>

可参考的面试的题库：
<题库>
{context}
</题库>

## Goals
- 全面评估候选人的专业能力和综合素质
- 营造专业友好的面试氛围
- 针对性提出与岗位相关的问题
- 给出客观公正的评价

## Rules
1. 若没有Commands指令，每轮对话仅根据候选人的面试岗位提出一个面试问题，问题要循序渐进，由浅入深；若用户提出Commands指令，则根据指令执行相应操作
2. 注意倾听候选人的回答，保持专业和友好的态度，不泄露题库中的标准答案

## Skills
- 结构化面试技巧
- 考察重点包括：专业能力、学习能力、沟通能力、团队协作等
- 根据候选人的回答灵活调整面试策略

## Workflow
1. 分析候选人简历和求职意向
2. 设计合适的面试问题
3. 评估候选人的回答
4. 适时给出追问或新的话题
5. 在面试过程中持续积累对候选人的评价

## Commands
- 可被执行的指令：
/analyze_resume - 分析候选人简历要点，以hr视角进行点评，并提供改进建议
/next_question - 切换面试知识点，生成以该知识点为主的一个面试问题让候选人进行回答
/technical_test - 开始技术能力测试，每次测试一个技术问题，在候选人给出回答后，给予其本次回答的客观评价
/summary - 生成面试总结报告，提供面试的改进建议
/language - 切换面试交谈的语言，若候选人未指出则默认切换为英文交流

## Constraints
1. 不透露面试评分标准
2. 不对候选人进行人身攻击
3. 不涉及隐私和歧视性问题
4. 保持面试官的专业形象

## Language Style
- 使用礼貌专业的措辞
- 语气平和但不失权威
- 适当使用专业术语
- 表达清晰简洁

请基于以上设定，开始进行面试。"""

def Chat(system_prompt, messages):
    # 初始化智谱AI客户端
    client = ZhipuAI(
        api_key=api_key, 
        base_url="https://open.bigmodel.cn/api/paas/v4/"
    )
    completion = client.chat.completions.create(
        model="glm-4-plus",
        messages=[{"role": "system", "content": system_prompt}] + messages,
        temperature=0.7,
        top_p=0.8,
        max_tokens=2048,
        stream=True
    )
    # 将对话内容写入文件
    with open("测试.txt", "a", encoding="utf-8") as f:
        f.write(str([{"role": "system", "content": system_prompt}] + messages) + "\n")

    return completion

def load_documents(base_dir):
    documents = []
    for file in os.listdir(base_dir):
        file_path = os.path.join(base_dir, file)
        progress_text.text(f"正在处理文件: {file}")
        if file.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())
        elif file.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
            documents.extend(loader.load())
        elif file.endswith('.txt'):
            loader = TextLoader(file_path)
            documents.extend(loader.load())
        progress_text.text(f"文件加载完成")

    return documents

def RAG(query, vectorstore):
    progress_text.text("开始向量检索...")
    # 从向量数据库检索相关内容
    search_result = vectorstore.similarity_search(query, k=10)
    results = {
        "documents": [[doc.page_content for doc in search_result]]
    }
    progress_text.text(f"检索完成！")
    return results

# 初始化向量数据库
def init_vector_store(base_dir):
    progress_text.text("开始Embeddings模型初始化...")
    # 初始化embeddings
    embeddings = OpenAIEmbeddings(
        model="embedding-3",
        openai_api_key=api_key,
        openai_api_base="https://open.bigmodel.cn/api/paas/v4"
    )
    progress_text.text("Embeddings模型初始化成功")
    
    # 加载文档
    documents = load_documents(base_dir)
    
    # 文档分割
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=10)
    chunked_documents = text_splitter.split_documents(documents)
    progress_text.text(f"文档分割完成,共{len(chunked_documents)}个片段")
    
    progress_text.text("开始初始化向量数据库，需要等待一段时间...")
    # 初始化Qdrant向量数据库
    vectorstore = Qdrant.from_documents(
        documents=chunked_documents,
        embedding=embeddings,
        location=":memory:",
        collection_name="interview_qa"
    )
    progress_text.text("向量数据库初始化完成，输入你的求职岗位，开始面试吧！")
    
    return vectorstore

def parse_resume(uploaded_file):
    """解析上传的文件内容"""
    # 创建临时目录来存储上传的文件
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    with open(f"./temp_uploads/{uploaded_file.name}", "wb") as f:
        f.write(uploaded_file.read())
    try:
        # 使用现有的 load_documents 函数加载文件
        documents = load_documents(str(temp_dir))
        # 合并所有文档内容
        resume_content = "\n".join(doc.page_content for doc in documents)
        return resume_content.strip()
    finally:
        # 清理临时文件
        for file in temp_dir.iterdir():
            file.unlink()
        temp_dir.rmdir()

# Streamlit UI
st.title("🤖 面试助手")

# 添加侧边栏说明
with st.sidebar:
    st.markdown("""
    ## 面试助手可用命令说明
    复制以下命令到对话框使用:  
    ### 命令1：`/analyze_resume`
    分析简历要点，给出点评和改进建议，示例: `/analyze_resume`
    ### 命令2：`/next_question` 
    切换面试知识点，生成新的面试问题，示例: `/next_question 机器学习`
    ### 命令3：`/technical_test`
    开始技术能力测试，示例: `/technical_test`
    ### 命令4：`/summary`
    生成面试总结报告，提供改进建议，示例: `/summary`
    ### 命令5：`/language`
    切换面试语言(默认切换为英文)，示例: `/language English`
    """)

# 文件上传
uploaded_file = st.file_uploader("请上传您的简历", type=["pdf", "docx", "txt"])

if uploaded_file:
    progress_text = st.empty()
    progress_text.text(f"收到上传文件: {uploaded_file.name}")

    resume_content = parse_resume(uploaded_file)
    
    # 初始化聊天历史和向量数据库
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.vectorstore = init_vector_store(base_dir)
    
    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 用户输入
    if prompt := st.chat_input("请输入您的回答"):

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.spinner('正在分析您的回答...'):
            # 使用RAG检索相关面试题
            results = RAG(prompt, st.session_state.vectorstore)
            context = "\n".join(results['documents'][0])
            
            # 生成面试官回复
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                completion = Chat(system_prompt.format(resume_content=resume_content, context=context), st.session_state.messages)
                
                for chunk in completion:
                    full_response += chunk.choices[0].delta.content or ""
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

else:
    st.write("请上传您的简历开始面试")