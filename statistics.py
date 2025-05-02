import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import os
import json
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go

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

def extract_entities_from_history(messages):
    """从聊天历史中提取所有实体"""
    all_entities = []
    for window in messages:
        for message in window:
            if message.get("role") == "assistant" and "ent" in message:
                try:
                    # 将字符串形式的实体字典转换回Python字典
                    ent_str = message["ent"]
                    if ent_str and ent_str != "{}":
                        # 移除可能的前缀和后缀，确保是有效的字典字符串
                        ent_str = ent_str.strip()
                        if ent_str.startswith("{") and ent_str.endswith("}"):
                            # 使用eval安全地将字符串转换为字典
                            entities = eval(ent_str)
                            if isinstance(entities, dict):
                                all_entities.append(entities)
                except Exception as e:
                    st.error(f"解析实体时出错: {e}")
                    continue
    return all_entities

def count_entity_types(entities_list):
    """统计各类实体出现的次数，考虑每种实体类型中包含的实体数量"""
    entity_types_counter = Counter()
    
    for entities in entities_list:
        # 遍历每个实体字典
        for entity_type, entity_value in entities.items():
            # 累加每种实体类型的出现次数
            entity_types_counter[entity_type] += 1
    
    return entity_types_counter

def count_entity_values(entities_list, entity_type):
    """统计特定类型实体的具体值出现次数"""
    values = []
    for entities in entities_list:
        if entity_type in entities:
            values.append(entities[entity_type])
    
    return Counter(values)

def statistics_page(username):
    st.title("医疗问答统计分析")
    
    # 加载用户的聊天历史
    messages = load_chat_history(username)
    
    # 提取所有实体
    entities_list = extract_entities_from_history(messages)
    
    if not entities_list:
        st.warning("没有找到任何实体数据，请先进行一些医疗问答。")
        return
    
    # 统计实体类型分布
    entity_types_count = count_entity_types(entities_list)
    # print(entity_types_count.values(), list(entity_types_count.values()))
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["实体类型分布", "实体详细分析", "问答趋势分析"])
    
    with tab1:
        st.header("实体类型分布")
        
        # 创建饼图
        if entity_types_count:
            # 显示数据表格
            df = pd.DataFrame({
                "实体类型": list(entity_types_count.keys()),
                "出现次数": list(entity_types_count.values())
            })
            st.dataframe(df, use_container_width=True)

            # print(type(df["实体类型"]), df["出现次数"])

            pie_trace = go.Pie(
                labels=df["实体类型"].tolist(),      
                values=df["出现次数"].tolist(),
                marker=dict(
                    colors=px.colors.qualitative.Pastel  # 使用 Pastel 调色板
                ),
                textposition='inside',
                textinfo='percent+label'
            )

            # 构造 Figure 并设置布局
            fig = go.Figure(data=[pie_trace])
            fig.update_layout(
                title="识别的实体类型分布"
            )

            # 在 Streamlit 中渲染
            st.plotly_chart(fig, use_container_width=True)  

        else:
            st.info("暂无实体类型数据")
    
    with tab2:
        st.header("实体详细分析")
        
        # 选择要分析的实体类型
        if entity_types_count:
            selected_entity_type = st.selectbox(
                "选择要分析的实体类型",
                options=list(entity_types_count.keys())
            )
        
        # 统计所选实体类型的具体值分布
        entity_values_count = count_entity_values(entities_list, selected_entity_type)
        
        if entity_values_count:
            # 限制显示前10个最常见的值
            top_values = dict(entity_values_count.most_common(10))
            
            # 准备 x, y 数据
            x_vals = list(top_values.keys())
            y_vals = list(top_values.values())
            
            # 使用 graph_objects 构造条形图
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=x_vals,
                        y=y_vals,
                        marker=dict(
                            color=y_vals,              # 用 y 值来映射颜色
                            colorscale='Viridis'       # Viridis 连续色表
                        )
                    )
                ]
            )
            
            # 更新布局
            fig.update_layout(
                title=f"最常见的{selected_entity_type}实体值",
                xaxis_title=selected_entity_type,
                yaxis_title="出现次数",
                yaxis=dict(
                    type="linear",   # 强制数值型轴
                    dtick=1,         # 刻度间隔为1
                    tickmode="linear",
                    tick0=0
                )
            )
            
            # 渲染到 Streamlit
            st.plotly_chart(fig, use_container_width=True)
                
            # 显示数据表格
            df = pd.DataFrame({
                f"{selected_entity_type}值": list(entity_values_count.keys()),
                "出现次数": list(entity_values_count.values())
            })
            df = df.sort_values("出现次数", ascending=False)
            st.dataframe(df, use_container_width=True)

        else:
            st.info("暂无实体类型数据")
    
    with tab3:
        st.header("问答趋势分析")
        
        # 分析每个对话窗口的问答数量
        # 计算每个窗口中的实际问答对数量（用户提问+助手回答算一次问答）
        window_qa_counts = []
        for window in messages:
            if window:
                # 计算用户消息的数量，每个用户消息对应一次问答
                qa_count = sum(1 for msg in window if msg.get("role") == "user")
                window_qa_counts.append(qa_count)
        
        if window_qa_counts:
            # 创建折线图
            fig = go.Figure(
                go.Scatter(
                    x=[f"对话{i}" for i in range(1, len(window_qa_counts)+1)],
                    y=window_qa_counts,
                    mode='lines+markers'
                )
            )
            fig.update_layout(
                title="各对话窗口问答数量",
                xaxis_title="对话窗口",
                yaxis_title="问答数量",
                yaxis=dict(type="linear", dtick=1, tick0=0)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 计算总问答次数和平均每个窗口的问答次数
            total_qa = sum(window_qa_counts)
            avg_qa = total_qa / len(window_qa_counts) if window_qa_counts else 0
            
            # 显示统计信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总问答次数", total_qa)
            with col2:
                st.metric("对话窗口数", len(window_qa_counts))
            with col3:
                st.metric("平均每窗口问答数", round(avg_qa, 2))
        else:
            st.info("暂无问答数据")

if __name__ == "__main__":
    statistics_page("admin")  # 测试用，实际使用时会传入真实用户名