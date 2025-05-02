import streamlit as st
import os
import json
import datetime
from user_data_storage import credentials, create_folder_if_not_exist

# 反馈数据存储路径
feedback_folder = "tmp_data"
feedback_file = os.path.join(feedback_folder, "user_feedback.json")

# 确保文件夹存在
create_folder_if_not_exist(feedback_folder)

def load_feedback():
    """加载所有用户反馈"""
    try:
        with open(feedback_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_feedback(feedback_list):
    """保存用户反馈"""
    with open(feedback_file, "w", encoding="utf-8") as file:
        json.dump(feedback_list, file, ensure_ascii=False, indent=4)

def submit_feedback_page(username):
    """用户提交反馈页面"""
    st.title("向管理员提交反馈")
    
    # 创建反馈表单
    with st.form("feedback_form"):
        # 反馈类型选择
        feedback_type = st.selectbox(
            "反馈类型",
            options=["功能建议", "问题报告", "内容纠错", "其他"]
        )
        
        # 反馈标题
        feedback_title = st.text_input("反馈标题", max_chars=50)
        
        # 反馈内容
        feedback_content = st.text_area("反馈内容", height=150, max_chars=500)
        
        # 紧急程度
        urgency = st.select_slider(
            "紧急程度",
            options=["低", "中", "高"]
        )
        
        # 提交按钮
        submit_button = st.form_submit_button("提交反馈")
        
        if submit_button:
            if not feedback_title or not feedback_content:
                st.error("请填写反馈标题和内容")
            else:
                # 加载现有反馈
                feedback_list = load_feedback()
                
                # 创建新的反馈
                new_feedback = {
                    "id": len(feedback_list) + 1,
                    "username": username,
                    "type": feedback_type,
                    "title": feedback_title,
                    "content": feedback_content,
                    "urgency": urgency,
                    "status": "待处理",
                    "submit_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "response": "",
                    "response_time": ""
                }
                
                # 添加到反馈列表
                feedback_list.append(new_feedback)
                
                # 保存反馈
                save_feedback(feedback_list)
                
                st.success("反馈提交成功！管理员将尽快处理您的反馈。")
                
                # 清空表单
                st.rerun()

def user_feedback_history(username):
    """用户查看自己的反馈历史"""
    st.subheader("我的反馈历史")
    
    # 加载所有反馈
    all_feedback = load_feedback()
    
    # 筛选当前用户的反馈
    user_feedback = [f for f in all_feedback if f["username"] == username]
    
    if not user_feedback:
        st.info("您还没有提交过反馈")
        return
    
    # 按提交时间倒序排序
    user_feedback.sort(key=lambda x: x["submit_time"], reverse=True)
    
    # 显示反馈历史
    for feedback in user_feedback:
        with st.expander(f"#{feedback['id']} - {feedback['title']} ({feedback['status']})", expanded=False):
            st.markdown(f"**类型**: {feedback['type']}")
            st.markdown(f"**提交时间**: {feedback['submit_time']}")
            st.markdown(f"**紧急程度**: {feedback['urgency']}")
            st.markdown(f"**内容**: {feedback['content']}")
            st.markdown(f"**状态**: {feedback['status']}")
            
            if feedback["response"]:
                st.markdown("---")
                st.markdown(f"**管理员回复**: {feedback['response']}")
                st.markdown(f"**回复时间**: {feedback['response_time']}")

def admin_feedback_management():
    """管理员反馈管理页面"""
    st.title("用户反馈管理")
    
    # 加载所有反馈
    all_feedback = load_feedback()
    
    if not all_feedback:
        st.info("目前没有收到任何用户反馈")
        return
    
    # 按状态和提交时间排序
    all_feedback.sort(key=lambda x: (0 if x["status"] == "待处理" else 1, x["submit_time"]), reverse=True)
    
    # 创建状态过滤器
    status_filter = st.multiselect(
        "按状态筛选",
        options=["待处理", "处理中", "已解决", "已关闭"],
        default=["待处理"]
    )
    
    # 筛选反馈
    if status_filter:
        filtered_feedback = [f for f in all_feedback if f["status"] in status_filter]
    else:
        filtered_feedback = all_feedback
    
    # 显示反馈数量统计
    st.markdown(f"共有 **{len(filtered_feedback)}** 条符合条件的反馈")
    
    # 显示反馈列表
    for feedback in filtered_feedback:
        with st.expander(f"#{feedback['id']} - {feedback['title']} ({feedback['status']}) - 用户: {feedback['username']}", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**类型**: {feedback['type']}")
            with col2:
                st.markdown(f"**提交时间**: {feedback['submit_time']}")
            with col3:
                st.markdown(f"**紧急程度**: {feedback['urgency']}")
            
            st.markdown(f"**内容**: {feedback['content']}")
            
            # 更新状态
            new_status = st.selectbox(
                "更新状态",
                options=["待处理", "处理中", "已解决", "已关闭"],
                index=["待处理", "处理中", "已解决", "已关闭"].index(feedback["status"]),
                key=f"status_{feedback['id']}"
            )
            
            # 管理员回复
            admin_response = st.text_area(
                "回复用户",
                value=feedback["response"],
                height=100,
                key=f"response_{feedback['id']}"
            )
            
            # 更新按钮
            if st.button("更新反馈", key=f"update_{feedback['id']}"):
                # 更新反馈状态和回复
                for f in all_feedback:
                    if f["id"] == feedback["id"]:
                        f["status"] = new_status
                        f["response"] = admin_response
                        if admin_response and admin_response != feedback["response"]:
                            f["response_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        break
                
                # 保存更新
                save_feedback(all_feedback)
                st.success("反馈已更新")
                st.rerun()