import streamlit as st

# ������������֮ǰ����� chat ����
def chat(user_input):
    # ����򻯳�һ���򵥵Ļ��Թ��ܣ�ʵ�����������û����뷵�ظ����ӵ�AI��Ӧ
    return f"AI Reply:{user_input}"

# �������������
user_input = st.text_input("Ask Anything")

# ����û�����������
if user_input:
    ai_response = chat(user_input)  # ����chat����
    st.write(ai_response)  # ��ʾAI�Ļظ�