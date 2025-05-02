首先启动neo4j
https://blog.csdn.net/weixin_51998255/article/details/141559877
运行
streamlit run login.py
     // 查询所有节点和关系
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100
          // 查询所有疾病节点
MATCH (d:疾病) RETURN d LIMIT 50

     // 查询特定疾病及其相关的药品
MATCH (d:疾病 {名称: "感冒"})-[:疾病使用药品]->(p:药品) RETURN d, p



问题1 
得了胃癌就一定会死么
问题 2 
感冒多久可以好
问题3
艾滋病在饮食方面要注意什么？
问题4
我腿骨折了，该去医院哪个部门看？


报错：
RateLimitError: Error code: 429 - {'error': {'message': 'Your account csjpq7egi3puohstuu00<ak-ey8hs8bds7ei11fmwipi> request reached max request: 3, please try again after 1 seconds', 'type': 'rate_limit_reached_error'}}
这个问题是因为不能短时间内连续问，因为使用的是免费的在线模型。