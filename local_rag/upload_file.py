#####################################
#######       上传文件         #######
#####################################
import gradio as gr
import os
import shutil
import pandas as pd
STRUCTURED_FILE_PATH = "File/Structured"
UNSTRUCTURED_FILE_PATH = "File/Unstructured"
# 刷新非结构化类目
def refresh_label():
    return os.listdir(UNSTRUCTURED_FILE_PATH)

# 刷新结构化数据表
def refresh_data_table():
    return os.listdir(STRUCTURED_FILE_PATH)

# 上传非结构化数据
def upload_unstructured_file(files,label_name):
    if files is None:
        gr.Info("请上传文件")
    elif len(label_name) == 0:
        gr.Info("请输入类目名称")
    # 判断类目是否存在
    elif label_name in os.listdir(UNSTRUCTURED_FILE_PATH):
        gr.Info(f"{label_name}类目已存在")
    else:
        try:
            if not os.path.exists(os.path.join(UNSTRUCTURED_FILE_PATH,label_name)):
                os.mkdir(os.path.join(UNSTRUCTURED_FILE_PATH,label_name))
            for file in files:
                print(file)
                file_path = file.name
                file_name = os.path.basename(file_path)
                destination_file_path = os.path.join(UNSTRUCTURED_FILE_PATH,label_name,file_name)
                shutil.move(file_path,destination_file_path)
            gr.Info(f"文件已上传至{label_name}类目中，请前往创建知识库")
        except:
            gr.Info(f"请勿重复上传")

# 上传结构化数据
def upload_structured_file(files,label_name):
    if files is None:
        gr.Info("请上传文件")
    elif len(label_name) == 0:
        gr.Info("请输入数据表名称")
    # 判断数据表是否存在
    elif label_name in os.listdir(STRUCTURED_FILE_PATH):
        gr.Info(f"{label_name}数据表已存在")
    else:
        try:
            if not os.path.exists(os.path.join(STRUCTURED_FILE_PATH,label_name)):
                os.mkdir(os.path.join(STRUCTURED_FILE_PATH,label_name))
            for file in files:
                file_path = file.name
                file_name = os.path.basename(file_path)
                destination_file_path = os.path.join(STRUCTURED_FILE_PATH,label_name,file_name)
                shutil.move(file_path,destination_file_path)
                if os.path.splitext(destination_file_path)[1] == ".xlsx":
                    df = pd.read_excel(destination_file_path)
                elif os.path.splitext(destination_file_path)[1] == ".csv":
                    df = pd.read_csv(destination_file_path)
                txt_file_name = os.path.splitext(file_name)[0]+'.txt'
                columns = df.columns
                with open(os.path.join(STRUCTURED_FILE_PATH,label_name,txt_file_name),"w") as file:
                    for idx,row in df.iterrows():
                        file.write("【")
                        info = []
                        for col in columns:
                            info.append(f"{col}:{row[col]}")
                        infos = ",".join(info)
                        file.write(infos)
                        if idx != len(df)-1:
                            file.write("】\n")
                        else:
                            file.write("】")
                os.remove(destination_file_path)
            gr.Info(f"文件已上传至{label_name}数据表中，请前往创建知识库")
        except:
            gr.Info(f"请勿重复上传")

# 实时更新结构化数据表
def update_datatable():
    return gr.update(choices=os.listdir(STRUCTURED_FILE_PATH))


# 实时更新非结构化类目
def update_label():
    return gr.update(choices=os.listdir(UNSTRUCTURED_FILE_PATH))

# 删除类目
def delete_label(label_name):
    if label_name is not None:
        for label in label_name:
            folder_path = os.path.join(UNSTRUCTURED_FILE_PATH,label)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                gr.Info(f"{label}类目已删除")

# 删除数据表
def delete_data_table(table_name):
    if table_name is not None:
        for table in table_name:
            folder_path = os.path.join(STRUCTURED_FILE_PATH,table)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                gr.Info(f"{table}数据表已删除")