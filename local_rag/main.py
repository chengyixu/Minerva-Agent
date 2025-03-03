from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import gradio as gr
import os
from html_string import main_html,plain_html
from upload_file import *
from create_kb import *
from chat import get_model_response
def user(user_message, history):
    print(user_message)
    return {'text': '','files': user_message['files']}, history + [[user_message['text'], None]]

#####################################
######       gradio界面       #######
#####################################

def get_chat_block():
    with gr.Blocks(theme=gr.themes.Base(),css=".gradio_container { background-color: #f0f0f0; }") as chat:
        gr.HTML(plain_html)
        with gr.Row():     
            with gr.Column(scale=10):
                chatbot = gr.Chatbot(label="Chatbot",height=750,avatar_images=("images/user.jpeg","images/tongyi.png"))
                with gr.Row():
                    # 
                    input_message = gr.MultimodalTextbox(label="请输入",file_types=[".xlsx",".csv",".docx",".pdf",".txt"],scale=7)
                    clear_btn = gr.ClearButton(chatbot,input_message,scale=1)
            # 模型与知识库参数
            with gr.Column(scale=5):
                knowledge_base =gr.Dropdown(choices=os.listdir(DB_PATH),label="加载知识库",interactive=True,scale=2)
                with gr.Accordion(label="召回文本段",open=False):
                    chunk_text = gr.Textbox(label="召回文本段",interactive=False,scale=5,lines=10)
                with gr.Accordion(label="模型设置",open=True):
                    model =gr.Dropdown(choices=['qwen-max','qwen-plus','qwen-turbo'],label="选择模型",interactive=True,value="qwen-max",scale=2)
                    temperature = gr.Slider(maximum=2,minimum=0,interactive=True,label="温度参数",step=0.01,value=0.85,scale=2)
                    max_tokens = gr.Slider(maximum=2000,minimum=0,interactive=True,label="最大回复长度",step=50,value=1024,scale=2)
                    history_round = gr.Slider(maximum=30,minimum=1,interactive=True,label="携带上下文轮数",step=1,value=3,scale=2)
                with gr.Accordion(label="RAG参数设置",open=True):
                    chunk_cnt = gr.Slider(maximum=20,minimum=1,interactive=True,label="选择召回片段数",step=1,value=5,scale=2)
                    similarity_threshold = gr.Slider(maximum=1,minimum=0,interactive=True,label="相似度阈值",step=0.01,value=0.2,scale=2)
        input_message.submit(fn=user,inputs=[input_message,chatbot],outputs=[input_message,chatbot],queue=False).then(
            fn=get_model_response,inputs=[input_message,chatbot,model,temperature,max_tokens,history_round,knowledge_base,similarity_threshold,chunk_cnt],outputs=[chatbot,chunk_text]
            )
        chat.load(update_knowledge_base,[],knowledge_base)
        chat.load(clear_tmp)
    return chat


def get_upload_block():
    with gr.Blocks(theme=gr.themes.Base()) as upload:
        gr.HTML(plain_html)
        with gr.Tab("非结构化数据"):
            with gr.Accordion(label="新建类目",open=True):
                with gr.Column(scale=2):
                    unstructured_file = gr.Files(file_types=["pdf","docx","txt"])
                    with gr.Row():
                        new_label = gr.Textbox(label="类目名称",placeholder="请输入类目名称",scale=5)
                        create_label_btn = gr.Button("新建类目",variant="primary",scale=1)
            with gr.Accordion(label="管理类目",open=False):
                with gr.Row():
                    data_label =gr.Dropdown(choices=os.listdir(UNSTRUCTURED_FILE_PATH),label="管理类目",interactive=True,scale=8,multiselect=True)
                    delete_label_btn = gr.Button("删除类目",variant="stop",scale=1)
        with gr.Tab("结构化数据"):
            with gr.Accordion(label="新建数据表",open=True):
                with gr.Column(scale=2):
                    structured_file = gr.Files(file_types=["xlsx","csv"])
                    with gr.Row():
                        new_label_1 = gr.Textbox(label="数据表名称",placeholder="请输入数据表名称",scale=5)
                        create_label_btn_1 = gr.Button("新建数据表",variant="primary",scale=1)
            with gr.Accordion(label="管理数据表",open=False):
                with gr.Row():
                    data_label_1 =gr.Dropdown(choices=os.listdir(STRUCTURED_FILE_PATH),label="管理数据表",interactive=True,scale=8,multiselect=True)
                    delete_data_table_btn = gr.Button("删除数据表",variant="stop",scale=1)
        delete_label_btn.click(delete_label,inputs=[data_label]).then(fn=update_label,outputs=[data_label])
        create_label_btn.click(fn=upload_unstructured_file,inputs=[unstructured_file,new_label]).then(fn=update_label,outputs=[data_label])
        delete_data_table_btn.click(delete_data_table,inputs=[data_label_1]).then(fn=update_datatable,outputs=[data_label_1])
        create_label_btn_1.click(fn=upload_structured_file,inputs=[structured_file,new_label_1]).then(fn=update_datatable,outputs=[data_label_1])
        upload.load(update_label,[],data_label)
        upload.load(update_datatable,[],data_label_1)
    return upload

def get_knowledge_base_block():
    with gr.Blocks(theme=gr.themes.Base()) as knowledge:
        gr.HTML(plain_html)
        # 非结构化数据知识库
        with gr.Tab("非结构化数据"):
            with gr.Row():
                data_label_2 =gr.Dropdown(choices=os.listdir(UNSTRUCTURED_FILE_PATH),label="选择类目",interactive=True,scale=2,multiselect=True)
                knowledge_base_name = gr.Textbox(label="知识库名称",placeholder="请输入知识库名称",scale=2)
                create_knowledge_base_btn = gr.Button("确认创建知识库",variant="primary",scale=1)
        # 结构化数据知识库
        with gr.Tab("结构化数据"):
            with gr.Row():
                data_label_3 =gr.Dropdown(choices=os.listdir(STRUCTURED_FILE_PATH),label="选择数据表",interactive=True,scale=2,multiselect=True)
                knowledge_base_name_1 = gr.Textbox(label="知识库名称",placeholder="请输入知识库名称",scale=2)
                create_knowledge_base_btn_1 = gr.Button("确认创建知识库",variant="primary",scale=1)
        with gr.Row():
            knowledge_base =gr.Dropdown(choices=os.listdir(DB_PATH),label="管理知识库",interactive=True,scale=4)
            delete_db_btn = gr.Button("删除知识库",variant="stop",scale=1)
        create_knowledge_base_btn.click(fn=create_unstructured_db,inputs=[knowledge_base_name,data_label_2]).then(update_knowledge_base,outputs=[knowledge_base])
        delete_db_btn.click(delete_db,inputs=[knowledge_base]).then(update_knowledge_base,outputs=[knowledge_base])
        create_knowledge_base_btn_1.click(fn=create_structured_db,inputs=[knowledge_base_name_1,data_label_3]).then(update_knowledge_base,outputs=[knowledge_base])
        knowledge.load(update_knowledge_base,[],knowledge_base)
        knowledge.load(update_label,[],data_label_2)
        knowledge.load(update_datatable,[],data_label_3)
    return knowledge

app = FastAPI()
@app.get("/", response_class=HTMLResponse)
def read_main():
    html_content = main_html
    return HTMLResponse(content=html_content)


app = gr.mount_gradio_app(app, get_chat_block(), path="/chat")
app = gr.mount_gradio_app(app, get_upload_block(), path="/upload_data")
app = gr.mount_gradio_app(app, get_knowledge_base_block(), path="/create_knowledge_base")