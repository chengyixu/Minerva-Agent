==**Local Agent阶段：**==
**LLM模型：Qwen系列 - 根据API用量付费**, Deepseek系列
1. 根据输出质量决定是否需要后续rl以及ft

**部署位置：
1. 云存储：NAS - 冰鲸科技私有云
2. 网页端：
	1. 暂定Streamlit，后续根据实现难度可调整为gradio等
	2. openweb-ui

**功能实现：**
1. 监控推流的各大信息网站的热点
2. 定时整合汇报各大信息网站的重要内容
3. 作为本地的事实知识库，可以随时添加各种类型的信息源，并支持可验证的cross check，
	1. 回答的时候同时展示信息源片段
	2. 可以选择对某个标签问答，比如（问xxx项目的信息）
	3. 对话
	4. 验证
	5. 搜索整理

事实库信息源写入 - 判断格式和形式 - 
					PDF -           读取并保存
					网站              爬取并保存 - 先用request，如果不行再用apify
					微信公众号   爬取并保存
					twitter账号   apify


读取进度条
					

**信源来源与爬取方式：**
1. X - apify
2. 微信公众号 - request
3. 常规网站爬取 - Jina ai，根据API用量或需要付费
4. 博客与论文 - 免费

用Swanlab监控
jina

==**Workflow Agent阶段：**==
1. 公司内部ERP整合（飞书，Notion等）作为企业级资源管理与规划平台
2. 公司Workflow整合（项目全生命周期）


监控

手动保存到rag：网页，文件，图片，语音

对rag进行chat

账号密码
分区
文章梗概+链接
设置关注词“AI，
进度条
限制时间
总结成1页
各网站详情
general爬虫 = firecrawl
arxiv爬虫
x 爬虫
general爬虫
csdn

fact-check模式，先物理搜索定位

  

https://barretzoph.github.io/

http://joschu.net/blog.html

https://www.csdn.net/?spm=1001.2101.3001.4476

### Follow articles written by
### [Jason Wei](https://scholar.google.com/citations?hl=en&user=wA5TK_0AAAAJ)

OpenAI
### [Niklas Muennighoff](https://scholar.google.com/citations?hl=en&user=Me0IoRMAAAAJ)

Stanford University
### [Naman Goyal](https://scholar.google.com/citations?hl=en&user=CRbM_P4AAAAJ)

Facebook AI Research
### [Thomas Wolf](https://scholar.google.com/citations?hl=en&user=D2H5EFEAAAAJ)

Co-founder at HuggingFace
### [Denny Zhou](https://scholar.google.com/citations?hl=en&user=UwLsYw8AAAAJ)

Research Scientist, Google DeepMind



1. 监控汇报：热度高于某个值，就汇报提醒(twitter很好做，爬下来的都)
2. 定时汇报：每天早上9点半和下午5点做个信息总结
3. 事实知识库：可以自行添加公众号/网站/x账号/pdf/文本/语音/图片，保存在本地
	1. 可以分类提问，只提问某个项目/只提问某个类型
4. 直接聊天，直接于deepseek或者qwen聊天

sft，rl
在本地跑一个7b适合吗+RL
还是直接qwen+rag
或者distill一个小模型0.5B，李飞飞那种

效果怎么保证？

基于streamlit还是什么gradio甚至是直接coze，dify这种哪种平台更好
怎么存储数据最好，batch json还是sql还是csv这种，
scrape爬取阶段怎么提升速度？

确定这是事实
chat to PDF，就是问问题的时候同时把原文列出来，
用python包列出来所有信息，然后再针对这些信息进行提问，
	是作为一个单独的rag好，还是直接在prompt里好呢

- top K，低创意，高具体
- top P，高创意，
- Temperature

提醒到微信里，或者提醒到飞书里？

你们对于
有啥要问我的吗，面对我这种个人或者smb开发者，可能是未来开放agent最多的那批人


分trunk
qwen - embedding

一个文，只输入文本

您对agent，返回的有用性，

Openweb UI
jina ai