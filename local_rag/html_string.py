main_html = """<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>阿里云本地RAG解决方案</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        header {
            background-color: #2196f3;
            color: white;
            width: 100%;
            padding: 1.5em;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        main {
            margin: 2em;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            width: 90%;
            max-width: 800px;
            padding: 2em;
        }
        h1 {
            color: #333;
        }
        p {
            color: #666;
            font-size: 1.1em;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        ul li {
            background-color: #2196f3;
            margin: 0.5em 0;
            padding: 1em;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        ul li a {
            color: white;
            text-decoration: none;
            display: flex;
            align-items: center;
        }
        ul li:hover {
            background-color: #1976d2;
        }
        .material-icons {
            margin-right: 0.5em;
        }
    </style>
</head>
<body>
    <header>
        <h1>阿里云本地RAG解决方案</h1>
    </header>
    <main>
        <p>如果您需要基于上传的文档与模型直接对话，请直接访问<a href="/chat">RAG问答</a>，并在输入框位置上传文件，就可以开始对话了。（此次上传的数据在页面刷新后无法保留，若您希望可以持久使用、维护知识库，请创建知识库）。</p>
        <p>如果您需要创建或更新知识库，请按照<a href="/upload_data">上传数据</a>、<a href="/create_knowledge_base">创建知识库</a>操作，在<a href="/chat">RAG问答</a>中的“知识库选择”位置选择您需要使用的知识库。</p>
        <p>如果您需要基于已创建好的知识库进行问答，请直接访问<a href="/chat">RAG问答</a>，在“加载知识库”处选择您已创建的知识库。</p>
        <ul>
            <li><a href="/upload_data"><span class="material-icons"></span> 1. 上传数据</a></li>
            <li><a href="/create_knowledge_base"><span class="material-icons"></span> 2. 创建知识库</a></li>
            <li><a href="/chat"><span class="material-icons"></span> 3. RAG问答</a></li>
        </ul>
    </main>
</body>
</html>"""

plain_html = """<!DOCTYPE html>
<html lang="zh">
    <head>
        <title>RAG问答</title>
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
        <style>
        .links-container {
            display: flex;
            justify-content: center; /* 在容器中居中分布子元素 */
            list-style-type: none; /* 去掉ul默认的列表样式 */
            padding: 0; /* 去掉ul默认的内边距 */
            margin: 0; /* 去掉ul默认的外边距 */
        }
        .links-container li {
            margin: 0 5px; /* 每个li元素的左右留出一些空间 */
            padding: 10px 15px; /* 添加内边距 */
            border: 1px solid #ccc; /* 添加边框 */
            border-radius: 5px; /* 添加圆角 */
            background-color: #f9f9f9; /* 背景颜色 */
            transition: background-color 0.3s; /* 背景颜色变化的过渡效果 */
            display: flex; /* 使用flex布局 */
            align-items: center; /* 垂直居中对齐 */
            height: 50px; /* 设置固定高度，确保一致 */
        }
        .links-container li:hover {
            background-color: #e0e0e0; /* 悬停时的背景颜色 */
        }
        .links-container a {
            text-decoration: none !important; /* 去掉链接的下划线 */
            color: #333; /* 链接颜色 */
            font-family: Arial, sans-serif; /* 字体 */
            font-size: 14px; /* 字体大小 */
            display: flex; /* 使用flex布局 */
            align-items: center; /* 垂直居中对齐 */
            height: 100%; /* 确保链接高度与父元素一致 */
        }
        .material-icons {
            font-size: 20px; /* 图标大小 */
            margin-right: 8px; /* 图标和文字间的间距 */
            text-decoration: none; /* 确保图标没有下划线 */
        }

        /* 深色模式样式 */
        @media (prefers-color-scheme: dark) {
            .links-container li {
                background-color: #333; /* 深色模式下的背景颜色 */
                border-color: #555; /* 深色模式下的边框颜色 */
            }
            .links-container li:hover {
                background-color: #555; /* 深色模式下悬停时的背景颜色 */
            }
            .links-container a {
                color: #f9f9f9; /* 深色模式下的文字颜色 */
            }
        }
        </style>
    </head>
    <body>
        <ul class="links-container">
            <li><a href="/"><span class="material-icons">home</span> 主页</a></li>
            <li><a href="/upload_data"><span class="material-icons">cloud_upload</span> 上传数据</a></li>
            <li><a href="/create_knowledge_base"><span class="material-icons">library_add</span> 创建知识库</a></li>
            <li><a href="/chat"><span class="material-icons">question_answer</span> RAG问答</a></li>
        </ul>
    </body>
</html>"""
