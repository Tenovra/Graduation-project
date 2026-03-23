import sqlite3
import os
import json

class Database:
    def __init__(self, db_path="data/users.db"):
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 连接到数据库
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # 创建用户表（如果不存在）
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        ''')
        self.conn.commit()
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def get_user(self, username):
        """获取用户信息"""
        self.cursor.execute("SELECT username, password, role FROM users WHERE username = ?", (username,))
        user = self.cursor.fetchone()
        if user:
            return {"username": user[0], "password": user[1], "role": user[2]}
        return None
    
    def get_all_users(self):
        """获取所有用户信息"""
        self.cursor.execute("SELECT username, password, role FROM users")
        users = self.cursor.fetchall()
        return [{"username": user[0], "password": user[1], "role": user[2]} for user in users]
    
    def add_user(self, username, password, role):
        """添加新用户"""
        try:
            self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                               (username, password, role))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # 用户名已存在
            return False
    
    def update_user(self, username, password=None, role=None):
        """更新用户信息"""
        if password and role:
            self.cursor.execute("UPDATE users SET password = ?, role = ? WHERE username = ?", 
                               (password, role, username))
        elif password:
            self.cursor.execute("UPDATE users SET password = ? WHERE username = ?", 
                               (password, username))
        elif role:
            self.cursor.execute("UPDATE users SET role = ? WHERE username = ?", 
                               (role, username))
        else:
            return False
        
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def delete_user(self, username):
        """删除用户"""
        self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def import_users_from_json(self, json_file):
        """从JSON文件导入用户数据"""
        if not os.path.exists(json_file):
            return False
        
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                users = json.load(f)
            
            for username, user_data in users.items():
                self.add_user(username, user_data["password"], user_data["role"])
            
            return True
        except Exception as e:
            print(f"导入用户数据失败: {e}")
            return False