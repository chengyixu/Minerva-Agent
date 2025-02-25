import streamlit as st

# 假设这里是你之前定义的 chat 函数
def chat(user_input):
    # 这里简化成一个简单的回显功能，实际中你会根据用户输入返回更复杂的AI响应
    return f"AI Reply:{user_input}"

# 创建聊天输入框
user_input = st.text_input("Ask Anything")

# 如果用户输入了内容
if user_input:
    ai_response = chat(user_input)  # 调用chat函数
    st.write(ai_response)  # 显示AI的回复