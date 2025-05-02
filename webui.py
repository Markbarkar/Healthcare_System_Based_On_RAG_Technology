import os
import streamlit as st
import ner_model as zwk
import pickle
import ollama
from transformers import BertTokenizer
import torch
import py2neo
import random
import re
import ssl
import logging
# 在代码开头添加
logging.getLogger('streamlit').setLevel(logging.ERROR)
import warnings
import streamlit as st
from user_data_storage import credentials, write_credentials, storage_file  # 添加这一行
import qrcode
from io import BytesIO
import base64
# 导入统计模块和用户信息管理模块
from statistics import statistics_page
from user_profile import user_profile_page, admin_user_management_page
# 导入反馈模块
from feedback import submit_feedback_page, user_feedback_history, admin_feedback_management

# 在代码开头添加
warnings.filterwarnings('ignore', category=DeprecationWarning)
# 或者更具体地针对特定警告
warnings.filterwarnings('ignore', message='The use_column_width parameter has been deprecated')
ssl._create_default_https_context = ssl._create_unverified_context
logging.getLogger('streamlit').setLevel(logging.ERROR)
from openai import OpenAI
client_gpt = OpenAI(
    api_key="sk-tAgyaxaD7qG8hRouN9FL6nXFcOEY5iXTCt9doUhqVHGPzUmG",
    base_url="https://api.moonshot.cn/v1",
)

# 设置页面配置
st.set_page_config(
    page_title="医疗问答系统",
    page_icon="🏥",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
    <style>
        /* 主题颜色 */
        :root {
            --primary-color: #2E86C1;
            --secondary-color: #AED6F1;
            --background-color: #F7F9F9;
            --text-color: #2C3E50;
        }
        
        /* 整体背景 */
        .stApp {
            background-color: var(--background-color);
        }
        
        /* 标题样式 */
        .main-title {
            color: var(--primary-color);
            font-size: 2.5rem;
            font-weight: bold;
            text-align: center;
            padding: 1rem;
            margin-bottom: 2rem;
        }
        
        /* 聊天框样式 */
        .chat-container {
            background-image: url('E:\\work\\Neo4j\\RAGQnASystem-main\\RAGQnASystem-main\\img\\logo.jpg'); /* 替换为您的背景图片路径 */
            background-size: cover;
            background-position: center;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        /* 按钮样式 */
        .stButton>button {
            background-color: var(--primary-color);
            color: white;
            border-radius: 5px;
            border: none;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: var(--secondary-color);
            color: var(--text-color);
        }
        
        /* 侧边栏样式 */
        .css-1d391kg {
            background-color: var(--secondary-color);
        }
        
        /* 输入框样式 */
        .stTextInput>div>div>input {
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_model(cache_model):
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    #加载ChatGLM模型
    # glm_tokenizer = AutoTokenizer.from_pretrained("model/chatglm3-6b-128k", trust_remote_code=True)
    # glm_model = AutoModel.from_pretrained("model/chatglm3-6b-128k",trust_remote_code=True,device=device)
    # glm_model.eval()
    glm_model = None
    glm_tokenizer= None
    #加载Bert模型
    with open('tmp_data/tag2idx.npy', 'rb') as f:
        tag2idx = pickle.load(f)
    idx2tag = list(tag2idx)
    rule = zwk.rule_find()
    tfidf_r = zwk.tfidf_alignment()
    model_name = 'model/chinese-roberta-wwm-ext'
    # model_name = r'model/best_roberta_rnn_model_ent_aug' 
    # model_name = r'E:\work\Neo4j\RAGQnASystem-main\RAGQnASystem-main\model\best_roberta_rnn_model_ent_aug.pt'
    bert_tokenizer = BertTokenizer.from_pretrained(model_name)
    bert_model = zwk.Bert_Model(model_name, hidden_size=128, tag_num=len(tag2idx), bi=True)
    bert_model.load_state_dict(torch.load(f'model/{cache_model}.pt', map_location=device))
    # print(f'!!!!!!!!!!!!!!!!model/{cache_model}.pt' )
    
    bert_model = bert_model.to(device)
    bert_model.eval()
    return glm_tokenizer,glm_model,bert_tokenizer,bert_model,idx2tag,rule,tfidf_r,device



def Intent_Recognition(query,choice):
    # 导入数据库操作意图识别模块
    import db_intent
    
    # 首先检查是否是数据库操作意图
    db_operation_intent = db_intent.identify_db_operation_intent(query)
    if db_operation_intent != "none":
        # 如果是数据库操作意图，返回特殊格式的结果
        return {"content": f"DB_OPERATION:{db_operation_intent}"}
    
    # 如果不是数据库操作意图，继续原有的意图识别流程
    prompt = f"""
阅读下列提示，回答问题（问题在输入的最后）:
当你试图识别用户问题中的查询意图时，你需要仔细分析问题，并在16个预定义的查询类别中一一进行判断。对于每一个类别，思考用户的问题是否含有与该类别对应的意图。如果判断用户的问题符合某个特定类别，就将该类别加入到输出列表中。这样的方法要求你对每一个可能的查询意图进行系统性的考虑和评估，确保没有遗漏任何一个可能的分类。

**查询类别**
- "查询疾病简介"
- "查询疾病病因"
- "查询疾病预防措施"
- "查询疾病治疗周期"
- "查询治愈概率"
- "查询疾病易感人群"
- "查询疾病所需药品"
- "查询疾病宜吃食物"
- "查询疾病忌吃食物"
- "查询疾病所需检查项目"
- "查询疾病所属科目"
- "查询疾病的症状"
- "查询疾病的治疗方法"
- "查询疾病的并发疾病"
- "查询药品的生产商"

在处理用户的问题时，请按照以下步骤操作：
- 仔细阅读用户的问题。
- 对照上述查询类别列表，依次考虑每个类别是否与用户问题相关。
- 如果用户问题明确或隐含地包含了某个类别的查询意图，请将该类别的描述添加到输出列表中。
- 确保最终的输出列表包含了所有与用户问题相关的类别描述。

以下是一些含有隐晦性意图的例子，每个例子都采用了输入和输出格式，并包含了对你进行思维链形成的提示：
**示例1：**
输入："睡眠不好，这是为什么？"
输出：["查询疾病简介","查询疾病病因"]  # 这个问题隐含地询问了睡眠不好的病因
**示例2：**
输入："感冒了，怎么办才好？"
输出：["查询疾病简介","查询疾病所需药品", "查询疾病的治疗方法"]  # 用户可能既想知道应该吃哪些药品，也想了解治疗方法
**示例3：**
输入："跑步后膝盖痛，需要吃点什么？"
输出：["查询疾病简介","查询疾病宜吃食物", "查询疾病所需药品"]  # 这个问题可能既询问宜吃的食物，也可能在询问所需药品
**示例4：**
输入："我怎样才能避免冬天的流感和感冒？"
输出：["查询疾病简介","查询疾病预防措施"]  # 询问的是预防措施，但因为提到了两种疾病，这里隐含的是对共同预防措施的询问
**示例5：**
输入："头疼是什么原因，应该怎么办？"
输出：["查询疾病简介","查询疾病病因", "查询疾病的治疗方法"]  # 用户询问的是头疼的病因和治疗方法
**示例6：**
输入："如何知道自己是不是有艾滋病？"
输出：["查询疾病简介","查询疾病所需检查项目","查询疾病病因"]  # 用户想知道自己是不是有艾滋病，一定一定要进行相关检查，这是根本性的！其次是查看疾病的病因，看看自己的行为是不是和病因重合。
**示例7：**
输入："我该怎么知道我自己是否得了21三体综合症呢？"
输出：["查询疾病简介","查询疾病所需检查项目","查询疾病病因"]  # 用户想知道自己是不是有21三体综合症，一定一定要进行相关检查(比如染色体)，这是根本性的！其次是查看疾病的病因。
**示例8：**
输入："感冒了，怎么办？"
输出：["查询疾病简介","查询疾病的治疗方法","查询疾病所需药品","查询疾病所需检查项目","查询疾病宜吃食物"]  # 问怎么办，首选治疗方法。然后是要给用户推荐一些药，最后让他检查一下身体。同时，也推荐一下食物。
**示例9：**
输入："癌症会引发其他疾病吗？"
输出：["查询疾病简介","查询疾病的并发疾病","查询疾病简介"]  # 显然，用户问的是疾病并发疾病， subsequent can give user knowledge about cancer.
**示例10：**
输入："葡萄糖浆的生产者是谁？葡萄糖浆是谁生产的？"
输出：["查询药品的生产商"]  # 显然，用户想要问药品的生产商
通过上述例子，我们希望你能够形成一套系统的思考过程，以准确识别出用户问题中的所有可能查询意图。请仔细分析用户的问题，考虑到其可能的多重含义，确保输出反映了所有相关的查询意图。

**注意：**
- 你的所有输出，都必须在这个范围内上述**查询类别**范围内，不可创造新的名词与类别！
- 参考上述5个示例：在输出查询意图对应的列表之后，请紧跟着用"#"号开始的注释，简短地解释为什么选择这些意图选项。注释应当直接跟在列表后面，形成一条连续的输出。
- 你的输出的类别数量不应该超过5，如果确实有很多个，请你输出最有可能的5个！同时，你的解释不宜过长，但是得富有条理性。

现在，你已经知道如何解决问题了，请你解决下面这个问题并将结果输出！
问题输入："{query}"
输出的时候请确保输出内容都在**查询类别**中出现过。确保输出类别个数**不要超过5个**！确保你的解释和合乎逻辑的！注意，如果用户询问了有关疾病的问题，一般都要先介绍一下疾病，也就是有"查询疾病简介"这个需求。
再次检查你的输出都包含在**查询类别**:"查询疾病简介"、"查询疾病病因"、"查询疾病预防措施"、"查询疾病治疗周期"、"查询治愈概率"、"查询疾病易感人群"、"查询疾病所需药品"、"查询疾病宜吃食物"、"查询疾病忌吃食物"、"查询疾病所需检查项目"、"查询疾病所属科目"、"查询疾病的症状"、"查询疾病的治疗方法"、"查询疾病的并发疾病"、"查询药品的生产商"。
"""
    print(f'prompt:{prompt}')
    # rec_result = ollama.generate(model=choice, prompt=prompt)['response']
    completion = client_gpt.chat.completions.create(
    model="moonshot-v1-8k",
    messages=[
            {
                "role": "system",
                "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0.3,
    )
    
    rec_result = completion.choices[0].message
    # try:
    #     rec_result = ollama.generate(model=choice, prompt=prompt)['response']
    #     from ollama import ResponseError
    # except ResponseError as e:
    #     print(f"Error: {e}")
    #     print(f"Response: {e.response.text}")
    print(f'意图识别结果:{rec_result}')
    # rec_result = '["查询疾病简介","查询疾病的并发疾病"]  # 显然，用户问的是疾病并发疾病， subsequent can give user knowledge about cancer.'
    # print(f'意图识别结果:{rec_result}')
    return rec_result
    # response, _ = glm_model.chat(glm_tokenizer, prompt, history=[])
    # return response


def add_shuxing_prompt(entity,shuxing,client):
    add_prompt = ""
    try:
        sql_q = "match (a:疾病{名称:'%s'}) return a.%s" % (entity,shuxing)
        res = client.run(sql_q).data()[0].values()
        add_prompt+=f"<提示>"
        add_prompt+=f"用户对{entity}可能有查询{shuxing}需求，知识库内容如下："
        if len(res)>0:
            join_res = "".join(res)
            add_prompt+=join_res
        else:
            add_prompt+="图谱中无信息，查找失败。"
        add_prompt+=f"</提示>"
    except:
        pass
    return add_prompt
def add_lianxi_prompt(entity,lianxi,target,client):
    add_prompt = ""
    
    try:
        sql_q = "match (a:疾病{名称:'%s'})-[r:%s]->(b:%s) return b.名称" % (entity,lianxi,target)
        res = client.run(sql_q).data()#[0].values()
        res = [list(data.values())[0] for data in res]
        add_prompt+=f"<提示>"
        add_prompt+=f"用户对{entity}可能有查询{lianxi}需求，知识库内容如下："
        if len(res)>0:
            join_res = "、".join(res)
            add_prompt+=join_res
        else:
            add_prompt+="图谱中无信息，查找失败。"
        add_prompt+=f"</提示>"
    except:
        pass
    return add_prompt
    
def generate_prompt(response,query,client,bert_model, bert_tokenizer,rule, tfidf_r, device, idx2tag):
    entities = zwk.get_ner_result(bert_model, bert_tokenizer, query, rule, tfidf_r, device, idx2tag)
    print(f'意图识别结果:{response}')
    response = response.content if hasattr(response, 'content') else response
    
    print(f'实体识别结果:{entities}')
    yitu = []
    
    # 检查是否是数据库操作意图
    if isinstance(response, dict) and 'content' in response and response['content'].startswith('DB_OPERATION:'):
        # 导入数据库操作模块
        import db_operations, db_intent

        # 确认对象
        types_list = ['药品', '病人', '症状']
        entities_list = []
        for i in types_list:
            if query.find(i) != -1:
                entities_list.append(i)

        entities = db_intent.extract_entity_from_query(query, entities_list)
        print(f'数据库操作实体:{entities}')

        # 解析操作类型
        operation_type = response['content'].split(':')[1].strip()
        
        # 创建Neo4j操作实例
        neo4j_ops = db_operations.Neo4jOperations()
        temp_name = entities.get(entities_list[0]) if entities_list else entities.get('药品', '')
        # 执行数据库操作
        success, message, data = neo4j_ops.execute_operation(operation_type, {
            "node_type": entities_list[0] if entities_list else '药品',
            # "node_id": entities.get(entities_list[0], entities.get('药品', '')) if entities_list else entities.get('药品', ''),
            "properties": {"名称": temp_name},
            "conditions": {k: v for k, v in entities.items() if k not in entities_list}
        })

        print({
            "node_type": entities_list[0] if entities_list else '药品',
            # "node_id": entities.get(entities_list[0], entities.get('药品', '')) if entities_list else entities.get('药品', ''),
            "properties": {"名称": entities.get(entities_list[0], entities.get('药品', ''))},
            "conditions": {k: v for k, v in entities.items() if k not in entities_list}
        })

        # 清空列表
        entities_list = []

        # 构建操作结果提示
        prompt = f"<指令>你是一个医疗问答机器人，现在要求充当信息传递的角色，用户会给出数据库操作的要求，你只需要根据你所知道的信息告知用户数据库操作的结果，包括你获取到的完整的成功或者失败的详细信息。</指令>\n"
        prompt += f"<提示>数据库操作类型：{operation_type}\n操作结果：{'成功' if success else '失败'}\n详细信息：{message}</提示>"

        yitu.append("数据库操作")

        return prompt, yitu, entities
    
    prompt = "<指令>你是一个医疗问答机器人，你需要根据给定的提示回答用户的问题。请注意，你的全部回答必须完全基于给定的提示，不可自由发挥。如果根据提示无法给出答案，立刻回答“根据已知信息无法回答该问题”。</指令>"
    prompt +="<指令>请你仅针对医疗类问题提供简洁和专业的回答。如果问题不是医疗相关的，你一定要回答“我只能回答医疗相关的问题。”，以明确告知你的回答限制。</指令>"
    
    # 预生成相关链接
    links = []
    if '疾病' in entities:
        disease_name = entities['疾病']
        # 添加疾病专属链接
        cdc_link = f"https://www.cdc.gov/search.htm?query={disease_name}"
        links.append(f"【疾病指南】你可以访问[疾病防控中心的相关页面]({cdc_link})了解更多信息。")
        
        # 常见疾病的专门页面映射
        disease_pages = {
            "艾滋病": "https://www.chinaids.org.cn/",
            "糖尿病": "https://www.cdrf.org.cn/",
            "高血压": "https://www.cvd.org.cn/",
            "心脏病": "https://www.heartcare.org.cn/",
            "肺炎": "https://www.chestchina.org/",
            "肝炎": "https://www.hepb.org.cn/",
            "结核病": "https://www.tb.org.cn/",
            "癌症": "https://www.cn-cancer.org/",
            "脑卒中": "https://www.csacn.org/",
            "抑郁症": "https://www.cmha.org.cn/",
        }
        
        # 直接可访问的医学信息页面
        if disease_name in disease_pages:
            specific_link = disease_pages[disease_name]
            links.append(f"【疾病专题】请访问[{disease_name}专题网站]({specific_link})获取详细指南。")
        
        # 使用39健康网的疾病百科页面 - 直接页面而非搜索
        health39_link = f"https://jbk.39.net/jibing_{disease_name}/"
        links.append(f"【疾病百科】[39健康网{disease_name}专题]({health39_link})提供了详细的相关知识。")
        
        # 使用丁香医生疾病百科
        dxy_link = f"https://dxy.com/disease/{disease_name}"
        links.append(f"【医生建议】[丁香医生{disease_name}专区]({dxy_link})有专业医生的诊疗建议。")
    
    elif '疾病症状' in entities:
        symptom = entities['疾病症状']
        # 使用有问必答网的症状页面
        symptom_link = f"https://www.120ask.com/list/symptom/{symptom}"
        links.append(f"【症状解析】查看[{symptom}症状专业解析]({symptom_link})了解可能的疾病。")
    
    elif '药品' in entities:
        drug = entities['药品']
        # 使用用药助手的药品说明书页面
        drug_link = f"https://www.315jiage.cn/x-{drug}/"
        links.append(f"【药品说明】[{drug}药品说明书]({drug_link})包含详细用法用量及注意事项。")
    
    # 随机选择一个链接添加到提示中
    if links:
        link_prompt = random.choice(links)
        prompt += f"<指令>在你的回答结尾，请添加以下专业医疗参考链接：\"{link_prompt}\"</指令>"
    else:
        # 如果没有识别到实体，提供通用医疗资源链接
        general_links = [
            "【健康资讯】更多健康信息请访问[中国疾控中心官网](http://www.chinacdc.cn/)。",
            "【就医指南】需要专业医疗建议请查看[国家卫健委官网](http://www.nhc.gov.cn/)。",
            "【医学科普】了解更多医学知识请访问[丁香园](https://www.dxy.cn/)。"
        ]
        link_prompt = random.choice(general_links)
        prompt += f"<指令>在你的回答结尾，请添加以下专业医疗参考链接：\"{link_prompt}\"</指令>"
    
    if '疾病症状' in entities and  '疾病' not in entities:
        sql_q = "match (a:疾病)-[r:疾病的症状]->(b:疾病症状 {名称:'%s'}) return a.名称" % (entities['疾病症状'])
        res = list(client.run(sql_q).data()[0].values())
        # print('res=',res)
        if len(res)>0:
            entities['疾病'] = random.choice(res)
            all_en = "、".join(res)
            prompt+=f"<提示>用户有{entities['疾病症状']}的情况，知识库推测其可能是得了{all_en}。请注意这只是一个推测，你需要明确告知用户这一点。</提示>"
    pre_len = len(prompt)
    if "简介" in response:
        if '疾病' in entities:
            prompt+=add_shuxing_prompt(entities['疾病'],'疾病简介',client)
            yitu.append('查询疾病简介')
    if "病因" in response:
        if '疾病' in entities:
            prompt+=add_shuxing_prompt(entities['疾病'],'疾病病因',client)
            yitu.append('查询疾病病因')
    if "预防" in response:
        if '疾病' in entities:
            prompt+=add_shuxing_prompt(entities['疾病'],'预防措施',client)
            yitu.append('查询预防措施')
    if "治疗周期" in response:
        if '疾病' in entities:
            prompt+=add_shuxing_prompt(entities['疾病'],'治疗周期',client)
            yitu.append('查询治疗周期')
    if "治愈概率" in response:
        if '疾病' in entities:
            prompt+=add_shuxing_prompt(entities['疾病'],'治愈概率',client)
            yitu.append('查询治愈概率')
    if "易感人群" in response:
        if '疾病' in entities:
            prompt+=add_shuxing_prompt(entities['疾病'],'疾病易感人群',client)
            yitu.append('查询疾病易感人群')
    if "药品" in response:
        if '疾病' in entities:
            prompt+=add_lianxi_prompt(entities['疾病'],'疾病使用药品','药品',client)
            yitu.append('查询疾病使用药品')
    if "宜吃食物" in response:
        if '疾病' in entities:
            prompt+=add_lianxi_prompt(entities['疾病'],'疾病宜吃食物','食物',client)
            yitu.append('查询疾病宜吃食物')
    if "忌吃食物" in response:
        if '疾病' in entities:
            prompt+=add_lianxi_prompt(entities['疾病'],'疾病忌吃食物','食物',client)
            yitu.append('查询疾病忌吃食物')
    if "检查项目" in response:
        if '疾病' in entities:
            prompt+=add_lianxi_prompt(entities['疾病'],'疾病所需检查','检查项目',client)
            yitu.append('查询疾病所需检查')
    if "查询疾病所属科目" in response:
        if '疾病' in entities:
            prompt+=add_lianxi_prompt(entities['疾病'],'疾病所属科目','科目',client)
            yitu.append('查询疾病所属科目')
    # if "所属科目" in response:
    #     if '疾病' in entities:
    #         prompt+=add_lianxi_prompt(entities['疾病'],'疾病所属科目','科目')
    #         yitu.append('查询疾病所属科目')
    if "症状" in response:
        if '疾病' in entities:
            prompt+=add_lianxi_prompt(entities['疾病'],'疾病的症状','疾病症状',client)
            yitu.append('查询疾病的症状')
    if "治疗" in response:
        if '疾病' in entities:
            prompt+=add_lianxi_prompt(entities['疾病'],'治疗的方法','治疗方法',client)
            yitu.append('查询治疗的方法')
    if "并发" in response:
        if '疾病' in entities:
            prompt+=add_lianxi_prompt(entities['疾病'],'疾病并发疾病','疾病',client)
            yitu.append('查询疾病并发疾病')
    if "生产商" in response:
        try:
            sql_q = "match (a:药品商)-[r:生产]->(b:药品{名称:'%s'}) return a.名称" % (entities['药品'])
            res = client.run(sql_q).data()[0].values()
            prompt+=f"<提示>"
            prompt+=f"用户对{entities['药品']}可能有查询药品生产商的需求，知识图谱内容如下："
            if len(res)>0:
                prompt+="".join(res)
            else:
                prompt+="图谱中无信息，查找失败"
            prompt+=f"</提示>"
        except:
            pass
        yitu.append('查询药物生产商')
    if pre_len==len(prompt) :
        prompt += f"<提示>提示：知识库异常，没有相关信息！请你直接回答“根据已知信息无法回答该问题”！</提示>"
    prompt += f"<用户问题>{query}</用户问题>"
    prompt += f"<注意>现在你已经知道给定的“<提示></提示>”和“<用户问题></用户问题>”了,你要极其认真的判断提示里是否有用户问题所需的信息，如果没有相关信息，你必须直接回答“根据已知信息无法回答该问题”。</注意>"

    prompt += f"<注意>你一定要再次检查你的回答是否完全基于“<提示></提示>”的内容，不可产生提示之外的答案！换而言之，你的任务是根据用户的问题，将“<提示></提示>”整理成有条理、有逻辑的语句。你起到的作用仅仅是整合提示的功能，你一定不可以利用自身已经存在的知识进行回答，你必须从提示中找到问题的答案！</注意>"
    # prompt += f"<注意>你必须自由的利用提示中的知识，不可将提示中的任何信息遗漏，你必须做到对提示信息的充分整合。你回答的任何一句话必须在提示中有所体现！如果根据提示无法给出答案，你必须回答“根据已知信息无法回答该问题”。<注意>"
    
    
    print(f'prompt:{prompt}')
    return prompt, "、".join(yitu), entities



def ans_stream(prompt):
    
    result = ""
    for res,his in glm_model.stream_chat(glm_tokenizer, prompt, history=[]):
        yield res


def show_user_management(credentials):
    """显示用户管理界面"""
    st.title("用户管理")
    
    # 创建一个表格显示所有用户信息
    users_data = []
    for username, user_cred in credentials.items():
        user_info = {
            "用户名": username,
            "权限设置": {
                "实体识别结果": user_cred.show_ent,
                "意图识别结果": user_cred.show_int,
                "知识库信息": user_cred.show_prompt
            }
        }
        users_data.append(user_info)
    
    # 为每个用户创建一个展开部分
    for user in users_data:
        with st.expander(f"用户: {user['用户名']}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            # 在每个列中显示对应的权限设置
            with col1:
                new_ent = st.checkbox(
                    "实体识别结果",
                    value=user["权限设置"]["实体识别结果"],
                    key=f"ent_{user['用户名']}"
                )
            
            with col2:
                new_int = st.checkbox(
                    "意图识别结果",
                    value=user["权限设置"]["意图识别结果"],
                    key=f"int_{user['用户名']}"
                )
            
            with col3:
                new_prompt = st.checkbox(
                    "知识库信息",
                    value=user["权限设置"]["知识库信息"],
                    key=f"prompt_{user['用户名']}"
                )
            
            # 如果权限被修改，更新用户权限
            if (new_ent != user["权限设置"]["实体识别结果"] or
                new_int != user["权限设置"]["意图识别结果"] or
                new_prompt != user["权限设置"]["知识库信息"]):
                
                credentials[user['用户名']].show_ent = new_ent
                credentials[user['用户名']].show_int = new_int
                credentials[user['用户名']].show_prompt = new_prompt
                write_credentials(storage_file, credentials)
                st.success(f"已更新 {user['用户名']} 的权限设置")

def generate_qr_code():
    """生成模拟支付的二维码"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 提高纠错级别
        box_size=10,
        border=4,
    )
    # 使用微信可识别的URL格式，这里使用微信官方网站作为示例
    qr.add_data("https://weixin.qq.com/")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def main(is_admin, usname):
    cache_model = 'best_roberta_rnn_model_ent_aug'
    
    # 初始化会话状态
    if 'show_user_management' not in st.session_state:
        st.session_state.show_user_management = False
    
    # 初始化统计页面状态
    if 'show_statistics' not in st.session_state:
        st.session_state.show_statistics = False
    
    # 初始化用户信息管理状态
    if 'show_user_profile' not in st.session_state:
        st.session_state.show_user_profile = False
        
    # 初始化反馈页面状态
    if 'show_feedback' not in st.session_state:
        st.session_state.show_feedback = False
        
    # 初始化管理员反馈管理页面状态
    if 'show_admin_feedback' not in st.session_state:
        st.session_state.show_admin_feedback = False
    
    # 初始化或加载聊天记录
    if 'chat_windows' not in st.session_state:
        # 从文件加载历史记录
        st.session_state.chat_windows = load_chat_history(usname)
        st.session_state.messages = st.session_state.chat_windows
    
    # 初始化模拟支付状态
    if 'show_payment' not in st.session_state:
        st.session_state.show_payment = False
    
    # 如果是管理员且点击了用户管理按钮，显示用户管理界面
    if is_admin and st.session_state.show_user_management:
        admin_user_management_page()
        if st.button("返回聊天"):
            st.session_state.show_user_management = False
            st.rerun()
    # 如果是管理员且点击了反馈管理按钮，显示反馈管理界面
    elif is_admin and st.session_state.show_admin_feedback:
        admin_feedback_management()
        if st.button("返回聊天", key="return_from_admin_feedback"):
            st.session_state.show_admin_feedback = False
            st.rerun()
    # 如果显示用户反馈页面
    elif st.session_state.show_feedback:
        submit_feedback_page(usname)
        # 显示用户的反馈历史
        user_feedback_history(usname)
        if st.button("返回聊天", key="return_from_feedback"):
            st.session_state.show_feedback = False
            st.rerun()
    # 如果显示用户信息管理页面
    elif st.session_state.show_user_profile:
        user_profile_page(usname, is_admin)
        if st.button("返回聊天", key="return_from_profile"):
            st.session_state.show_user_profile = False
            st.rerun()
    # 如果显示统计页面，展示统计分析
    elif st.session_state.show_statistics:
        statistics_page(usname)
        if st.button("返回聊天", key="return_from_stats"):
            st.session_state.show_statistics = False
            st.rerun()
    # 如果显示支付界面，展示模拟支付页面
    elif st.session_state.show_payment:
        st.title("模拟支付")
        
        # 生成并显示二维码
        qr_code = generate_qr_code()
        st.markdown(f"""
            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; background-color: #f8f8f8; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
                <h2 style='color: #07C160; margin-bottom: 15px;'>微信扫码支付</h2>
                <div style='background-color: white; padding: 15px; border-radius: 8px;'>
                    <img src='data:image/png;base64,{qr_code}' alt='支付二维码' style='width: 200px; height: 200px;'>
                </div>
                <div style='margin-top: 15px; text-align: center;'>
                    <p style='color: #333; font-size: 16px;'>请使用微信扫描上方二维码进行支付</p>
                    <p style='color: #333; font-size: 14px;'>支付成功后，您将获得5次额外的问答机会</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 模拟支付完成按钮
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("我已完成支付", key="payment_complete"):
                # 增加用户的问答次数
                credentials[usname].question_count += 5
                write_credentials(storage_file, credentials)
                
                # 返回聊天界面
                st.session_state.show_payment = False
                st.success("支付成功！您已获得5次额外问答机会")
                st.rerun()
        
        # 返回按钮
        with col2:
            if st.button("返回聊天", key="payment_cancel"):
                st.session_state.show_payment = False
                st.rerun()
    else:
        st.title(f"医疗智能问答机器人")
        
        with st.sidebar:
            col1, col2 = st.columns([0.6, 0.6])
            with col1:
                st.image(os.path.join("img", "logo.jpg"))
            
            st.caption(
                f"""<p align="left">欢迎您，{'管理员' if is_admin else '用户'}{usname}！当前版本：{1.0}</p>""",
                unsafe_allow_html=True,
            )
            
            # 显示剩余问答次数
            st.info(f"剩余问答次数: {credentials[usname].question_count}")
            
            # 添加充值按钮
            if st.button("充值问答次数"):
                st.session_state.show_payment = True
                st.rerun()
                
            # 添加个人信息按钮
            if st.button("设置"):
                st.session_state.show_user_profile = True
                st.rerun()
            
            # 修改这部分代码，让普通用户也能看到已获得权限的按钮
            show_ent = show_int = show_prompt = False
            
            # 获取当前用户的权限设置
            current_user = credentials.get(usname)
            
            # 根据用户权限显示按钮
            if is_admin:
                # 管理员可以看到所有复选框
                show_ent = st.sidebar.checkbox("显示实体识别结果")
                show_int = st.sidebar.checkbox("显示意图识别结果")
                show_prompt = st.sidebar.checkbox("显示查询的知识库信息")
                
                # 管理员特有功能
                st.markdown("### 管理员功能")
                # if st.button("用户管理"):
                #     st.session_state.show_user_management = True
                #     st.rerun()
                
                if st.button('修改知识图谱'):
                    st.markdown('[点击这里修改知识图谱](http://127.0.0.1:7474/)', unsafe_allow_html=True)
                    
                # 添加管理员查看反馈的按钮
                if st.button('查看用户反馈'):
                    st.session_state.show_admin_feedback = True
                    st.rerun()
            else:
                # 普通用户根据权限显示按钮
                if current_user.show_ent:
                    show_ent = st.sidebar.checkbox("显示实体识别结果")
                if current_user.show_int:
                    show_int = st.sidebar.checkbox("显示意图识别结果")
                if current_user.show_prompt:
                    show_prompt = st.sidebar.checkbox("显示查询的知识库信息")

            if st.button('新建对话窗口'):                
                st.session_state.chat_windows.append([])
                st.session_state.messages.append([])
                # 保存更新后的聊天记录
                save_chat_history(usname, st.session_state.messages)
            
            # 添加统计按钮 - 仅管理员可见
            if is_admin and st.button('查看统计分析'):
                st.session_state.show_statistics = True
                st.rerun()
                
            # 添加反馈按钮 - 仅普通用户可见
            if not is_admin and st.button('提交反馈'):
                st.session_state.show_feedback = True
                st.rerun()
                
            # 添加数据库操作说明
            st.sidebar.markdown("""
            ### 使用说明
            1. 输入您的医疗问题
            2. 系统会自动识别相关疾病和症状
            3. 获取专业的医疗建议
            
            ### 数据库操作
            您还可以通过对话进行Neo4j数据库的增删改查操作：
            - 添加药品信息：例如"添加药品阿斯匹林"
            - 修改药品信息：例如"将药品阿斯匹林修改为舒心健腰丸"
            - 删除药品信息：例如"删除药品阿司匹林"
            - 查询药品信息：例如"查询药品阿斯匹林"
            
            **注意：** 本系统仅提供参考，请遵医嘱进行治疗。
            """)

            window_options = [f"对话窗口 {i + 1}" for i in range(len(st.session_state.chat_windows))]
            selected_window = st.selectbox('请选择对话窗口:', window_options)
            active_window_index = int(selected_window.split()[1]) - 1

            selected_option = st.selectbox(
                label='请选择大语言模型:',
                options=['deepseek']
            )
            choice = 'qwen:32b' if selected_option == 'Qwen 1.5' else 'llama2-chinese:13b-chat-q8_0'

            if st.button("返回登录"):
                st.session_state.logged_in = False
                st.session_state.admin = False
                st.rerun()

        glm_tokenizer, glm_model, bert_tokenizer, bert_model, idx2tag, rule, tfidf_r, device = load_model(cache_model)
        client = py2neo.Graph('bolt:http://localhost:7474', user='neo4j', password='123456789', name='neo4j')

        current_messages = st.session_state.messages[active_window_index]

        for message in current_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant":
                    if show_ent:
                        with st.expander("实体识别结果"):
                            st.write(message.get("ent", ""))
                    if show_int:
                        with st.expander("意图识别结果"):
                            st.write(message.get("yitu", ""))
                    if show_prompt:
                        with st.expander("点击显示知识库信息"):
                            st.write(message.get("prompt", ""))

        if query := st.chat_input("Ask me anything!", key=f"chat_input_{active_window_index}"):
            # 检查用户是否有足够的问答次数
            if credentials[usname].question_count <= 0 and not is_admin:
                st.warning("您的问答次数已用完，请充值后继续使用")
                st.session_state.show_payment = True
                st.rerun()
            
            # 非管理员用户每次提问都会消耗一次问答次数
            if not is_admin:
                credentials[usname].question_count -= 1
                write_credentials(storage_file, credentials)
            
            current_messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)

            response_placeholder = st.empty()
            response_placeholder.text("正在进行意图识别...")

            query = current_messages[-1]["content"]
            print(f'意图识别query:{query}')
            response = Intent_Recognition(query, choice)
            response_placeholder.empty()

            prompt, yitu, entities = generate_prompt(response, query, client, bert_model, bert_tokenizer, rule, tfidf_r, device, idx2tag)

            last = ""

            

            # for chunk in client_gpt.chat.completions.create(
            #     model="moonshot-v1-8k",
            #     messages=[
            #         {
            #             "role": "system",
            #             "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"
            #         },
            #         {
            #             "role": "user",
            #             "content": prompt
            #         }
            #     ],
            #     temperature=0.3,
            #     stream=True  # 启用流式输出
            # ):
            #     content = chunk.choices[0].delta.content
            #     print(content)
            #     if content is not None:
            #         last += content
            #         response_placeholder.markdown(last)
            for chunk in ollama.chat(
                        model='deepseek-r1:1.5b', 
                        messages=[{'role': 'user', 'content': prompt}], 
                        stream=True
                    ):
                content = chunk['message']['content']
                if content is not None:
                    last += content
                    response_placeholder.markdown(last)
            response_placeholder.markdown("")
            # 提取知识库信息
            knowledge = re.findall(r'<提示>(.*?)</提示>', prompt)
            zhishiku_content = "\n".join([f"提示{idx + 1}, {kn}" for idx, kn in enumerate(knowledge) if len(kn) >= 3])
            
            with st.chat_message("assistant"):
                st.markdown(last)
                if show_ent:
                    with st.expander("实体识别结果"):
                        st.write(str(entities))
                if show_int:
                    with st.expander("意图识别结果"):
                        st.write(yitu)
                if show_prompt:
                    with st.expander("点击显示知识库信息"):
                        st.write(zhishiku_content)
            current_messages.append({"role": "assistant", "content": last, "yitu": yitu, "prompt": zhishiku_content, "ent": str(entities)})


        st.session_state.messages[active_window_index] = current_messages

        # 保存更新后的聊天记录
        save_chat_history(usname, st.session_state.messages)

def save_chat_history(username, messages):
    """保存用户的聊天记录到文件"""
    history_dir = 'chat_history'
    if not os.path.exists(history_dir):
        os.makedirs(history_dir)
    
    history_file = os.path.join(history_dir, f'{username}_history.pkl')
    with open(history_file, 'wb') as f:
        pickle.dump(messages, f)

def load_chat_history(username):
    """加载用户的聊天记录"""
    history_file = os.path.join('chat_history', f'{username}_history.pkl')
    if os.path.exists(history_file):
        try:
            with open(history_file, 'rb') as f:
                return pickle.load(f)
        except:
            return [[]]  # 如果加载失败，返回空的聊天窗口
    return [[]]  # 如果没有历史记录，返回空的聊天窗口
