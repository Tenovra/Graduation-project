from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from db.database import Database

class UserPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        title_label = QLabel("用户管理")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 添加用户表单区域
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        form_layout = QVBoxLayout(form_widget)
        
        form_title = QLabel("添加/编辑用户")
        form_title.setFont(QFont("Arial", 14, QFont.Bold))
        form_layout.addWidget(form_title)
        
        # 用户名输入
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名:")
        username_label.setFixedWidth(80)
        username_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        username_layout.addWidget(self.username_input)
        form_layout.addLayout(username_layout)
        
        # 密码输入
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setFixedWidth(80)
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)
        
        # 角色选择
        role_layout = QHBoxLayout()
        role_label = QLabel("角色:")
        role_label.setFixedWidth(80)
        role_layout.addWidget(role_label)
        
        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText("请输入角色 (管理员/普通用户)")
        self.role_input.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        role_layout.addWidget(self.role_input)
        form_layout.addLayout(role_layout)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("添加用户")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.add_btn.clicked.connect(self.add_user)
        buttons_layout.addWidget(self.add_btn)
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_form)
        buttons_layout.addWidget(self.clear_btn)
        
        form_layout.addLayout(buttons_layout)
        main_layout.addWidget(form_widget)
        
        # 用户列表区域
        list_widget = QWidget()
        list_widget.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        list_layout = QVBoxLayout(list_widget)
        
        list_title = QLabel("用户列表")
        list_title.setFont(QFont("Arial", 14, QFont.Bold))
        list_layout.addWidget(list_title)
        
        # 用户表格
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["用户名", "角色", "编辑", "删除"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setStyleSheet("border: 1px solid #bdc3c7; border-radius: 4px;")
        list_layout.addWidget(self.user_table)
        
        main_layout.addWidget(list_widget)
    
    def add_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_input.text().strip()
        
        if not username or not password or not role:
            QMessageBox.warning(self, "输入错误", "请填写所有字段")
            return
        
        # 检查用户名是否已存在
        if self.db.get_user(username):
            QMessageBox.warning(self, "添加失败", "用户名已存在")
            return
        
        # 将用户信息保存到数据库
        success = self.db.add_user(username, password, role)
        if success:
            self.add_user_to_table(username, role)
            self.clear_form()
            QMessageBox.information(self, "成功", f"用户 {username} 已添加")
        else:
            QMessageBox.warning(self, "添加失败", "创建用户时出现错误")
    
    def add_user_to_table(self, username, role):
        row_position = self.user_table.rowCount()
        self.user_table.insertRow(row_position)
        
        # 添加用户名和角色
        self.user_table.setItem(row_position, 0, QTableWidgetItem(username))
        self.user_table.setItem(row_position, 1, QTableWidgetItem(role))
        
        # 添加编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_user(row_position))
        self.user_table.setCellWidget(row_position, 2, edit_btn)
        
        # 添加删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_user(row_position))
        self.user_table.setCellWidget(row_position, 3, delete_btn)
    
    def edit_user(self, row):
        username = self.user_table.item(row, 0).text()
        role = self.user_table.item(row, 1).text()
        
        self.username_input.setText(username)
        self.role_input.setText(role)
        self.password_input.clear()
        
        # 更改添加按钮为更新按钮
        self.add_btn.setText("更新用户")
        self.add_btn.clicked.disconnect()
        self.add_btn.clicked.connect(lambda: self.update_user(row))
    
    def update_user(self, row):
        old_username = self.user_table.item(row, 0).text()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_input.text().strip()
        
        if not username or not role:
            QMessageBox.warning(self, "输入错误", "用户名和角色不能为空")
            return
        
        # 如果用户名已更改，检查新用户名是否已存在
        if username != old_username and self.db.get_user(username):
            QMessageBox.warning(self, "更新失败", "新用户名已存在")
            return
        
        # 更新数据库中的用户信息
        if username != old_username:
            # 如果用户名已更改，需要删除旧用户并创建新用户
            if password:
                self.db.delete_user(old_username)
                success = self.db.add_user(username, password, role)
            else:
                QMessageBox.warning(self, "更新失败", "更改用户名时必须提供密码")
                return
        else:
            # 如果用户名未更改，只更新密码和角色
            if password:
                success = self.db.update_user(username, password=password, role=role)
            else:
                success = self.db.update_user(username, role=role)
        
        if success:
            # 更新表格中的用户信息
            self.user_table.setItem(row, 0, QTableWidgetItem(username))
            self.user_table.setItem(row, 1, QTableWidgetItem(role))
            
            self.clear_form()
            self.add_btn.setText("添加用户")
            self.add_btn.clicked.disconnect()
            self.add_btn.clicked.connect(self.add_user)
            
            QMessageBox.information(self, "成功", f"用户 {username} 已更新")
        else:
            QMessageBox.warning(self, "更新失败", "更新用户信息时出现错误")
    
    def delete_user(self, row):
        username = self.user_table.item(row, 0).text()
        
        reply = QMessageBox.question(self, "确认删除", f"确定要删除用户 {username} 吗？",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 从数据库中删除用户
            success = self.db.delete_user(username)
            if success:
                # 从表格中删除用户
                self.user_table.removeRow(row)
                QMessageBox.information(self, "成功", f"用户 {username} 已删除")
            else:
                QMessageBox.warning(self, "删除失败", "删除用户时出现错误")
    
    def clear_form(self):
        self.username_input.clear()
        self.password_input.clear()
        self.role_input.clear()
        
        # 确保添加按钮功能正确
        if self.add_btn.text() != "添加用户":
            self.add_btn.setText("添加用户")
            self.add_btn.clicked.disconnect()
            self.add_btn.clicked.connect(self.add_user)
    
    def load_users(self):
        # 从数据库加载所有用户
        users = self.db.get_all_users()
        for user in users:
            self.add_user_to_table(user["username"], user["role"])