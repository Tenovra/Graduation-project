from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from db.database import Database

class StatisticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.init_ui()
    
    def showEvent(self, event):
        # 当页面显示时加载用户列表
        self.load_users()
        super().showEvent(event)
    
    def load_users(self):
        # 清空当前用户列表（保留"全部"选项）
        while self.user_combo.count() > 1:
            self.user_combo.removeItem(1)
        
        # 从数据库获取所有用户
        users = self.db.get_all_users()
        
        # 添加用户到下拉列表
        for user in users:
            self.user_combo.addItem(user["username"])
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        title_label = QLabel("数据统计与分析")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 添加筛选条件区域
        filter_widget = QWidget()
        filter_widget.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        filter_layout = QVBoxLayout(filter_widget)
        
        filter_title = QLabel("筛选条件")
        filter_title.setFont(QFont("Arial", 14, QFont.Bold))
        filter_layout.addWidget(filter_title)
        
        # 创建水平布局用于筛选条件
        filter_options_layout = QHBoxLayout()
        
        # 时间范围选择
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_layout.setContentsMargins(5, 0, 5, 0)
        
        time_label = QLabel("时间范围:")
        time_layout.addWidget(time_label)
        
        self.time_combo = QComboBox()
        self.time_combo.addItems(["今天", "本周", "本月", "本季度", "本年", "自定义"])
        self.time_combo.setStyleSheet("padding: 5px; border: 1px solid #bdc3c7; border-radius: 4px;")
        time_layout.addWidget(self.time_combo)
        filter_options_layout.addWidget(time_widget)
        
        # 检测类型选择
        type_widget = QWidget()
        type_layout = QVBoxLayout(type_widget)
        type_layout.setContentsMargins(5, 0, 5, 0)
        
        type_label = QLabel("检测类型:")
        type_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["全部", "图像检测", "视频检测", "实时检测"])
        self.type_combo.setStyleSheet("padding: 5px; border: 1px solid #bdc3c7; border-radius: 4px;")
        type_layout.addWidget(self.type_combo)
        filter_options_layout.addWidget(type_widget)
        
        # 目标类型选择
        target_widget = QWidget()
        target_layout = QVBoxLayout(target_widget)
        target_layout.setContentsMargins(5, 0, 5, 0)
        
        target_label = QLabel("目标类型:")
        target_layout.addWidget(target_label)
        
        self.target_combo = QComboBox()
        self.target_combo.addItems(["全部", "人", "车辆", "动物", "其他"])
        self.target_combo.setStyleSheet("padding: 5px; border: 1px solid #bdc3c7; border-radius: 4px;")
        target_layout.addWidget(self.target_combo)
        filter_options_layout.addWidget(target_widget)
        
        # 用户筛选选择
        user_widget = QWidget()
        user_layout = QVBoxLayout(user_widget)
        user_layout.setContentsMargins(5, 0, 5, 0)
        
        user_label = QLabel("用户:")
        user_layout.addWidget(user_label)
        
        self.user_combo = QComboBox()
        self.user_combo.addItem("全部")
        # 用户列表将在页面显示时从数据库加载
        self.user_combo.setStyleSheet("padding: 5px; border: 1px solid #bdc3c7; border-radius: 4px;")
        user_layout.addWidget(self.user_combo)
        filter_options_layout.addWidget(user_widget)
        
        # 将水平布局添加到筛选条件布局中
        filter_layout.addLayout(filter_options_layout)
        
        # 查询按钮
        query_btn = QPushButton("查询")
        query_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        filter_layout.addWidget(query_btn)
        
        main_layout.addWidget(filter_widget)
        
        # 统计结果区域
        stats_widget = QWidget()
        stats_widget.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        stats_layout = QVBoxLayout(stats_widget)
        
        stats_title = QLabel("统计结果")
        stats_title.setFont(QFont("Arial", 14, QFont.Bold))
        stats_layout.addWidget(stats_title)
        
        # 统计数据展示
        data_layout = QHBoxLayout()
        
        # 总检测次数
        total_widget = QWidget()
        total_widget.setStyleSheet("background-color: #3498db; color: white; border-radius: 8px; padding: 10px;")
        total_layout = QVBoxLayout(total_widget)
        
        total_value = QLabel("0")
        total_value.setFont(QFont("Arial", 24, QFont.Bold))
        total_value.setAlignment(Qt.AlignCenter)
        
        total_label = QLabel("总检测次数")
        total_label.setAlignment(Qt.AlignCenter)
        
        total_layout.addWidget(total_value)
        total_layout.addWidget(total_label)
        data_layout.addWidget(total_widget)
        
        # 目标检出数
        target_widget = QWidget()
        target_widget.setStyleSheet("background-color: #2ecc71; color: white; border-radius: 8px; padding: 10px;")
        target_layout = QVBoxLayout(target_widget)
        
        target_value = QLabel("0")
        target_value.setFont(QFont("Arial", 24, QFont.Bold))
        target_value.setAlignment(Qt.AlignCenter)
        
        target_label = QLabel("目标检出数")
        target_label.setAlignment(Qt.AlignCenter)
        
        target_layout.addWidget(target_value)
        target_layout.addWidget(target_label)
        data_layout.addWidget(target_widget)
        
        # 平均置信度
        conf_widget = QWidget()
        conf_widget.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 8px; padding: 10px;")
        conf_layout = QVBoxLayout(conf_widget)
        
        conf_value = QLabel("0%")
        conf_value.setFont(QFont("Arial", 24, QFont.Bold))
        conf_value.setAlignment(Qt.AlignCenter)
        
        conf_label = QLabel("平均置信度")
        conf_label.setAlignment(Qt.AlignCenter)
        
        conf_layout.addWidget(conf_value)
        conf_layout.addWidget(conf_label)
        data_layout.addWidget(conf_widget)
        
        stats_layout.addLayout(data_layout)
        
        # 图表区域
        chart_label = QLabel("图表区域 - 这里将显示统计图表")
        chart_label.setStyleSheet("background-color: #ecf0f1; min-height: 300px; border-radius: 4px; padding: 10px;")
        chart_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(chart_label)
        
        main_layout.addWidget(stats_widget)