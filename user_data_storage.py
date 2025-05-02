import json
import os

class Credentials:
    def __init__(self, username, password, is_admin=False, show_ent=False, show_int=False, show_prompt=False, question_count=5):
        self.username = username
        self.password = password
        self.is_admin = is_admin
        self.show_ent = show_ent
        self.show_int = show_int
        self.show_prompt = show_prompt
        self.question_count = question_count

    def to_dict(self):
        return {
            'username': self.username,
            'password': self.password,
            'is_admin': self.is_admin,
            'show_ent': self.show_ent,
            'show_int': self.show_int,
            'show_prompt': self.show_prompt,
            'question_count': self.question_count
        }

def create_folder_if_not_exist(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def read_credentials(file_path):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return {k: Credentials(**v) for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_credentials(file_path, credentials_dict):
    data = {k: v.to_dict() for k, v in credentials_dict.items()}
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

# 文件存储位置
storage_folder = "tmp_data"
storage_file = os.path.join(storage_folder, "user_credentials.json")

# 确保文件夹存在
create_folder_if_not_exist(storage_folder)

# 读取现有的用户数据
credentials = read_credentials(storage_file)

# 如果初始文件为空，则初始化管理员账户
if not credentials:
    admin = Credentials("admin", "admin123", True)
    credentials['admin'] = admin
    write_credentials(storage_file, credentials)
