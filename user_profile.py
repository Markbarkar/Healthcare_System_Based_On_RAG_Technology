import streamlit as st
import os
from user_data_storage import credentials, write_credentials, storage_file, Credentials

def user_profile_page(username, is_admin=False):
    """用户信息修改页面"""
    st.title("用户信息管理")
    
    # 获取当前用户信息
    current_user = credentials.get(username)
    if not current_user:
        st.error("无法获取用户信息")
        return
    
    # 创建两个标签页：个人信息和密码修改
    tab1, tab2 = st.tabs(["个人信息", "密码修改"])
    
    with tab1:
        st.header("个人信息")
        
        # 显示用户基本信息
        st.write(f"**用户名**: {current_user.username}")
        st.write(f"**账户类型**: {'管理员' if current_user.is_admin else '普通用户'}")
        st.write(f"**剩余问答次数**: {current_user.question_count}")
        
        # 显示权限信息
        st.subheader("权限设置")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**显示实体识别结果**: {'是' if current_user.show_ent else '否'}")
        with col2:
            st.write(f"**显示意图识别结果**: {'是' if current_user.show_int else '否'}")
        with col3:
            st.write(f"**显示知识库信息**: {'是' if current_user.show_prompt else '否'}")
        
        # 如果是管理员，显示用户管理入口
        if is_admin:
            st.subheader("管理员功能")
            if st.button("进入用户管理"):
                st.session_state.show_user_management = True
                st.rerun()
    
    with tab2:
        st.header("密码修改")
        
        # 密码修改表单
        with st.form("password_change_form"):
            current_password = st.text_input("当前密码", type="password")
            new_password = st.text_input("新密码", type="password")
            confirm_password = st.text_input("确认新密码", type="password")
            
            submit_button = st.form_submit_button("修改密码")
            
            if submit_button:
                # 验证当前密码
                if current_password != current_user.password:
                    st.error("当前密码不正确")
                # 验证新密码
                elif new_password != confirm_password:
                    st.error("两次输入的新密码不一致")
                elif not new_password:
                    st.error("新密码不能为空")
                else:
                    # 更新密码
                    current_user.password = new_password
                    write_credentials(storage_file, credentials)
                    st.success("密码修改成功")

def admin_user_management_page():
    """管理员用户管理页面"""
    st.title("用户管理")
    
    # 创建两个标签页：用户列表和添加用户
    tab1, tab2 = st.tabs(["用户列表", "添加用户"])
    
    with tab1:
        st.header("用户列表")
        
        # 创建一个表格显示所有用户信息
        users_data = []
        for username, user_cred in credentials.items():
            user_info = {
                "用户名": username,
                "是否管理员": "是" if user_cred.is_admin else "否",
                "剩余问答次数": user_cred.question_count,
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
                # 用户基本信息
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**用户名**: {user['用户名']}")
                    st.write(f"**是否管理员**: {user['是否管理员']}")
                with col2:
                    # 修改问答次数
                    new_count = st.number_input(
                        "问答次数",
                        min_value=0,
                        value=user["剩余问答次数"],
                        key=f"count_{user['用户名']}"
                    )
                    
                    # 修改管理员状态
                    new_admin = st.checkbox(
                        "设为管理员",
                        value=True if user["是否管理员"] == "是" else False,
                        key=f"admin_{user['用户名']}"
                    )
                
                # 权限设置
                st.subheader("权限设置")
                col1, col2, col3 = st.columns(3)
                
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
                
                # 保存和删除按钮
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("保存修改", key=f"save_{user['用户名']}"):
                        # 更新用户信息
                        credentials[user['用户名']].is_admin = new_admin
                        credentials[user['用户名']].question_count = new_count
                        credentials[user['用户名']].show_ent = new_ent
                        credentials[user['用户名']].show_int = new_int
                        credentials[user['用户名']].show_prompt = new_prompt
                        write_credentials(storage_file, credentials)
                        st.success(f"已更新 {user['用户名']} 的信息")
                        st.rerun()
                
                with col2:
                    # 不允许删除自己
                    if user['用户名'] != st.session_state.usname:
                        if st.button("删除用户", key=f"delete_{user['用户名']}"):
                            if user['用户名'] in credentials:
                                del credentials[user['用户名']]
                                write_credentials(storage_file, credentials)
                                st.success(f"已删除用户 {user['用户名']}")
                                st.rerun()
    
    with tab2:
        st.header("添加新用户")
        
        # 添加用户表单
        with st.form("add_user_form"):
            new_username = st.text_input("用户名")
            new_password = st.text_input("密码", type="password")
            is_admin = st.checkbox("设为管理员")
            question_count = st.number_input("问答次数", min_value=0, value=5)
            
            # 权限设置
            st.subheader("权限设置")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                show_ent = st.checkbox("实体识别结果")
            
            with col2:
                show_int = st.checkbox("意图识别结果")
            
            with col3:
                show_prompt = st.checkbox("知识库信息")
            
            submit = st.form_submit_button("添加用户")
            
            if submit:
                if not new_username:
                    st.error("用户名不能为空")
                elif not new_password:
                    st.error("密码不能为空")
                elif new_username in credentials:
                    st.error("用户名已存在")
                else:
                    # 创建新用户
                    new_user = Credentials(
                        new_username,
                        new_password,
                        is_admin,
                        show_ent,
                        show_int,
                        show_prompt,
                        question_count
                    )
                    credentials[new_username] = new_user
                    write_credentials(storage_file, credentials)
                    st.success(f"用户 {new_username} 添加成功！")

# 测试代码
if __name__ == "__main__":
    # 设置页面配置
    st.set_page_config(
        page_title="用户信息管理",
        page_icon="👤",
        layout="wide"
    )
    
    # 模拟登录状态
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = True
    if 'admin' not in st.session_state:
        st.session_state.admin = True
    if 'usname' not in st.session_state:
        st.session_state.usname = "admin"
    
    # 显示用户信息页面
    user_profile_page("admin", True)