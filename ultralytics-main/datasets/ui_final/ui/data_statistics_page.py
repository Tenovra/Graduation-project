from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QDateEdit, QFrame, QSplitter
from PySide6.QtCore import Qt, QDate, QUrl
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView
from pyecharts.charts import Bar, Pie
from pyecharts import options as opts
from pyecharts.globals import ThemeType
import os
import sys
from datetime import datetime, timedelta
# 导入图表工具模块
from ui.chart_utils import ensure_echarts_available

class DataStatisticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_username = ""
        self.current_role = ""
        self.init_ui()
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        title_label = QLabel("数据统计与分析")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建筛选区域
        filter_widget = QWidget()
        filter_widget.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        filter_layout = QHBoxLayout(filter_widget)
        
        # 检测类型筛选
        detection_type_label = QLabel("检测类型:")
        filter_layout.addWidget(detection_type_label)
        
        self.detection_type_combo = QComboBox()
        self.detection_type_combo.addItems(["全部", "图像检测", "视频检测", "实时检测"])
        self.detection_type_combo.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        filter_layout.addWidget(self.detection_type_combo)
        
        # 目标类型筛选
        target_type_label = QLabel("目标类型:")
        filter_layout.addWidget(target_type_label)
        
        self.target_type_combo = QComboBox()
        self.target_type_combo.addItems(["全部类型"])
        self.target_type_combo.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        filter_layout.addWidget(self.target_type_combo)
        
        # 用户筛选（仅管理员可见）
        self.user_label = QLabel("用户:")
        filter_layout.addWidget(self.user_label)
        
        self.user_combo = QComboBox()
        self.user_combo.addItems(["全部用户"])
        self.user_combo.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        filter_layout.addWidget(self.user_combo)
        
        # 时间筛选
        time_label = QLabel("时间:")
        filter_layout.addWidget(time_label)
        
        self.time_combo = QComboBox()
        self.time_combo.addItems(["全部时间", "今天", "最近7天", "最近30天", "自定义"])
        self.time_combo.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        self.time_combo.currentIndexChanged.connect(self.on_time_filter_changed)
        filter_layout.addWidget(self.time_combo)
        
        # 日期选择器（默认隐藏）
        self.start_date = QDateEdit(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        self.start_date.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        self.start_date.setVisible(False)
        filter_layout.addWidget(self.start_date)
        
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        self.end_date.setVisible(False)
        filter_layout.addWidget(self.end_date)
        
        # 统计按钮
        stats_btn = QPushButton("统计分析")
        stats_btn.setStyleSheet("""
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
        stats_btn.clicked.connect(self.update_statistics)
        filter_layout.addWidget(stats_btn)
        
        main_layout.addWidget(filter_widget)
        
        # 创建图表区域
        charts_frame = QFrame()
        charts_frame.setStyleSheet("background-color: white; border-radius: 10px; margin-top: 20px;")
        charts_layout = QVBoxLayout(charts_frame)
        
        # 创建水平分割器，用于并排放置两个图表
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建图表容器
        self.bar_view = QWebEngineView()
        self.pie_view = QWebEngineView()
        
        splitter.addWidget(self.bar_view)
        splitter.addWidget(self.pie_view)
        
        # 设置分割器的初始大小
        splitter.setSizes([500, 500])
        
        charts_layout.addWidget(splitter)
        main_layout.addWidget(charts_frame, 1)  # 1表示拉伸因子，使图表区域占据更多空间
        
        # 数据库连接
        from db.detection_db import DetectionDatabase
        self.db = DetectionDatabase.get_instance()
    
    def set_user_info(self, username, role):
        """设置当前用户信息"""
        self.current_username = username
        self.current_role = role
        
        # 根据用户角色显示或隐藏用户筛选
        self.user_label.setVisible(role == "管理员")
        self.user_combo.setVisible(role == "管理员")
        
        # 加载目标类型和用户列表
        self.load_target_types()
        if role == "管理员":
            self.load_users()
        
        # 初始化统计图表
        self.update_statistics()
    
    def load_target_types(self):
        """加载目标类型列表"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 获取所有不同的目标类型
        cursor.execute("""
        SELECT DISTINCT class_name FROM (
            SELECT class_name FROM image_detections
            UNION
            SELECT class_name FROM video_detections
            UNION
            SELECT class_name FROM realtime_detections
        )
        ORDER BY class_name
        """)
        
        types = cursor.fetchall()
        self.target_type_combo.clear()
        self.target_type_combo.addItem("全部类型")
        for type_name in types:
            self.target_type_combo.addItem(type_name[0])
    
    def load_users(self):
        """加载用户列表（仅管理员可见）"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 获取所有不同的用户
        cursor.execute("""
        SELECT DISTINCT username FROM (
            SELECT username FROM image_detections
            UNION
            SELECT username FROM video_detections
            UNION
            SELECT username FROM realtime_detections
        )
        ORDER BY username
        """)
        
        users = cursor.fetchall()
        self.user_combo.clear()
        self.user_combo.addItem("全部用户")
        for user in users:
            self.user_combo.addItem(user[0])
    
    def on_time_filter_changed(self, index):
        """时间筛选变化时的处理"""
        # 如果选择了自定义，显示日期选择器
        is_custom = index == 4  # "自定义"选项的索引
        self.start_date.setVisible(is_custom)
        self.end_date.setVisible(is_custom)
    
    def get_time_filter_condition(self):
        """根据时间筛选选项生成SQL条件"""
        time_filter = self.time_combo.currentText()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if time_filter == "今天":
            start_date = today
            end_date = today + timedelta(days=1)
        elif time_filter == "最近7天":
            start_date = today - timedelta(days=7)
            end_date = today + timedelta(days=1)
        elif time_filter == "最近30天":
            start_date = today - timedelta(days=30)
            end_date = today + timedelta(days=1)
        elif time_filter == "自定义":
            start_date = self.start_date.date().toPython()
            end_date = self.end_date.date().toPython() + timedelta(days=1)  # 包含结束日期
        else:  # 全部时间
            return ""
        
        start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
        
        return f"AND timestamp BETWEEN '{start_str}' AND '{end_str}'"
    
    def update_statistics(self):
        """更新统计图表"""
        if not hasattr(self, 'current_username') or not self.current_username:
            return
        
        try:
            # 确保echarts库可用
            ensure_echarts_available()
            
            # 获取筛选条件
            detection_type = self.detection_type_combo.currentText()
            target_type = self.target_type_combo.currentText()
            time_condition = self.get_time_filter_condition()
            
            # 用户筛选条件
            user_filter = ""
            if self.current_role != "管理员":
                # 普通用户只能看到自己的数据
                user_filter = f"AND username = '{self.current_username}'"
            else:
                # 管理员可以筛选用户
                selected_user = self.user_combo.currentText()
                if selected_user != "全部用户":
                    user_filter = f"AND username = '{selected_user}'"
            
            # 目标类型筛选
            target_filter = ""
            if target_type != "全部类型":
                target_filter = f"AND class_name = '{target_type}'"
            
            # 创建柱状图 - 目标类型统计
            bar_chart = self.create_bar_chart(detection_type, user_filter, target_filter, time_condition)
            bar_path = "charts/stats_bar_chart.html"
            bar_chart.render(bar_path)
            # 修复HTML文件中的echarts引用
            from ui.chart_utils import fix_chart_html
            fix_chart_html(bar_path)
            # 使用QUrl.fromLocalFile()方法正确处理本地文件路径
            self.bar_view.load(QUrl.fromLocalFile(os.path.abspath(bar_path)))
            
            # 创建饼图 - 检测类型占比
            pie_chart = self.create_pie_chart(user_filter, target_filter, time_condition)
            pie_path = "charts/stats_pie_chart.html"
            pie_chart.render(pie_path)
            # 修复HTML文件中的echarts引用
            fix_chart_html(pie_path)
            # 使用QUrl.fromLocalFile()方法正确处理本地文件路径
            self.pie_view.load(QUrl.fromLocalFile(os.path.abspath(pie_path)))
            
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def create_bar_chart(self, detection_type, user_filter, target_filter, time_condition):
        """创建柱状图 - 目标类型统计"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 构建SQL查询获取目标类型统计
        if detection_type == "全部" or detection_type == "图像检测":
            image_query = f"""
            SELECT class_name, COUNT(*) as count FROM image_detections
            WHERE 1=1 {user_filter} {target_filter} {time_condition}
            GROUP BY class_name
            """
            cursor.execute(image_query)
            image_results = {row[0]: row[1] for row in cursor.fetchall()}
        else:
            image_results = {}
        
        if detection_type == "全部" or detection_type == "视频检测":
            video_query = f"""
            SELECT class_name, COUNT(*) as count FROM video_detections
            WHERE 1=1 {user_filter} {target_filter} {time_condition}
            GROUP BY class_name
            """
            cursor.execute(video_query)
            video_results = {row[0]: row[1] for row in cursor.fetchall()}
        else:
            video_results = {}
        
        if detection_type == "全部" or detection_type == "实时检测":
            realtime_query = f"""
            SELECT class_name, COUNT(*) as count FROM realtime_detections
            WHERE 1=1 {user_filter} {target_filter} {time_condition}
            GROUP BY class_name
            """
            cursor.execute(realtime_query)
            realtime_results = {row[0]: row[1] for row in cursor.fetchall()}
        else:
            realtime_results = {}
        
        # 合并结果
        all_classes = set(list(image_results.keys()) + list(video_results.keys()) + list(realtime_results.keys()))
        categories = sorted(list(all_classes))
        
        # 如果没有数据，添加一个默认类别
        if not categories:
            categories = ["无数据"]
            image_results = {"无数据": 0}
            video_results = {"无数据": 0}
            realtime_results = {"无数据": 0}
        
        # 准备数据
        image_values = [image_results.get(cat, 0) for cat in categories]
        video_values = [video_results.get(cat, 0) for cat in categories]
        realtime_values = [realtime_results.get(cat, 0) for cat in categories]
        
        # 创建柱状图
        bar = (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
            .add_xaxis(categories)
        )
        
        # 根据选择的检测类型添加数据系列
        if detection_type == "全部" or detection_type == "图像检测":
            bar.add_yaxis("图像检测", image_values, stack="stack1")
        if detection_type == "全部" or detection_type == "视频检测":
            bar.add_yaxis("视频检测", video_values, stack="stack1")
        if detection_type == "全部" or detection_type == "实时检测":
            bar.add_yaxis("实时检测", realtime_values, stack="stack1")
        
        # 设置全局选项
        bar.set_global_opts(
            title_opts=opts.TitleOpts(title="目标类型检测统计"),
            toolbox_opts=opts.ToolboxOpts(),
            legend_opts=opts.LegendOpts(pos_top="5%"),
            xaxis_opts=opts.AxisOpts(name="目标类型"),
            yaxis_opts=opts.AxisOpts(name="检测次数", min_=0),
        )
        
        return bar
    
    def create_pie_chart(self, user_filter, target_filter, time_condition):
        """创建饼图 - 检测类型占比"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 查询各检测类型的数量
        image_query = f"""
        SELECT COUNT(*) FROM image_detections
        WHERE 1=1 {user_filter} {target_filter} {time_condition}
        """
        cursor.execute(image_query)
        image_count = cursor.fetchone()[0]
        
        video_query = f"""
        SELECT COUNT(*) FROM video_detections
        WHERE 1=1 {user_filter} {target_filter} {time_condition}
        """
        cursor.execute(video_query)
        video_count = cursor.fetchone()[0]
        
        realtime_query = f"""
        SELECT COUNT(*) FROM realtime_detections
        WHERE 1=1 {user_filter} {target_filter} {time_condition}
        """
        cursor.execute(realtime_query)
        realtime_count = cursor.fetchone()[0]
        
        # 准备数据
        categories = ["图像检测", "视频检测", "实时检测"]
        values = [image_count, video_count, realtime_count]
        
        # 如果所有值都为0，添加一个默认值
        if sum(values) == 0:
            categories = ["无数据"]
            values = [1]
        
        # 创建饼图
        pie = (
            Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
            .add(
                series_name="检测类型",
                data_pair=[list(z) for z in zip(categories, values)],
                radius=["40%", "70%"],
                label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)"),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="检测类型占比"),
                legend_opts=opts.LegendOpts(pos_top="5%"),
            )
        )
        
        return pie