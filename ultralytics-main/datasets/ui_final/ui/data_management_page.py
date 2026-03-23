from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QLineEdit, QHeaderView, QMessageBox, QCheckBox, QAbstractItemView
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime, timedelta
from ui.data_dialogs import AddDataDialog, ImportDataDialog, ExportDataDialog, ViewDataDialog

class DataManagementPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        title_label = QLabel("数据管理")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建搜索和过滤区域
        filter_widget = QWidget()
        filter_widget.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        filter_layout = QHBoxLayout(filter_widget)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索数据...")
        self.search_input.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        filter_layout.addWidget(self.search_input)
        
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
        from PySide6.QtWidgets import QDateEdit
        from PySide6.QtCore import QDate
        
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
        
        # 搜索按钮
        search_btn = QPushButton("搜索")
        search_btn.setStyleSheet("""
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
        search_btn.clicked.connect(self.load_detection_data)
        filter_layout.addWidget(search_btn)
        
        main_layout.addWidget(filter_widget)
        
        # 数据操作按钮区域
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 10, 0, 10)
        
        # 添加数据按钮
        add_btn = QPushButton("添加数据")
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self.add_data)
        action_layout.addWidget(add_btn)
        
        # 导入数据按钮
        import_btn = QPushButton("导入数据")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        import_btn.clicked.connect(self.import_data)
        action_layout.addWidget(import_btn)
        
        # 导出数据按钮
        export_btn = QPushButton("导出数据")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        export_btn.clicked.connect(self.export_data)
        action_layout.addWidget(export_btn)
        
        # 删除数据按钮
        delete_btn = QPushButton("删除数据")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected_data)
        action_layout.addWidget(delete_btn)
        
        action_layout.addStretch()
        main_layout.addWidget(action_widget)
        
        # 数据表格
        self.data_table = QTableWidget()
        self.data_table.setStyleSheet("background-color: white; border-radius: 8px;")
        self.data_table.setColumnCount(8)  # 增加一列用于复选框
        self.data_table.setHorizontalHeaderLabels(["选择", "ID", "用户名", "检测类型", "目标类型", "置信度", "时间", "操作"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 复选框列宽自适应
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选择整行
        self.data_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # 数据库连接
        from db.detection_db import DetectionDatabase
        self.db = DetectionDatabase.get_instance()
        
        main_layout.addWidget(self.data_table)
    
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
        
        # 加载检测数据
        self.load_detection_data()
    
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
    
    def load_detection_data(self):
        """加载检测数据"""
        if not hasattr(self, 'current_username') or not self.current_username:
            # 如果用户未登录，不加载数据
            QMessageBox.information(self, "提示", "请先登录后再查看数据")
            return
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
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
            
            # 构建SQL查询
            queries = []
            
            # 根据检测类型筛选
            if detection_type == "全部" or detection_type == "图像检测":
                queries.append(f"""
                SELECT id, username, '图像检测' as detection_type, class_name, confidence, timestamp, image_path as path
                FROM image_detections
                WHERE 1=1 {user_filter} {target_filter} {time_condition}
                """)
            
            if detection_type == "全部" or detection_type == "视频检测":
                queries.append(f"""
                SELECT id, username, '视频检测' as detection_type, class_name, confidence, timestamp, video_path as path
                FROM video_detections
                WHERE 1=1 {user_filter} {target_filter} {time_condition}
                """)
            
            if detection_type == "全部" or detection_type == "实时检测":
                queries.append(f"""
                SELECT id, username, '实时检测' as detection_type, class_name, confidence, timestamp, camera_id as path
                FROM realtime_detections
                WHERE 1=1 {user_filter} {target_filter} {time_condition}
                """)
            
            # 合并查询并按时间排序
            full_query = " UNION ".join(queries) + " ORDER BY timestamp DESC"
            
            # 执行查询
            cursor.execute(full_query)
            results = cursor.fetchall()
            
            # 更新表格
            self.data_table.setRowCount(len(results))
            
            for row, data in enumerate(results):
                # 添加复选框
                checkbox = QCheckBox()
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.data_table.setCellWidget(row, 0, checkbox_widget)
                
                # 数据顺序: id, username, detection_type, class_name, confidence, timestamp, path
                for col, value in enumerate(data[:6]):  # 不显示路径
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    # 存储数据ID和检测类型，用于后续操作
                    if col == 0:  # ID列
                        item.setData(Qt.UserRole, data[0])  # 存储ID
                        item.setData(Qt.UserRole + 1, data[2])  # 存储检测类型
                    self.data_table.setItem(row, col + 1, item)  # +1是因为第一列是复选框
                
                # 添加操作按钮
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 0, 5, 0)
                
                view_btn = QPushButton("查看")
                view_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border-radius: 4px;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                """)
                view_btn.clicked.connect(lambda checked=False, r=row: self.view_data(r))
                
                delete_btn = QPushButton("删除")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        border-radius: 4px;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        background-color: #c0392b;
                    }
                """)
                delete_btn.clicked.connect(lambda checked=False, r=row: self.delete_data(r))
                
                action_layout.addWidget(view_btn)
                action_layout.addWidget(delete_btn)
                
                self.data_table.setCellWidget(row, 7, action_widget)  # 第8列是操作列
            
            # 更新状态信息
            if len(results) == 0:
                QMessageBox.information(self, "提示", "没有找到符合条件的检测数据")
        
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载检测数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def add_data(self):
        """添加数据"""
        if not hasattr(self, 'current_username') or not self.current_username:
            QMessageBox.information(self, "提示", "请先登录后再添加数据")
            return
        
        # 创建添加数据对话框
        dialog = AddDataDialog(self.db, self)
        dialog.username_input.setText(self.current_username)
        
        # 如果对话框被接受（用户点击了保存按钮）
        if dialog.exec_():
            # 重新加载数据以显示新添加的内容
            self.load_detection_data()
    
    def import_data(self):
        """导入数据"""
        if not hasattr(self, 'current_username') or not self.current_username:
            QMessageBox.information(self, "提示", "请先登录后再导入数据")
            return
        
        # 创建导入数据对话框
        dialog = ImportDataDialog(self.db, self)
        dialog.username_input.setText(self.current_username)
        
        # 如果对话框被接受
        if dialog.exec_():
            # 重新加载数据以显示导入的内容
            self.load_detection_data()
    
    def export_data(self):
        """导出数据"""
        if not hasattr(self, 'current_username') or not self.current_username:
            QMessageBox.information(self, "提示", "请先登录后再导出数据")
            return
        
        # 获取当前筛选条件下的查询
        detection_type = self.detection_type_combo.currentText()
        target_type = self.target_type_combo.currentText()
        time_condition = self.get_time_filter_condition()
        
        # 用户筛选条件
        user_filter = ""
        if self.current_role != "管理员":
            user_filter = f"AND username = '{self.current_username}'"
        else:
            selected_user = self.user_combo.currentText()
            if selected_user != "全部用户":
                user_filter = f"AND username = '{selected_user}'"
        
        # 目标类型筛选
        target_filter = ""
        if target_type != "全部类型":
            target_filter = f"AND class_name = '{target_type}'"
        
        # 构建SQL查询
        queries = []
        
        # 根据检测类型筛选
        if detection_type == "全部" or detection_type == "图像检测":
            queries.append(f"""
            SELECT id, username, '图像检测' as detection_type, class_name, confidence, timestamp, image_path as path
            FROM image_detections
            WHERE 1=1 {user_filter} {target_filter} {time_condition}
            """)
        
        if detection_type == "全部" or detection_type == "视频检测":
            queries.append(f"""
            SELECT id, username, '视频检测' as detection_type, class_name, confidence, timestamp, video_path as path
            FROM video_detections
            WHERE 1=1 {user_filter} {target_filter} {time_condition}
            """)
        
        if detection_type == "全部" or detection_type == "实时检测":
            queries.append(f"""
            SELECT id, username, '实时检测' as detection_type, class_name, confidence, timestamp, camera_id as path
            FROM realtime_detections
            WHERE 1=1 {user_filter} {target_filter} {time_condition}
            """)
        
        # 合并查询
        current_filter = " UNION ".join(queries) + " ORDER BY timestamp DESC"
        
        # 创建导出数据对话框
        dialog = ExportDataDialog(self.db, current_filter, self)
        dialog.exec_()
    
    def delete_selected_data(self):
        """删除选中的数据"""
        if not hasattr(self, 'current_username') or not self.current_username:
            QMessageBox.information(self, "提示", "请先登录后再删除数据")
            return
        
        # 获取所有选中的行
        selected_rows = []
        for row in range(self.data_table.rowCount()):
            checkbox_widget = self.data_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox_layout = checkbox_widget.layout()
                checkbox = checkbox_layout.itemAt(0).widget()
                if checkbox.isChecked():
                    selected_rows.append(row)
        
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择要删除的数据")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除选中的 {len(selected_rows)} 条数据吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                # 删除选中的数据
                for row in selected_rows:
                    id_item = self.data_table.item(row, 1)  # ID列
                    detection_type = self.data_table.item(row, 3).text()  # 检测类型列
                    
                    data_id = id_item.data(Qt.UserRole)  # 获取存储的ID
                    
                    # 根据检测类型删除数据
                    if detection_type == "图像检测":
                        cursor.execute("DELETE FROM image_detections WHERE id = ?", (data_id,))
                    elif detection_type == "视频检测":
                        cursor.execute("DELETE FROM video_detections WHERE id = ?", (data_id,))
                    elif detection_type == "实时检测":
                        cursor.execute("DELETE FROM realtime_detections WHERE id = ?", (data_id,))
                
                conn.commit()
                QMessageBox.information(self, "成功", f"成功删除 {len(selected_rows)} 条数据")
                
                # 重新加载数据
                self.load_detection_data()
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"删除数据时出错: {str(e)}")
                import traceback
                traceback.print_exc()
    
    def view_data(self, row):
        """查看数据详情"""
        try:
            # 获取数据ID和检测类型
            id_item = self.data_table.item(row, 1)  # ID列
            data_id = id_item.text()
            detection_type = self.data_table.item(row, 3).text()  # 检测类型列
            
            # 创建查看数据对话框 - 修正参数顺序：先data_id，再detection_type
            dialog = ViewDataDialog(self.db, data_id, detection_type, self)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"查看数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def delete_data(self, row):
        """删除单条数据"""
        try:
            # 获取数据ID和检测类型
            id_item = self.data_table.item(row, 1)  # ID列
            data_id = id_item.text()
            detection_type = self.data_table.item(row, 3).text()  # 检测类型列
            
            # 确认删除
            reply = QMessageBox.question(
                self, "确认删除", f"确定要删除ID为 {data_id} 的{detection_type}数据吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                # 根据检测类型删除数据
                if detection_type == "图像检测":
                    cursor.execute("DELETE FROM image_detections WHERE id = ?", (data_id,))
                elif detection_type == "视频检测":
                    cursor.execute("DELETE FROM video_detections WHERE id = ?", (data_id,))
                elif detection_type == "实时检测":
                    cursor.execute("DELETE FROM realtime_detections WHERE id = ?", (data_id,))
                
                conn.commit()
                QMessageBox.information(self, "成功", "数据已成功删除")
                
                # 重新加载数据
                self.load_detection_data()
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"删除数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()