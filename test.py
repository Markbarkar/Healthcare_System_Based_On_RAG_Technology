# from openai import OpenAI
 
# client = OpenAI(
#     api_key="sk-GOz1Lh7NrLfh6rUlNGXqWZxXySav7JTwHmPrY5KmlA5OldXn",
#     base_url="https://api.moonshot.cn/v1",
# )
 
# completion = client.chat.completions.create(
#     model="moonshot-v1-8k",
#     messages=[
#         {
#             "role": "system",
#             "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"
#         },
#         {
#             "role": "user",
#             "content": "帮我生成一篇关于怎么使用Kimi API接口文档的文章"
#         },
#     ],
#     temperature=0.3,
# )
 
# answer = completion.choices[0].message
 
# print("*" * 30)
# print(answer["content"])

import ollama

response = ollama.chat(
  'deepseek-r1:1.5b',
  messages=[{'role': 'user', 'content': '你好'}],
)

print(response.message.content)