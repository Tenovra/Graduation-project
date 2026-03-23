import sys
import os
import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from ultralytics import YOLO

# 导入数据库初始化函数
from db import init_database

# 导入自定义页面
from ui.home_page import HomePage
from ui.detection_page import DetectionPage
from ui.data_statistics_page import DataStatisticsPage
from ui.user_page import UserPage
from ui.data_management_page import DataManagementPage
from ui.login_page import LoginPage

class MainWindow(QMainWindow):
    # 定义登录成功信号
    login_completed = Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("舰船检测与识别系统")
        self.resize(1200, 800)
        self.current_username = ""
        self.current_role = ""
        
        # 创建主布局
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 创建顶部导航栏
        self.navbar = QWidget()
        self.navbar.setFixedHeight(60)
        self.navbar.setStyleSheet("background-color: #2c3e50;")
        self.navbar_layout = QHBoxLayout(self.navbar)
        self.navbar_layout.setContentsMargins(20, 0, 20, 0)
        self.navbar_layout.setSpacing(10)
        
        # 添加应用标题
        title_label = QLabel("舰船检测与识别系统")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.navbar_layout.addWidget(title_label)
        
        # 创建导航按钮
        self.nav_buttons = []
        nav_items = [
            {"name": "首页"},
            {"name": "目标检测"},
            {"name": "数据统计与分析"},
            {"name": "数据管理"},
            {"name": "用户管理"}
        ]
        
        # 添加弹性空间，使导航按钮居中
        self.navbar_layout.addStretch(1)
        
        for i, item in enumerate(nav_items):
            btn = QPushButton(item["name"])
            btn.setFixedSize(120, 40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    color: white;
                    border: none;
                    font-size: 16px;
                    background-color: transparent;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #34495e;
                }
                QPushButton:checked {
                    background-color: #3498db;
                    border-bottom: 3px solid white;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, idx=i: self.change_page(idx))
            self.navbar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            
        # 添加弹性空间，使导航按钮居中
        self.navbar_layout.addStretch(1)
        
        # 添加用户信息和时间显示
        self.user_info_layout = QHBoxLayout()
        self.user_info_layout.setSpacing(15)
        
        # 用户信息标签
        self.user_label = QLabel()
        self.user_label.setStyleSheet("color: white; font-size: 14px;")
        self.user_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.user_info_layout.addWidget(self.user_label)
        
        # 添加退出按钮
        self.logout_button = QPushButton("退出")
        self.logout_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #e74c3c;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.logout_button.setCursor(Qt.PointingHandCursor)
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setVisible(False)  # 初始不可见
        self.user_info_layout.addWidget(self.logout_button)
        
        # 添加登录按钮
        self.login_button = QPushButton("登录")
        self.login_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #3498db;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.show_login_page)
        self.login_button.setVisible(True)  # 初始可见
        self.user_info_layout.addWidget(self.login_button)
        
        # 时间标签
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: white; font-size: 14px;")
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.user_info_layout.addWidget(self.time_label)
        
        # 添加用户信息和时间到导航栏
        self.navbar_layout.addLayout(self.user_info_layout)
        
        # 创建内容区域
        self.content_widget = QStackedWidget()
        self.content_widget.setStyleSheet("background-color: #f5f5f5;")
        
        # 创建登录页面
        self.login_page = LoginPage()
        self.login_page.login_success.connect(self.on_login_success)
        
        # 创建各个页面
        self.home_page = HomePage()
        self.detection_page = DetectionPage()
        self.detection_page.current_username = self.current_username  # 传递当前用户名
        self.statistics_page = DataStatisticsPage()
        self.data_management_page = DataManagementPage()
        self.user_page = UserPage()
        
        # 添加页面到堆叠窗口
        self.content_widget.addWidget(self.login_page)  # 索引0 - 登录页面
        self.content_widget.addWidget(self.home_page)   # 索引1 - 首页
        self.content_widget.addWidget(self.detection_page)
        self.content_widget.addWidget(self.statistics_page)
        self.content_widget.addWidget(self.data_management_page)
        self.content_widget.addWidget(self.user_page)
        
        # 将顶部导航栏和内容区域添加到主布局
        self.main_layout.addWidget(self.navbar)
        self.main_layout.addWidget(self.content_widget)
        
        # 设置中央窗口
        self.setCentralWidget(self.main_widget)
        
        # 初始显示登录页面，隐藏导航栏
        self.navbar.setVisible(False)
        self.content_widget.setCurrentIndex(0)
        
        # 设置定时器更新时间
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 每秒更新一次
        self.update_time()
    
    def change_page(self, index):
        # 更新按钮状态
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        
        # 切换页面 (注意索引需要+1，因为索引0是登录页面)
        self.content_widget.setCurrentIndex(index + 1)
    
    def on_login_success(self, username, role):
        # 更新统计页面的用户信息
        self.statistics_page.set_user_info(username, role)
        # 保存用户信息
        self.current_username = username
        self.current_role = role
        
        # 更新用户信息显示
        self.user_label.setText(f"用户: {username} ({role})")
        
        # 显示导航栏并切换到首页
        self.navbar.setVisible(True)
        self.nav_buttons[0].setChecked(True)
        self.content_widget.setCurrentIndex(1)  # 切换到首页
        
        # 更新检测页面的用户名
        self.detection_page.current_username = username
        
        # 更新数据管理页面的用户信息
        self.data_management_page.set_user_info(username, role)
        
        # 根据用户角色控制用户管理页面的可见性
        if role == "管理员":
            # 管理员可以看到所有页面
            self.nav_buttons[4].setVisible(True)  # 用户管理按钮可见
        else:
            # 普通用户看不到用户管理页面
            self.nav_buttons[4].setVisible(False)  # 用户管理按钮不可见
        
        # 显示退出按钮，隐藏登录按钮
        self.logout_button.setVisible(True)
        self.login_button.setVisible(False)
        
        # 发出登录完成信号
        self.login_completed.emit()
    
    def logout(self):
        # 清空当前用户信息
        self.current_username = ""
        self.current_role = ""
        
        # 清空检测页面的用户名
        self.detection_page.current_username = ""
        
        # 清空统计页面的用户信息
        self.statistics_page.set_user_info("", "")
        
        # 更新用户信息显示
        self.user_label.setText("")
        
        # 隐藏导航栏并切换到登录页面
        self.navbar.setVisible(False)
        self.content_widget.setCurrentIndex(0)  # 切换到登录页面
        
        # 重置用户管理按钮的可见性（默认为可见，下次登录时会根据角色重新设置）
        self.nav_buttons[4].setVisible(True)
        
        # 隐藏退出按钮，显示登录按钮
        self.logout_button.setVisible(False)
        self.login_button.setVisible(True)
    
    def show_login_page(self):
        # 切换到登录页面
        self.content_widget.setCurrentIndex(0)
    
    def update_time(self):
        # 更新时间显示
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)

if __name__ == "__main__":
    # 确保存在必要的目录
    os.makedirs("ui/icons", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # 初始化数据库
    init_database()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())