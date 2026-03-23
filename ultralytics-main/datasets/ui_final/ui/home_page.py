from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout, QFrame, QSplitter
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView
from pyecharts.charts import Bar, Pie, Gauge, Calendar, TreeMap, Sunburst
from pyecharts import options as opts
from pyecharts.globals import ThemeType
from pyecharts.commons.utils import JsCode
import random
import os
import sys
import psutil
from datetime import datetime, timedelta
# 导入图表工具模块
from ui.chart_utils import ensure_echarts_available, fix_chart_html
from db.detection_db import DetectionDatabase

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DetectionDatabase.get_instance()
        self.init_ui()
        self.init_charts()
        # 创建定时器，每10秒更新系统资源使用情况
        self.resource_timer = QTimer(self)
        self.resource_timer.timeout.connect(self.update_resource_charts)
        self.resource_timer.start(10000)  # 10秒更新一次
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 添加标题
        title_label = QLabel("舰船检测与识别系统")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # 创建网格布局用于放置六个图表
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # 创建六个图表容器框架
        # 左上：系统资源占用
        self.resource_frame = QFrame()
        self.resource_frame.setFrameShape(QFrame.StyledPanel)
        self.resource_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        resource_layout = QVBoxLayout(self.resource_frame)
        resource_title = QLabel("当前系统占用资源状况")
        resource_title.setAlignment(Qt.AlignCenter)
        resource_title.setFont(QFont("Arial", 12, QFont.Bold))
        resource_layout.addWidget(resource_title)
        self.resource_view = QWebEngineView()
        resource_layout.addWidget(self.resource_view)
        
        # 左下：人员使用次数统计
        self.usage_frame = QFrame()
        self.usage_frame.setFrameShape(QFrame.StyledPanel)
        self.usage_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        usage_layout = QVBoxLayout(self.usage_frame)
        usage_title = QLabel("人员使用次数统计")
        usage_title.setAlignment(Qt.AlignCenter)
        usage_title.setFont(QFont("Arial", 12, QFont.Bold))
        usage_layout.addWidget(usage_title)
        self.usage_view = QWebEngineView()
        usage_layout.addWidget(self.usage_view)
        
        # 中间：目标类型统计
        self.target_frame = QFrame()
        self.target_frame.setFrameShape(QFrame.StyledPanel)
        self.target_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        target_layout = QVBoxLayout(self.target_frame)
        target_layout.setContentsMargins(10, 5, 10, 10)  # 减小上边距
        target_title = QLabel("目标类型统计")
        target_title.setAlignment(Qt.AlignCenter)
        target_title.setFont(QFont("Arial", 14, QFont.Bold))  # 增大字体
        target_title.setStyleSheet("margin-bottom: 0px;")  # 减小标题下方间距
        target_layout.addWidget(target_title)
        self.target_view = QWebEngineView()
        target_layout.addWidget(self.target_view, 1)  # 添加拉伸因子，使图表占据更多空间
        
        # 右上：检测人员统计
        self.personnel_frame = QFrame()
        self.personnel_frame.setFrameShape(QFrame.StyledPanel)
        self.personnel_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        personnel_layout = QVBoxLayout(self.personnel_frame)
        personnel_title = QLabel("检测人员统计")
        personnel_title.setAlignment(Qt.AlignCenter)
        personnel_title.setFont(QFont("Arial", 12, QFont.Bold))
        personnel_layout.addWidget(personnel_title)
        self.personnel_view = QWebEngineView()
        personnel_layout.addWidget(self.personnel_view)
        
        # 右下：检测方式统计
        self.method_frame = QFrame()
        self.method_frame.setFrameShape(QFrame.StyledPanel)
        self.method_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        method_layout = QVBoxLayout(self.method_frame)
        method_title = QLabel("检测方式统计")
        method_title.setAlignment(Qt.AlignCenter)
        method_title.setFont(QFont("Arial", 12, QFont.Bold))
        method_layout.addWidget(method_title)
        self.method_view = QWebEngineView()
        method_layout.addWidget(self.method_view)
        
        # 将图表添加到网格布局中
        grid_layout.addWidget(self.resource_frame, 0, 0)  # 左上
        grid_layout.addWidget(self.usage_frame, 1, 0)     # 左下
        grid_layout.addWidget(self.target_frame, 0, 1, 2, 1)  # 中间（跨两行）
        grid_layout.addWidget(self.personnel_frame, 0, 2)  # 右上
        grid_layout.addWidget(self.method_frame, 1, 2)    # 右下
        
        # 设置列宽比例
        grid_layout.setColumnStretch(0, 1)  # 左列
        grid_layout.setColumnStretch(1, 2)  # 中间列（宽度是左右列的两倍）
        grid_layout.setColumnStretch(2, 1)  # 右列
        
        main_layout.addLayout(grid_layout)
    
    def init_charts(self):
        # 确保echarts库可用
        ensure_echarts_available()
        
        # 初始化所有图表
        self.update_resource_charts()
        self.update_usage_chart()
        self.update_target_chart()
        self.update_personnel_chart()
        self.update_method_chart()
    
    def update_resource_charts(self):
        # 获取系统资源使用情况
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 尝试获取GPU使用情况（如果有NVIDIA GPU）
        gpu_percent = 0
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_percent = gpus[0].load * 100
        except:
            # 如果没有GPU或无法获取GPU信息，使用随机值模拟
            gpu_percent = random.randint(10, 90)
        
        # 创建仪表盘图表
        gauge = (
            Gauge(init_opts=opts.InitOpts(width="100%", height="300px", theme=ThemeType.LIGHT))
            .add(
                series_name="CPU使用率",
                data_pair=[("CPU", cpu_percent)],
                radius="50%",
                center=["25%", "50%"],
                progress={
                    "show": True,
                    "width": 15,
                    "overlap": False,
                    "roundCap": True
                },
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(width=15)
                ),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                axislabel_opts=opts.LabelOpts(is_show=False),
                detail_label_opts=opts.LabelOpts(
                    formatter="{value}%",
                    font_size=20
                ),
            )
            .add(
                series_name="内存使用率",
                data_pair=[("内存", memory_percent)],
                radius="50%",
                center=["50%", "50%"],
                progress={
                    "show": True,
                    "width": 15,
                    "overlap": False,
                    "roundCap": True
                },
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(width=15)
                ),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                axislabel_opts=opts.LabelOpts(is_show=False),
                detail_label_opts=opts.LabelOpts(
                    formatter="{value}%",
                    font_size=20
                ),
            )
            .add(
                series_name="GPU使用率",
                data_pair=[("GPU", gpu_percent)],
                radius="50%",
                center=["75%", "50%"],
                progress={
                    "show": True,
                    "width": 15,
                    "overlap": False,
                    "roundCap": True
                },
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(width=15)
                ),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                axislabel_opts=opts.LabelOpts(is_show=False),
                detail_label_opts=opts.LabelOpts(
                    formatter="{value}%",
                    font_size=20
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="系统资源使用情况", pos_left="center", is_show=False),
                tooltip_opts=opts.TooltipOpts(formatter="{a} <br/>{b} : {c}%"),
                legend_opts=opts.LegendOpts(is_show=True, pos_bottom="5%", orient="horizontal"),
            )
        )
        
        # 渲染图表
        gauge_path = "charts/stats_gauge_chart.html"
        gauge.render(gauge_path)
        fix_chart_html(gauge_path)
        self.resource_view.load(QUrl.fromLocalFile(os.path.abspath(gauge_path)))
    
    def update_usage_chart(self):
        # 获取用户使用数据
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 获取最近30天的日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        current_month = end_date.strftime("%Y-%m")
        
        # 查询每天的使用次数和类型
        cursor.execute("""
        SELECT date(timestamp) as date, 
               CASE 
                   WHEN source = 'image_detections' THEN '图像检测'
                   WHEN source = 'video_detections' THEN '视频检测'
                   WHEN source = 'realtime_detections' THEN '实时检测'
               END as detection_type,
               COUNT(*) as count 
        FROM (
            SELECT timestamp, 'image_detections' as source FROM image_detections
            UNION ALL
            SELECT timestamp, 'video_detections' as source FROM video_detections
            UNION ALL
            SELECT timestamp, 'realtime_detections' as source FROM realtime_detections
        ) WHERE timestamp BETWEEN ? AND ?
        GROUP BY date(timestamp), detection_type
        ORDER BY date
        """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        
        results = cursor.fetchall()
        
        # 整理数据格式
        date_data = {}
        for row in results:
            date_str = str(row[0])
            detection_type = row[1]
            count = row[2]
            
            if date_str not in date_data:
                date_data[date_str] = {
                    '图像检测': 0,
                    '视频检测': 0,
                    '实时检测': 0,
                    'total': 0
                }
            
            date_data[date_str][detection_type] = count
            date_data[date_str]['total'] += count
        
        # 如果没有数据，生成模拟数据
        if not date_data:
            for i in range(30, 0, -1):
                date_str = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
                date_data[date_str] = {
                    '图像检测': random.randint(1, 10),
                    '视频检测': random.randint(1, 10),
                    '实时检测': random.randint(1, 10),
                    'total': 0
                }
                date_data[date_str]['total'] = sum(v for k, v in date_data[date_str].items() if k != 'total')
        
        # 准备日历数据
        calendar_data = [[date, data['total']] for date, data in date_data.items()]
        
        # 准备饼图系列
        pie_series = []
        for date, data in date_data.items():
            if date.startswith(current_month):
                pie_series.append({
                    "type": "pie",
                    "id": f"pie-{date}",
                    "coordinateSystem": "calendar",
                    "center": date,
                    "radius": 15,
                    "label": {"show": False},
                    "zlevel": 1,  # 确保饼图在日期标签下方
                    "data": [
                        {"name": "图像检测", "value": data['图像检测']},
                        {"name": "视频检测", "value": data['视频检测']},
                        {"name": "实时检测", "value": data['实时检测']}
                    ]
                })
        
        # 创建日历饼图
        calendar = (
            Calendar(init_opts=opts.InitOpts(width="100%", height="300px", theme=ThemeType.LIGHT))
            .add(
                series_name="使用次数",
                yaxis_data=calendar_data,
                label_opts=opts.LabelOpts(
                    is_show=False  # 关闭默认标签，我们将在自定义HTML中显示日期
                ),
                calendar_opts=opts.CalendarOpts(
                    pos_top="middle",
                    pos_left="center",
                    cell_size=[60, 40],
                    range_=[f"{current_month}-01", f"{current_month}-{(end_date.replace(day=1) + timedelta(days=32)).replace(day=1).replace(day=1) - timedelta(days=1):%d}"],
                    orient="vertical",
                    daylabel_opts=opts.CalendarDayLabelOpts(
                        is_show=True,
                        first_day=1,
                        position="top",
                        name_map=["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
                    ),
                    monthlabel_opts=opts.CalendarMonthLabelOpts(is_show=True),
                    yearlabel_opts=opts.CalendarYearLabelOpts(is_show=False),
                    itemstyle_opts=opts.ItemStyleOpts(
                        border_width=0.5,
                        border_color="#ccc"
                    ),
                    splitline_opts=opts.SplitLineOpts(
                        is_show=True,
                        linestyle_opts=opts.LineStyleOpts(
                            color="#ccc",
                            width=1,
                            type_="solid"
                        )
                    )
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="使用日历饼图", pos_left="center", is_show=False),
                legend_opts=opts.LegendOpts(
                    is_show=True,
                    pos_top="5%",
                    orient="horizontal",
                    item_width=25,
                    item_height=14,
                    item_gap=15,
                    legend_icon=None
                ),
                tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}")
            )
        )
        
        # 添加饼图系列
        for pie in pie_series:
            calendar.add_js_funcs(f"chart_{calendar.chart_id}.addSeries({pie});")
        
        # 渲染图表
        calendar_path = "charts/stats_calendar_chart.html"
        calendar.render(calendar_path)
        fix_chart_html(calendar_path)
        
        # 直接创建完整的HTML文件，确保饼图系列正确显示
        # 导入json模块用于序列化数据
        import json
        
        # 分步构建HTML内容，避免嵌套f-string
        calendar_data_json = json.dumps(calendar_data)
        pie_series_json = json.dumps(pie_series)
        
        # HTML头部
        html_head = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>使用日历饼图</title>
            <script src="./assets/echarts.min.js"></script>
        </head>
        <body>
            <div id="calendar" style="width:100%; height:300px;"></div>
            <script type="text/javascript">
                var chart = echarts.init(document.getElementById('calendar'), 'light', {renderer: 'canvas'});
        '''
        
        # 日历图配置 - 使用普通字符串，避免嵌套f-string
        calendar_config = '''
                // 基础日历图配置
                var option = {
                    title: {
                        text: "使用日历饼图",
                        left: "center",
                        show: false
                    },
                    tooltip: {
                        formatter: "{b}: {c}"
                    },
                    legend: {
                        show: true,
                        top: "5%",
                        orient: "horizontal",
                        itemWidth: 25,
                        itemHeight: 14,
                        itemGap: 15
                    },
                    calendar: {
                        top: "middle",
                        left: "center",
                        cellSize: [60, 40],
                        range: ["MONTH_START", "MONTH_END"],
                        orient: "vertical",
                        dayLabel: {
                            show: true,
                            firstDay: 1,
                            nameMap: ["周日", "周一", "周二", "周三", "周四", "周五", "周六"],
                            color: "#333",
                            fontSize: 12,
                            position: "top"
                        },
                        itemStyle: {
                            borderWidth: 1,
                            borderColor: '#ccc',
                            color: '#f5f5f5'
                        },
                        splitLine: {
                            show: true,
                            lineStyle: {
                                color: '#ccc',
                                width: 1,
                                type: 'solid'
                            }
                        },
                        monthLabel: {
                            show: true
                        },
                        yearLabel: {
                            show: false
                        }
                    },
                    series: [
                        // 数据散点图 - 用于显示饼图
                        {
                            type: 'scatter',
                            coordinateSystem: 'calendar',
                            symbolSize: 0,
                            itemStyle: {
                                color: 'rgba(0, 0, 0, 0)'  // 透明色
                            },
                            data: CALENDAR_DATA_JSON
                        },
                        // 日期标签散点图 - 专门用于显示日期
                        {
                            type: 'scatter',
                            coordinateSystem: 'calendar',
                            symbolSize: 1,
                            symbol: 'circle',
                            zlevel: 2,  // 确保日期标签显示在饼图上方
                            label: {
                                show: true,
                                formatter: function(params) {
                                    // 获取日期的天数部分
                                    var date = new Date(params.value[0]);
                                    return date.getDate();
                                },
                                color: '#333',
                                position: 'inside',
                                fontSize: 14,
                                fontWeight: 'bold',
                                distance: 0,
                                align: 'center',
                                verticalAlign: 'middle',
                                backgroundColor: 'rgba(255, 255, 255, 0.6)',
                                borderRadius: 10,
                                padding: [2, 2, 2, 2],
                                emphasis: {
                                    show: true,
                                    color: '#000'
                                }
                            },
                            itemStyle: {
                                color: 'rgba(0, 0, 0, 0)'  // 透明色
                            },
                            // 生成当月所有日期的数据
                            data: (function() {
                                var data = [];
                                var date = new Date('MONTH_START');
                                var year = date.getFullYear();
                                var month = date.getMonth();
                                var lastDay = new Date(year, month + 1, 0).getDate();
                                
                                for (var i = 1; i <= lastDay; i++) {
                                    // 确保日期格式正确，使用两位数表示月和日
                                    var monthStr = (month + 1).toString().padStart(2, '0');
                                    var dayStr = i.toString().padStart(2, '0');
                                    var dateStr = year + '-' + monthStr + '-' + dayStr;
                                    data.push([dateStr, 0]);
                                }
                                return data;
                            })()
                        }
                    ]
                };
        '''
        
        # 替换占位符
        calendar_config = calendar_config.replace('CALENDAR_DATA_JSON', calendar_data_json)
        # 确保月份开始和结束日期格式正确
        month_start_date = f"{current_month}-01"
        # 计算月份最后一天
        last_day = (datetime.strptime(month_start_date, "%Y-%m-%d").replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        month_end_date = last_day.strftime("%Y-%m-%d")
        calendar_config = calendar_config.replace('MONTH_START', month_start_date)
        calendar_config = calendar_config.replace('MONTH_END', month_end_date)
        
        # 饼图系列 - 使用普通字符串，避免嵌套f-string
        pie_series_code = '''
                // 添加饼图系列到option中
                var pieSeries = PIE_SERIES_JSON;
                for (var i = 0; i < pieSeries.length; i++) {
                    option.series.push(pieSeries[i]);
                }
                
                // 设置日期标签样式
                option.calendar.dayLabel.nameMap = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
                option.calendar.dayLabel.color = "#333";
                option.calendar.dayLabel.fontSize = 12;
                option.calendar.dayLabel.position = "left";
                
                // 确保日期标签显示在日历单元格中
                option.calendar.itemStyle.borderWidth = 1;
                option.calendar.itemStyle.borderColor = '#ccc';
                option.calendar.itemStyle.borderRadius = 0;
                
                chart.setOption(option);
            </script>
        </body>
        </html>
        '''
        
        # 替换饼图系列占位符
        pie_series_code = pie_series_code.replace('PIE_SERIES_JSON', pie_series_json)
        
        # 组合HTML内容
        html_content = html_head + calendar_config + pie_series_code
        
        # 保存HTML文件
        with open(calendar_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.usage_view.load(QUrl.fromLocalFile(os.path.abspath(calendar_path)))
    
    def update_target_chart(self):
        # 获取目标类型统计数据
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 查询目标类型、检测人员和检测方式的统计数据
        cursor.execute("""
        SELECT class_name, username, 
               CASE 
                   WHEN t.source = 'image_detections' THEN '图像检测'
                   WHEN t.source = 'video_detections' THEN '视频检测'
                   WHEN t.source = 'realtime_detections' THEN '实时检测'
               END as detection_type,
               COUNT(*) as count
        FROM (
            SELECT class_name, username, 'image_detections' as source FROM image_detections
            UNION ALL
            SELECT class_name, username, 'video_detections' as source FROM video_detections
            UNION ALL
            SELECT class_name, username, 'realtime_detections' as source FROM realtime_detections
        ) t
        GROUP BY class_name, username, detection_type
        ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        
        # 如果没有数据，生成模拟数据
        if not results:
            class_names = ["舰船", "潜艇", "航母", "驱逐舰", "护卫舰", "补给舰"]
            usernames = ["admin", "operator1", "operator2", "analyst"]
            detection_types = ["图像检测", "视频检测", "实时检测"]
            
            results = []
            for cls in class_names:
                for user in usernames:
                    for det_type in detection_types:
                        count = random.randint(5, 50)
                        results.append((cls, user, det_type, count))
        
        # 准备树图数据
        tree_data = []
        for class_name, username, detection_type, count in results:
            # 添加到树图数据
            found = False
            for item in tree_data:
                if item["name"] == class_name:
                    found = True
                    # 检查是否已有该用户
                    user_found = False
                    for child in item["children"]:
                        if child["name"] == username:
                            user_found = True
                            # 添加检测方式
                            child["children"].append({
                                "name": detection_type,
                                "value": count
                            })
                            break
                    
                    if not user_found:
                        # 添加新用户
                        item["children"].append({
                            "name": username,
                            "children": [{
                                "name": detection_type,
                                "value": count
                            }]
                        })
                    break
            
            if not found:
                # 添加新类别
                tree_data.append({
                    "name": class_name,
                    "children": [{
                        "name": username,
                        "children": [{
                            "name": detection_type,
                            "value": count
                        }]
                    }]
                })
        
        # 创建矩形树图
        treemap = (
            TreeMap(init_opts=opts.InitOpts(width="100%", height="600px", theme=ThemeType.LIGHT))
            .add(
                series_name="目标类型统计",
                data=tree_data,
                visual_min=5,
                visual_max=50,
                leaf_depth=3,
                roam=False,
                node_click=None,
                label_opts=opts.LabelOpts(position="inside", formatter="{b}\n{c}"),
                breadcrumb_opts=opts.TreeMapBreadcrumbOpts(is_show=False)
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="目标类型统计", pos_top="0", pos_left="center", is_show=False),
                legend_opts=opts.LegendOpts(is_show=False),
                tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}"),
            )
        )
        
        # 创建旭日图（使用相同数据）
        sunburst = (
            Sunburst(init_opts=opts.InitOpts(width="100%", height="600px", theme=ThemeType.LIGHT))
            .add(
                series_name="目标类型统计",
                data_pair=tree_data,
                radius=["10%", "95%"],  # 增大旭日图的半径范围
                node_click=None,
                label_opts=opts.LabelOpts(position="inside", formatter="{b}\n{c}"),
                itemstyle_opts=opts.ItemStyleOpts(
                    border_width=1,
                    border_color="rgba(255,255,255,.5)"
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="目标类型统计", pos_top="0", pos_left="center", is_show=False),
                legend_opts=opts.LegendOpts(is_show=False),
                tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}"),
            )
        )
        
        # 渲染树图
        treemap_path = "charts/stats_treemap_chart.html"
        treemap.render(treemap_path)
        fix_chart_html(treemap_path)
        
        # 渲染旭日图
        sunburst_path = "charts/stats_sunburst_chart.html"
        sunburst.render(sunburst_path)
        fix_chart_html(sunburst_path)
        
        # 创建HTML文件，包含两个图表和切换按钮的JavaScript
        # 读取树图和旭日图的HTML内容
        with open(treemap_path, 'r', encoding='utf-8') as f:
            treemap_html = f.read()
        
        with open(sunburst_path, 'r', encoding='utf-8') as f:
            sunburst_html = f.read()
            
        # 提取树图和旭日图的JavaScript代码
        import re
        # 提取树图的JavaScript代码
        treemap_chart_id = re.search(r'var chart_(\w+) = echarts.init', treemap_html)
        treemap_option = re.search(r'var option_(\w+) = (\{[\s\S]*?\});', treemap_html)
        
        # 提取旭日图的JavaScript代码
        sunburst_chart_id = re.search(r'var chart_(\w+) = echarts.init', sunburst_html)
        sunburst_option = re.search(r'var option_(\w+) = (\{[\s\S]*?\});', sunburst_html)
        
        # 构建完整的JavaScript代码
        treemap_js = ''
        if treemap_chart_id and treemap_option:
            treemap_js = f'''
            var chart_{treemap_chart_id.group(1)} = echarts.init(document.getElementById('treemap'), 'light', {{renderer: 'canvas'}});
            var option_{treemap_chart_id.group(1)} = {treemap_option.group(2)};
            chart_{treemap_chart_id.group(1)}.setOption(option_{treemap_chart_id.group(1)});
            '''
        
        sunburst_js = ''
        if sunburst_chart_id and sunburst_option:
            sunburst_js = f'''
            var chart_{sunburst_chart_id.group(1)} = echarts.init(document.getElementById('sunburst'), 'light', {{renderer: 'canvas'}});
            var option_{sunburst_chart_id.group(1)} = {sunburst_option.group(2)};
            chart_{sunburst_chart_id.group(1)}.setOption(option_{sunburst_chart_id.group(1)});
            '''
        
        combined_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>目标类型统计</title>
            <script src="./assets/echarts.min.js"></script>
            <style>
                .chart-container {{ height: 650px; width: 100%; }}
                .button-container {{ text-align: center; margin: 5px 0; }}
                button {{ padding: 5px 10px; margin: 0 5px; cursor: pointer; font-size: 14px; }}
                .active {{ background-color: #3498db; color: white; }}
                h2 {{ text-align: center; margin-top: 0; margin-bottom: 5px; font-size: 18px; }}
                body {{ display: flex; flex-direction: column; }}
                .chart-wrapper {{ flex: 1; display: flex; justify-content: center; align-items: center; }}
            </style>
        </head>
        <body>
            <!-- 隐藏图表标题 -->
            <div class="button-container">
                <button id="treemapBtn" onclick="showChart('treemap')">矩形树图</button>
                <button id="sunburstBtn" class="active" onclick="showChart('sunburst')">旭日图</button>
            </div>
            <div class="chart-wrapper">
                <div id="treemap" class="chart-container" style="display:none;"></div>
                <div id="sunburst" class="chart-container"></div>
            </div>
            
            <script type="text/javascript">
                // 树图脚本
                {treemap_js}
                
                // 旭日图脚本
                {sunburst_js}
                
                // 切换图表显示
                function showChart(chartType) {{                    
                    if (chartType === 'treemap') {{                        
                        document.getElementById('treemap').style.display = 'block';
                        document.getElementById('sunburst').style.display = 'none';
                        document.getElementById('treemapBtn').classList.add('active');
                        document.getElementById('sunburstBtn').classList.remove('active');
                    }} else {{                        
                        document.getElementById('treemap').style.display = 'none';
                        document.getElementById('sunburst').style.display = 'block';
                        document.getElementById('treemapBtn').classList.remove('active');
                        document.getElementById('sunburstBtn').classList.add('active');
                    }}
                    
                    // 调整图表大小以适应容器
                    if (chartType === 'treemap') {{
                        chart_{treemap_chart_id.group(1)}.resize();
                    }} else {{
                        chart_{sunburst_chart_id.group(1)}.resize();
                    }}
                }}
                
                // 默认显示旭日图
                showChart('sunburst');
                
                // 自动切换图表显示（每5秒切换一次）
                let currentOption = 'sunburst';
                setInterval(function() {{
                    currentOption = currentOption === 'treemap' ? 'sunburst' : 'treemap';
                    showChart(currentOption);
                }}, 5000);
                
                // 窗口大小变化时调整图表大小
                window.addEventListener('resize', function() {{
                    chart_{treemap_chart_id.group(1)}.resize();
                    chart_{sunburst_chart_id.group(1)}.resize();
                }});
            </script>
        </body>
        </html>
        """
        
        # 保存组合HTML文件
        combined_path = "charts/stats_target_combined.html"
        with open(combined_path, "w", encoding="utf-8") as f:
            f.write(combined_html)
        
        # 加载组合图表
        self.target_view.load(QUrl.fromLocalFile(os.path.abspath(combined_path)))
    
    def update_personnel_chart(self):
        # 获取检测人员统计数据
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 查询每个用户的检测次数
        cursor.execute("""
        SELECT username, COUNT(*) as count FROM (
            SELECT username FROM image_detections
            UNION ALL
            SELECT username FROM video_detections
            UNION ALL
            SELECT username FROM realtime_detections
        )
        GROUP BY username
        ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        
        # 如果没有数据，生成模拟数据
        if not results:
            usernames = ["admin", "operator1", "operator2", "analyst", "guest"]
            results = [(name, random.randint(20, 100)) for name in usernames]
        
        # 准备饼图数据
        data_pair = [(username, count) for username, count in results]
        
        # 创建饼图
        pie = (
            Pie(init_opts=opts.InitOpts(width="100%", height="300px", theme=ThemeType.LIGHT))
            .add(
                series_name="检测次数",
                data_pair=data_pair,
                radius=["40%", "70%"],
                center=["50%", "50%"],
                rosetype="radius",
                label_opts=opts.LabelOpts(
                    position="outside",
                    formatter="{b}: {c}人次",
                    font_size=12,
                    font_style="normal",
                    font_weight="bold"
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="item", 
                    formatter="{a} <br/>{b}: {c}人次 ({d}%)"
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="检测人员统计", pos_left="center", is_show=False),
                legend_opts=opts.LegendOpts(
                    orient="vertical", 
                    pos_right="5%", 
                    pos_top="middle",
                    item_width=25,
                    item_height=14,
                    item_gap=10,
                    textstyle_opts=opts.TextStyleOpts(font_size=12)
                ),
            )
            .set_series_opts(
                label_opts=opts.LabelOpts(formatter="{b}: {c}"),
                itemstyle_opts=opts.ItemStyleOpts(
                    border_color="#fff",
                    border_width=1,
                )
            )
        )
        
        # 渲染图表
        pie_path = "charts/stats_personnel_chart.html"
        pie.render(pie_path)
        fix_chart_html(pie_path)
        self.personnel_view.load(QUrl.fromLocalFile(os.path.abspath(pie_path)))
    
    def update_method_chart(self):
        # 获取检测方式统计数据
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 查询各种检测方式的次数
        cursor.execute("""
        SELECT 
            'image_detections' as source, COUNT(*) as count FROM image_detections
        UNION ALL
        SELECT 
            'video_detections' as source, COUNT(*) as count FROM video_detections
        UNION ALL
        SELECT 
            'realtime_detections' as source, COUNT(*) as count FROM realtime_detections
        """)
        
        results = cursor.fetchall()
        
        # 如果没有数据，生成模拟数据
        if not results or all(count == 0 for _, count in results):
            results = [
                ("image_detections", random.randint(50, 150)),
                ("video_detections", random.randint(30, 100)),
                ("realtime_detections", random.randint(20, 80))
            ]
        
        # 准备柱状图数据
        categories = ["图像检测" if src == "image_detections" else 
                     "视频检测" if src == "video_detections" else 
                     "实时检测" for src, _ in results]
        values = [count for _, count in results]
        
        # 创建柱状图
        bar = (
            Bar(init_opts=opts.InitOpts(width="100%", height="300px", theme=ThemeType.LIGHT))
            .add_xaxis(categories)
            .add_yaxis(
                "检测次数", 
                values,
                category_gap="50%",
                label_opts=opts.LabelOpts(position="top", formatter="{c}次"),
                itemstyle_opts=opts.ItemStyleOpts(
                    color=JsCode("""
                    function(params) {
                        var colorList = ['#5470c6', '#91cc75', '#fac858'];
                        return colorList[params.dataIndex];
                    }
                    """),
                    border_radius=[5, 5, 0, 0]
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="检测方式统计", pos_left="center", is_show=False),
                tooltip_opts=opts.TooltipOpts(trigger="axis", formatter="{b}: {c}次"),
                toolbox_opts=opts.ToolboxOpts(
                    is_show=True,
                    feature={
                        "dataZoom": {"yAxisIndex": "none"},
                        "dataView": {"readOnly": False},
                        "restore": {},
                        "saveAsImage": {}
                    }
                ),
                legend_opts=opts.LegendOpts(is_show=False),
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(rotate=0, font_size=12, font_weight="bold"),
                    axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(width=2))
                ),
                yaxis_opts=opts.AxisOpts(
                    name="检测次数",
                    name_location="middle",
                    name_gap=35,
                    name_textstyle_opts=opts.TextStyleOpts(font_size=14),
                    splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dashed"))
                ),
            )
            .set_series_opts(
                markpoint_opts=opts.MarkPointOpts(
                    data=[
                        opts.MarkPointItem(type_="max", name="最大值"),
                        opts.MarkPointItem(type_="min", name="最小值")
                    ]
                )
            )
        )
        
        # 渲染图表
        bar_path = "charts/stats_method_chart.html"
        bar.render(bar_path)
        fix_chart_html(bar_path)
        self.method_view.load(QUrl.fromLocalFile(os.path.abspath(bar_path)))