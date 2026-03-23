# 数据库模块初始化

import os
from .database import Database

def init_database():
    """
    初始化数据库，如果数据库不存在则创建，并从JSON文件导入用户数据
    """
    # 确保数据目录存在
    os.makedirs("data", exist_ok=True)
    
    # 初始化用户数据库连接
    db = Database()
    
    # 检查是否需要从JSON导入数据
    users = db.get_all_users()
    if not users:
        # 尝试从JSON文件导入用户数据
        json_file = "data/users.json"
        if os.path.exists(json_file):
            print("从JSON文件导入用户数据...")
            db.import_users_from_json(json_file)
            print("导入完成")
        else:
            # 默认创建一个管理员账户
            print("创建默认管理员账户...")
            db.add_user("admin", "admin123", "管理员")
    
    # 关闭用户数据库连接
    db.close()
    
    return True