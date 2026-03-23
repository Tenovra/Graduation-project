from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTabWidget, QMessageBox, QCheckBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
import os
import json
from db.database import Database

class LoginPage(QWidget):
    # 定义登录成功信号
    login_success = Signal(str, str)  # 用户名, 角色
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.db = Database()
        self.load_users()
        self.load_saved_credentials()
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建中央容器
        container = QWidget()
        container.setFixedSize(400, 450)
        container.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            border: 1px solid #ddd;
        """)
        
        # 设置窗口背景
        self.setStyleSheet("""
            background-color: #f5f5f5;
        """)
        
        # 创建容器布局
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        
        # 添加标题
        title_label = QLabel("舰船检测与识别系统")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        container_layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: none;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
        """)
        
        # 创建登录和注册页面
        login_tab = QWidget()
        register_tab = QWidget()
        
        self.setup_login_tab(login_tab)
        self.setup_register_tab(register_tab)
        
        self.tab_widget.addTab(login_tab, "登录")
        self.tab_widget.addTab(register_tab, "注册")
        
        container_layout.addWidget(self.tab_widget)
        
        # 将容器添加到主布局并居中
        main_layout.addWidget(container, 0, Qt.AlignCenter)
    
    def setup_login_tab(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 20, 0, 10)
        layout.setSpacing(15)
        
        # 用户名输入
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("用户名")
        self.login_username.setStyleSheet("""
            padding: 10px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 14px;
        """)
        layout.addWidget(self.login_username)
        
        # 密码输入
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("密码")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setStyleSheet("""
            padding: 10px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 14px;
        """)
        layout.addWidget(self.login_password)
        
        # 记住密码选项
        remember_layout = QHBoxLayout()
        self.remember_checkbox = QCheckBox("记住密码")
        self.remember_checkbox.setStyleSheet("font-size: 14px;")
        remember_layout.addWidget(self.remember_checkbox)
        remember_layout.addStretch()
        layout.addLayout(remember_layout)
        
        # 登录按钮
        self.login_button = QPushButton("登录")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)
        
        # 添加一些空间
        layout.addStretch()
    
    def setup_register_tab(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 20, 0, 10)
        layout.setSpacing(15)
        
        # 用户名输入
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("用户名")
        self.register_username.setStyleSheet("""
            padding: 10px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 14px;
        """)
        layout.addWidget(self.register_username)
        
        # 密码输入
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("密码")
        self.register_password.setEchoMode(QLineEdit.Password)
        self.register_password.setStyleSheet("""
            padding: 10px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 14px;
        """)
        layout.addWidget(self.register_password)
        
        # 确认密码输入
        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("确认密码")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setStyleSheet("""
            padding: 10px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 14px;
        """)
        layout.addWidget(self.confirm_password)
        
        # 移除角色选择部分
        
        # 注册按钮
        self.register_button = QPushButton("注册")
        self.register_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 4px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.register_button.clicked.connect(self.register)
        layout.addWidget(self.register_button)
        
        # 添加一些空间
        layout.addStretch()
    
    def load_users(self):
        # 检查数据库中是否有用户，如果没有则导入JSON数据或创建默认管理员账户
        users = self.db.get_all_users()
        
        if not users:
            # 尝试从JSON文件导入用户数据
            json_file = "data/users.json"
            if os.path.exists(json_file):
                self.db.import_users_from_json(json_file)
            else:
                # 默认创建一个管理员账户
                self.db.add_user("admin", "admin123", "管理员")
    
    def save_users(self):
        # 数据库自动保存，此方法保留以兼容现有代码
        pass
        
    def save_credentials(self, username, password):
        """保存用户凭据到本地文件"""
        credentials = {"username": username, "password": password}
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/credentials.json", "w", encoding="utf-8") as f:
                json.dump(credentials, f)
        except Exception as e:
            print(f"保存凭据时出错: {e}")
    
    def clear_credentials(self):
        """清除保存的凭据"""
        if os.path.exists("data/credentials.json"):
            try:
                os.remove("data/credentials.json")
            except Exception as e:
                print(f"清除凭据时出错: {e}")
    
    def load_saved_credentials(self):
        """加载保存的凭据"""
        try:
            if os.path.exists("data/credentials.json"):
                with open("data/credentials.json", "r", encoding="utf-8") as f:
                    credentials = json.load(f)
                    if "username" in credentials and "password" in credentials:
                        self.login_username.setText(credentials["username"])
                        self.login_password.setText(credentials["password"])
                        self.remember_checkbox.setChecked(True)
        except Exception as e:
            print(f"加载凭据时出错: {e}")
    
    def login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "登录失败", "请输入用户名和密码")
            return
        
        user = self.db.get_user(username)
        if user and user["password"] == password:
            role = user["role"]
            QMessageBox.information(self, "登录成功", f"欢迎回来，{username}!")
            
            # 如果勾选了记住密码，保存用户名和密码
            if self.remember_checkbox.isChecked():
                self.save_credentials(username, password)
            else:
                # 如果没有勾选，则清除保存的凭据
                self.clear_credentials()
            
            # 发送登录成功信号
            self.login_success.emit(username, role)
        else:
            QMessageBox.warning(self, "登录失败", "用户名或密码错误")
    
    def register(self):
        username = self.register_username.text().strip()
        password = self.register_password.text().strip()
        confirm = self.confirm_password.text().strip()
        # 默认设置为普通用户，移除角色选择
        role = "普通用户"
        
        if not username or not password or not confirm:
            QMessageBox.warning(self, "注册失败", "请填写所有字段")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "注册失败", "两次输入的密码不一致")
            return
        
        # 检查用户名是否已存在
        if self.db.get_user(username):
            QMessageBox.warning(self, "注册失败", "用户名已存在")
            return
        
        # 添加新用户
        success = self.db.add_user(username, password, role)
        if success:
            QMessageBox.information(self, "注册成功", "账户创建成功，请登录")
            
            # 清空输入并切换到登录页面
            self.register_username.clear()
            self.register_password.clear()
            self.confirm_password.clear()
            self.tab_widget.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "注册失败", "创建账户时出现错误")