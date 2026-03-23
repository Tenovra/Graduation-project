from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QComboBox, QPushButton, QFileDialog, QMessageBox, 
                             QTableWidget, QTableWidgetItem, QCheckBox, QDateTimeEdit,
                             QSpinBox, QDoubleSpinBox, QHeaderView, QGroupBox, QFormLayout)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont
import csv
import os
from datetime import datetime

class AddDataDialog(QDialog):
    """添加数据对话框"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("添加数据")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 用户名
        self.username_input = QLineEdit()
        form_layout.addRow("用户名:", self.username_input)
        
        # 检测类型
        self.detection_type_combo = QComboBox()
        self.detection_type_combo.addItems(["图像检测", "视频检测", "实时检测"])
        self.detection_type_combo.currentIndexChanged.connect(self.on_detection_type_changed)
        form_layout.addRow("检测类型:", self.detection_type_combo)
        
        # 目标类型
        self.target_type_input = QLineEdit()
        form_layout.addRow("目标类型:", self.target_type_input)
        
        # 目标个数
        self.target_count_spin = QSpinBox()
        self.target_count_spin.setRange(1, 1000)
        self.target_count_spin.setValue(1)
        form_layout.addRow("目标个数:", self.target_count_spin)
        
        # 置信度
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.01, 1.0)
        self.confidence_spin.setValue(0.5)
        self.confidence_spin.setSingleStep(0.01)
        form_layout.addRow("置信度:", self.confidence_spin)
        
        # 文件位置
        self.file_path_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_layout.addWidget(self.file_path_input)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_file)
        self.file_path_layout.addWidget(self.browse_btn)
        
        form_layout.addRow("文件位置:", self.file_path_layout)
        
        # 时间
        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        form_layout.addRow("时间:", self.datetime_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.setStyleSheet("""
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
        self.save_btn.clicked.connect(self.save_data)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
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
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def on_detection_type_changed(self, index):
        """检测类型变化时的处理"""
        detection_type = self.detection_type_combo.currentText()
        if detection_type == "图像检测":
            self.browse_btn.clicked.disconnect()
            self.browse_btn.clicked.connect(self.browse_image)
        elif detection_type == "视频检测":
            self.browse_btn.clicked.disconnect()
            self.browse_btn.clicked.connect(self.browse_video)
        else:  # 实时检测
            self.browse_btn.clicked.disconnect()
            self.browse_btn.clicked.connect(self.browse_camera)
    
    def browse_file(self):
        """浏览文件"""
        detection_type = self.detection_type_combo.currentText()
        if detection_type == "图像检测":
            self.browse_image()
        elif detection_type == "视频检测":
            self.browse_video()
        else:  # 实时检测
            self.browse_camera()
    
    def browse_image(self):
        """浏览图像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图像文件", "", "图像文件 (*.jpg *.jpeg *.png *.bmp)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
    
    def browse_video(self):
        """浏览视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", "视频文件 (*.mp4 *.avi *.mov)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
    
    def browse_camera(self):
        """设置摄像头ID"""
        self.file_path_input.setText("camera_0")  # 默认摄像头ID
    
    def save_data(self):
        """保存数据"""
        # 获取输入数据
        username = self.username_input.text().strip()
        detection_type = self.detection_type_combo.currentText()
        target_type = self.target_type_input.text().strip()
        target_count = self.target_count_spin.value()
        confidence = self.confidence_spin.value()
        file_path = self.file_path_input.text().strip()
        timestamp = self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        
        # 验证输入
        if not username:
            QMessageBox.warning(self, "输入错误", "请输入用户名")
            return
        
        if not target_type:
            QMessageBox.warning(self, "输入错误", "请输入目标类型")
            return
        
        if not file_path:
            QMessageBox.warning(self, "输入错误", "请输入文件位置")
            return
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # 根据检测类型保存到不同的表
            if detection_type == "图像检测":
                for _ in range(target_count):
                    cursor.execute("""
                    INSERT INTO image_detections 
                    (username, timestamp, image_path, class_name, confidence, bbox_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (username, timestamp, file_path, target_type, str(confidence), 'rect'))
            
            elif detection_type == "视频检测":
                for i in range(target_count):
                    cursor.execute("""
                    INSERT INTO video_detections 
                    (username, timestamp, video_path, frame_number, class_name, confidence, bbox_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (username, timestamp, file_path, i, target_type, str(confidence), 'rect'))
            
            else:  # 实时检测
                for _ in range(target_count):
                    cursor.execute("""
                    INSERT INTO realtime_detections 
                    (username, timestamp, camera_id, class_name, confidence, bbox_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (username, timestamp, file_path, target_type, str(confidence), 'rect'))
            
            conn.commit()
            QMessageBox.information(self, "成功", "数据添加成功！")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存数据时出错: {str(e)}")


class ImportDataDialog(QDialog):
    """导入数据对话框"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("导入数据")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 说明标签
        info_label = QLabel("请选择要导入的CSV文件。CSV文件应包含以下列：\n"
                           "用户名,检测类型,目标类型,目标个数,置信度,文件位置,时间")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 用户名输入
        user_layout = QHBoxLayout()
        user_label = QLabel("用户名:")
        user_layout.addWidget(user_label)
        
        self.username_input = QLineEdit()
        self.username_input.setReadOnly(True)  # 设置为只读，由系统自动填充当前用户名
        user_layout.addWidget(self.username_input)
        
        layout.addLayout(user_layout)
        
        # 文件选择
        file_layout = QHBoxLayout()
        
        self.file_path_input = QLineEdit()
        file_layout.addWidget(self.file_path_input)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        # 检测类型选择
        type_group = QGroupBox("导入到哪种检测类型")
        type_layout = QVBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["根据CSV文件内容", "图像检测", "视频检测", "实时检测"])
        type_layout.addWidget(self.type_combo)
        
        layout.addWidget(type_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        import_btn = QPushButton("导入")
        import_btn.setStyleSheet("""
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
        import_btn.clicked.connect(self.import_data)
        button_layout.addWidget(import_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
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
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def browse_file(self):
        """浏览CSV文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", "", "CSV文件 (*.csv)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
    
    def import_data(self):
        """导入数据"""
        file_path = self.file_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "输入错误", "请选择CSV文件")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "文件错误", "所选文件不存在")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # 读取表头
                
                # 验证CSV格式
                expected_headers = ["用户名", "检测类型", "目标类型", "目标个数", "置信度", "文件位置", "时间"]
                if len(header) < len(expected_headers):
                    QMessageBox.warning(self, "格式错误", f"CSV文件格式不正确，应包含以下列：{', '.join(expected_headers)}")
                    return
                
                # 读取数据
                data = []
                for row in reader:
                    if len(row) >= len(expected_headers):
                        data.append(row)
                
                if not data:
                    QMessageBox.warning(self, "数据错误", "CSV文件中没有数据")
                    return
                
                # 导入数据
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                force_type = self.type_combo.currentText()
                imported_count = 0
                
                for row in data:
                    username = row[0].strip()
                    detection_type = row[1].strip() if force_type == "根据CSV文件内容" else force_type
                    target_type = row[2].strip()
                    target_count = int(row[3])
                    confidence = float(row[4])
                    file_path = row[5].strip()
                    timestamp = row[6].strip()
                    
                    # 验证时间格式
                    try:
                        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 根据检测类型保存到不同的表
                    if detection_type == "图像检测":
                        for _ in range(target_count):
                            cursor.execute("""
                            INSERT INTO image_detections 
                            (username, timestamp, image_path, class_name, confidence, bbox_type)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """, (username, timestamp, file_path, target_type, str(confidence), 'rect'))
                            imported_count += 1
                    
                    elif detection_type == "视频检测":
                        for i in range(target_count):
                            cursor.execute("""
                            INSERT INTO video_detections 
                            (username, timestamp, video_path, frame_number, class_name, confidence, bbox_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (username, timestamp, file_path, i, target_type, str(confidence), 'rect'))
                            imported_count += 1
                    
                    elif detection_type == "实时检测":
                        for _ in range(target_count):
                            cursor.execute("""
                            INSERT INTO realtime_detections 
                            (username, timestamp, camera_id, class_name, confidence, bbox_type)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """, (username, timestamp, file_path, target_type, str(confidence), 'rect'))
                            imported_count += 1
                
                conn.commit()
                QMessageBox.information(self, "成功", f"成功导入 {imported_count} 条数据！")
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入数据时出错: {str(e)}")


class ExportDataDialog(QDialog):
    """导出数据对话框"""
    def __init__(self, db, current_filter, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_filter = current_filter  # 当前筛选条件
        self.setWindowTitle("导出数据")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 导出选项
        options_group = QGroupBox("导出选项")
        options_layout = QVBoxLayout(options_group)
        
        self.current_filter_check = QCheckBox("使用当前筛选条件")
        self.current_filter_check.setChecked(True)
        options_layout.addWidget(self.current_filter_check)
        
        self.include_header_check = QCheckBox("包含表头")
        self.include_header_check.setChecked(True)
        options_layout.addWidget(self.include_header_check)
        
        layout.addWidget(options_group)
        
        # 文件选择
        file_layout = QHBoxLayout()
        
        file_label = QLabel("保存到:")
        file_layout.addWidget(file_label)
        
        self.file_path_input = QLineEdit()
        file_layout.addWidget(self.file_path_input)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("导出")
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
        button_layout.addWidget(export_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
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
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def browse_file(self):
        """选择保存文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存CSV文件", "", "CSV文件 (*.csv)"
        )
        if file_path:
            if not file_path.endswith('.csv'):
                file_path += '.csv'
            self.file_path_input.setText(file_path)
    
    def export_data(self):
        """导出数据"""
        file_path = self.file_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "输入错误", "请选择保存文件路径")
            return
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # 构建查询
            if self.current_filter_check.isChecked() and self.current_filter:
                # 使用当前筛选条件
                query = self.current_filter
            else:
                # 不使用筛选条件，导出所有数据
                queries = [
                    """SELECT id, username, '图像检测' as detection_type, class_name, confidence, timestamp, image_path as path FROM image_detections""",
                    """SELECT id, username, '视频检测' as detection_type, class_name, confidence, timestamp, video_path as path FROM video_detections""",
                    """SELECT id, username, '实时检测' as detection_type, class_name, confidence, timestamp, camera_id as path FROM realtime_detections"""
                ]
                query = " UNION ".join(queries) + " ORDER BY timestamp DESC"
            
            # 执行查询
            cursor.execute(query)
            results = cursor.fetchall()
            
            if not results:
                QMessageBox.warning(self, "数据错误", "没有数据可导出")
                return
            
            # 写入CSV文件
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入表头
                if self.include_header_check.isChecked():
                    writer.writerow(["ID", "用户名", "检测类型", "目标类型", "置信度", "时间", "文件位置"])
                
                # 写入数据
                for row in results:
                    writer.writerow(row)
            
            QMessageBox.information(self, "成功", f"成功导出 {len(results)} 条数据到 {file_path}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出数据时出错: {str(e)}")


class ViewDataDialog(QDialog):
    """查看数据详情对话框"""
    def __init__(self, db, data_id, detection_type, parent=None):
        super().__init__(parent)
        self.db = db
        self.data_id = data_id
        self.detection_type = detection_type
        self.setWindowTitle("数据详情")
        self.setMinimumSize(600, 400)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["字段", "值"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
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
        
        layout.addWidget(self.table)
        
        # 关闭按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
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
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_data(self):
        """加载数据详情"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # 根据检测类型查询不同的表
            if self.detection_type == "图像检测":
                cursor.execute("""
                SELECT id, username, timestamp, image_path, class_name, confidence, bbox_type, obb_points
                FROM image_detections
                WHERE id = ?
                """, (self.data_id,))
                columns = ["ID", "用户名", "时间", "图像路径", "目标类型", "置信度", "边界框类型", "OBB点坐标"]
            
            elif self.detection_type == "视频检测":
                cursor.execute("""
                SELECT id, username, timestamp, video_path, frame_number, class_name, confidence, bbox_type, obb_points
                FROM video_detections
                WHERE id = ?
                """, (self.data_id,))
                columns = ["ID", "用户名", "时间", "视频路径", "帧号", "目标类型", "置信度", "边界框类型", "OBB点坐标"]
            
            else:  # 实时检测
                cursor.execute("""
                SELECT id, username, timestamp, camera_id, class_name, confidence, bbox_type, obb_points
                FROM realtime_detections
                WHERE id = ?
                """, (self.data_id,))
                columns = ["ID", "用户名", "时间", "摄像头ID", "目标类型", "置信度", "边界框类型", "OBB点坐标"]
            
            result = cursor.fetchone()
            
            if result:
                # 设置表格行数
                self.table.setRowCount(len(result))
                
                # 填充表格
                for i, (value, column) in enumerate(zip(result, columns)):
                    # 字段名
                    field_item = QTableWidgetItem(column)
                    field_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    field_item.setFont(QFont("Arial", 10, QFont.Bold))
                    self.table.setItem(i, 0, field_item)
                    
                    # 值
                    value_item = QTableWidgetItem(str(value) if value is not None else "")
                    value_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.table.setItem(i, 1, value_item)
            else:
                # 显示更详细的错误信息
                error_msg = f"未找到指定的数据记录\n检测类型: {self.detection_type}\n数据ID: {self.data_id}"
                QMessageBox.warning(self, "数据错误", error_msg)
                # 确保对话框关闭
                self.close()
                return
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据时出错: {str(e)}")
            self.reject()