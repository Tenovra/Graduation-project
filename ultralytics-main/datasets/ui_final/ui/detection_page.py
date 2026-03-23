from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QFileDialog, QProgressBar, QMessageBox
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QPixmap, QImage
import os
import cv2
import numpy as np
from ultralytics import YOLO
import time
import torch
import threading
from datetime import datetime

class YOLOThread(QThread):
    """用于在后台运行YOLO检测的线程"""
    def __init__(self, model_path, image_path=None, image_paths=None, video_path=None, camera_id=None, username=None):
        super().__init__()
        self.model_path = model_path
        self.image_path = image_path
        self.image_paths = image_paths  # 新增：支持多图像路径列表
        self.video_path = video_path
        self.camera_id = camera_id
        self.username = username
        self.results = None
        self.running = True
        self.frame = None
        self.processed_frame = None
        self.fps = 0
        self.detection_count = 0
        self.error_message = ""  # 用于存储详细的错误信息
        self.current_image_index = 0  # 当前处理的图像索引
        self.total_images = len(image_paths) if image_paths else 0  # 总图像数量
        self.processed_results = []  # 存储所有处理结果
        self.frame_count = 0  # 视频帧计数
        
        # 初始化数据库连接
        try:
            from db.detection_db import DetectionDatabase
            self.db = DetectionDatabase.get_instance()
        except Exception as e:
            print(f"初始化检测数据库连接失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
    def __del__(self):
        """析构函数，确保线程资源被正确释放"""
        pass
            

    
    def run(self):
        try:
            
            # 检查模型文件是否存在
            if not os.path.exists(self.model_path):
                error_msg = f"模型文件不存在: {self.model_path}"
                print(f"错误: {error_msg}")
                self.error_message = error_msg
                return
                
            # 加载模型
            print(f"正在加载模型: {self.model_path}")
            try:
                self.model = YOLO(self.model_path)
                print(f"模型加载成功: {type(self.model)}")
            except Exception as model_err:
                error_msg = f"模型加载失败: {str(model_err)}"
                print(f"错误: {error_msg}")
                self.error_message = error_msg
                import traceback
                traceback.print_exc()
                return
            
            # 处理单个图像路径的情况
            if self.image_path:
                # 图像检测
                try:
                    print(f"开始检测图像: {self.image_path}")
                    # 检查图像是否存在
                    if not os.path.exists(self.image_path):
                        print(f"错误: 图像文件不存在: {self.image_path}")
                        self.results = None
                        return
                        
                    # 尝试读取图像以验证格式
                    try:
                        img = cv2.imread(self.image_path)
                        if img is None:
                            print(f"错误: 无法读取图像: {self.image_path}")
                            self.results = None
                            return
                        print(f"图像读取成功: 尺寸={img.shape}")
                    except Exception as img_err:
                        print(f"图像读取错误: {str(img_err)}")
                        self.results = None
                        return
                    
                    # 执行检测前的预处理
                    print(f"准备执行检测，图像路径: {self.image_path}")
                    
                    # 尝试使用不同的方式加载图像
                    try:
                        # 方法1: 直接使用路径
                        self.results = self.model(self.image_path)
                    except Exception as e1:
                        print(f"使用路径直接检测失败: {str(e1)}")
                        try:
                            # 方法2: 先用OpenCV加载，然后传递图像数组
                            img_array = cv2.imread(self.image_path)
                            if img_array is None:
                                raise ValueError("OpenCV无法读取图像")
                                
                            # 转换BGR到RGB (YOLO期望RGB格式)
                            img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                            print(f"使用OpenCV加载图像成功，尺寸: {img_rgb.shape}")
                            
                            # 使用图像数组进行检测
                            self.results = self.model(img_rgb)
                        except Exception as e2:
                            error_msg = f"图像预处理和检测失败: {str(e2)}"
                            print(error_msg)
                            self.error_message = error_msg
                            self.results = None
                            return
                    
                    # 确保结果不为空
                    if not self.results or len(self.results) == 0 or self.results[0] is None:
                        error_msg = "YOLO检测返回空结果"
                        print(f"警告: {error_msg}")
                        self.error_message = error_msg
                        self.results = None
                    else:
                        # 打印结果信息以便调试
                        result = self.results[0]
                        print(f"检测结果类型: {type(result)}")
                        print(f"检测结果属性: {dir(result)}")
                        
                        # 检查是否为OBB模型结果
                        if hasattr(result, 'obb') and result.obb is not None:
                            print("检测到图像的OBB模型结果")
                            # 处理OBB模型结果
                            try:
                                # 获取OBB模型的类别和置信度
                                if hasattr(result.obb, 'cls') and result.obb.cls is not None and len(result.obb.cls) > 0:
                                    classes = result.names
                                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    for i in range(len(result.obb.cls)):
                                        try:
                                            # 获取类别ID和名称
                                            cls_id = int(result.obb.cls[i].item())
                                            cls_name = classes[cls_id]
                                            
                                            # 获取置信度
                                            conf = float(result.obb.conf[i].item())
                                            conf_str = f"{conf:.2f}"
                                            
                                            # 获取旋转框坐标 (xyxyxyxy 格式)
                                            if hasattr(result.obb, 'xyxyxyxy') and result.obb.xyxyxyxy is not None:
                                                obb_points = result.obb.xyxyxyxy[i].tolist()
                                                
                                                # 保存检测结果到数据库
                                                if self.username:
                                                    try:
                                                        self.db.save_image_detection(
                                                            self.username,
                                                            self.image_path,
                                                            cls_name,
                                                            conf_str,
                                                            None,  # 矩形框为None
                                                            bbox_type='obb',
                                                            obb_points=obb_points
                                                        )
                                                        print(f"已保存图像检测结果到数据库: 用户={self.username}, 文件={self.image_path}, 类别={cls_name}, 置信度={conf_str}")
                                                    except Exception as db_err:
                                                        print(f"保存检测结果到数据库时出错: {str(db_err)}")
                                                        import traceback
                                                        traceback.print_exc()
                                        except Exception as e:
                                            print(f"处理OBB检测结果时出错: {str(e)}")
                                            import traceback
                                            traceback.print_exc()
                                print("OBB模型结果处理成功")
                            except Exception as obb_err:
                                print(f"OBB结果处理错误: {str(obb_err)}")
                                import traceback
                                traceback.print_exc()
                        # 检查是否有boxes属性
                        elif hasattr(result, 'boxes') and result.boxes is not None:
                            try:
                                boxes_count = len(result.boxes)
                                print(f"检测到的目标数量: {boxes_count}")
                                
                                # 处理boxes中的检测结果
                                classes = result.names
                            except TypeError as te:
                                error_msg = f"无法获取boxes长度: {str(te)}"
                                print(f"警告: {error_msg}")
                                self.error_message = error_msg
                        else:
                            error_msg = "结果对象没有boxes属性或obb属性，或者它们为None"
                            print(f"警告: {error_msg}")
                            self.error_message = error_msg
                except Exception as e:
                    error_msg = f"图像检测错误: {str(e)}"
                    print(error_msg)
                    import traceback
                    traceback.print_exc()
                    self.error_message = error_msg
                    self.results = None
            
            # 处理多个图像路径的情况
            elif self.image_paths and len(self.image_paths) > 0:
                self.processed_results = []
                self.total_images = len(self.image_paths)
                
                for idx, img_path in enumerate(self.image_paths):
                    if not self.running:
                        break
                        
                    self.current_image_index = idx
                    print(f"处理图像 {idx+1}/{self.total_images}: {img_path}")
                    
                    try:
                        # 检查图像是否存在
                        if not os.path.exists(img_path):
                            print(f"错误: 图像文件不存在: {img_path}")
                            self.processed_results.append({
                                "path": img_path,
                                "result": None,
                                "error": f"图像文件不存在: {img_path}"
                            })
                            continue
                            
                        # 尝试读取图像以验证格式
                        try:
                            img = cv2.imread(img_path)
                            if img is None:
                                print(f"错误: 无法读取图像: {img_path}")
                                self.processed_results.append({
                                    "path": img_path,
                                    "result": None,
                                    "error": f"无法读取图像: {img_path}"
                                })
                                continue
                            print(f"图像读取成功: 尺寸={img.shape}")
                        except Exception as img_err:
                            print(f"图像读取错误: {str(img_err)}")
                            self.processed_results.append({
                                "path": img_path,
                                "result": None,
                                "error": f"图像读取错误: {str(img_err)}"
                            })
                            continue
                        
                        # 执行检测
                        result = None
                        error = ""
                        
                        try:
                            # 方法1: 直接使用路径
                            result = self.model(img_path)
                        except Exception as e1:
                            print(f"使用路径直接检测失败: {str(e1)}")
                            try:
                                # 方法2: 先用OpenCV加载，然后传递图像数组
                                img_array = cv2.imread(img_path)
                                if img_array is None:
                                    raise ValueError("OpenCV无法读取图像")
                                    
                                # 转换BGR到RGB (YOLO期望RGB格式)
                                img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                                print(f"使用OpenCV加载图像成功，尺寸: {img_rgb.shape}")
                                
                                # 使用图像数组进行检测
                                result = self.model(img_rgb)
                            except Exception as e2:
                                error = f"图像预处理和检测失败: {str(e2)}"
                                print(error)
                        
                        # 处理结果
                        if not result or len(result) == 0 or result[0] is None:
                            error = "YOLO检测返回空结果"
                            print(f"警告: {error}")
                            self.processed_results.append({
                                "path": img_path,
                                "result": None,
                                "error": error
                            })
                        else:
                            # 保存结果
                            self.processed_results.append({
                                "path": img_path,
                                "result": result[0],
                                "error": ""
                            })
                            
                            # 更新当前结果用于显示
                            self.results = result
                            
                            # 打印结果信息
                            print(f"检测结果类型: {type(result[0])}")  
                            
                            # 保存检测结果到数据库
                            if self.username and hasattr(result[0], 'boxes') and result[0].boxes is not None:  # 确保有用户名和有效的检测结果
                                classes = result[0].names
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                for box in result[0].boxes:
                                    try:
                                        # 获取类别ID和名称
                                        cls_id = int(box.cls[0])
                                        cls_name = self.model.names.get(cls_id, "未知类别")
                                        
                                        # 获取置信度
                                        conf = f"{box.conf[0].item():.2f}"
                                        
                                        # 检查是否有旋转框坐标 (xyxyxyxy 格式)
                                        if hasattr(box, 'xyxyxyxy') and box.xyxyxyxy is not None and len(box.xyxyxyxy) > 0:
                                            # 获取旋转框坐标
                                            coords = [round(x) for x in box.xyxyxyxy[0].flatten().tolist()]
                                            obb_points = coords
                                        
                                            # 保存旋转框坐标到数据库
                                            self.db.save_image_detection(
                                                self.username,
                                                img_path,
                                                cls_name,
                                                conf,
                                                None,  # 矩形框为None
                                                bbox_type='obb',
                                                obb_points=obb_points
                                            )
                                            print(f"已保存OBB检测结果到数据库: 用户={self.username}, 文件={img_path}, 类别={cls_name}, 置信度={conf}")
                                        else:
                                            # 获取边界框坐标 (x1, y1, x2, y2 格式)
                                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                                            
                                            # 转换为 (x, y, width, height) 格式
                                            x, y = x1, y1
                                            width, height = x2 - x1, y2 - y1
                                            
                                            # 保存矩形框坐标到数据库
                                            self.db.save_image_detection(
                                                self.username,
                                                img_path,
                                                cls_name,
                                                conf,
                                                (x, y, width, height),  # 矩形框
                                                bbox_type='rect'
                                            )
                                            print(f"已保存矩形框检测结果到数据库: 用户={self.username}, 文件={img_path}, 类别={cls_name}, 置信度={conf}")
                                    except Exception as db_err:
                                        print(f"保存检测结果到数据库时出错: {str(db_err)}")
                                        import traceback
                                        traceback.print_exc()
                            
                            # 检查是否为OBB模型结果或有boxes属性
                            if hasattr(result[0], 'obb') and result[0].obb is not None:
                                print("检测到图像的OBB模型结果")
                                # 处理OBB模型结果
                                try:
                                    # 获取OBB模型的类别和置信度
                                    if hasattr(result[0].obb, 'cls') and result[0].obb.cls is not None and len(result[0].obb.cls) > 0:
                                        classes = result[0].names
                                        for i in range(len(result[0].obb.cls)):
                                            try:
                                                # 获取类别ID和名称
                                                cls_id = int(result[0].obb.cls[i].item())
                                                cls_name = classes[cls_id]
                                                
                                                # 获取置信度
                                                conf = float(result[0].obb.conf[i].item())
                                                
                                                # 获取旋转框坐标 (xyxyxyxy 格式)
                                                if hasattr(result[0].obb, 'xyxyxyxy') and result[0].obb.xyxyxyxy is not None:
                                                    obb_points = result[0].obb.xyxyxyxy[i].tolist()
                                                      
                                                    # 保存检测结果到数据库
                                                    if self.username:
                                                        try:
                                                            # 根据检测类型保存到对应的数据库表
                                                            if self.video_path:
                                                                self.db.save_video_detection(
                                                                    self.username,
                                                                    self.video_path,
                                                                    self.frame_count,
                                                                    cls_name,
                                                                    conf_str,
                                                                    None,  # 矩形框为None
                                                                    bbox_type='obb',
                                                                    obb_points=obb_points
                                                                )
                                                                print(f"正在保存视频检测结果到数据库: 用户={self.username}, 文件={self.video_path}, 类别={cls_name}, 置信度={conf_str}, 帧号={self.frame_count}")
                                                            elif self.camera_id is not None:
                                                                self.db.save_realtime_detection(
                                                                    self.username,
                                                                    str(self.camera_id),
                                                                    cls_name,
                                                                    conf_str,
                                                                    None,  # 矩形框为None
                                                                    bbox_type='obb',
                                                                    obb_points=obb_points
                                                                )
                                                                print(f"正在保存实时检测结果到数据库: 用户={self.username}, 摄像头ID={self.camera_id}, 类别={cls_name}, 置信度={conf_str}")
                                                        except Exception as db_err:
                                                            print(f"保存检测结果到数据库时出错: {str(db_err)}")
                                                            import traceback
                                                            traceback.print_exc()
                                            except Exception as e:
                                                print(f"处理OBB检测结果时出错: {str(e)}")
                                                import traceback
                                                traceback.print_exc()
                                    print("OBB模型结果处理成功")
                                except Exception as obb_err:
                                    print(f"OBB结果处理错误: {str(obb_err)}")
                                    import traceback
                                    traceback.print_exc()
                            elif hasattr(result[0], 'boxes') and result[0].boxes is not None:
                                try:
                                    boxes_count = len(result[0].boxes)
                                    print(f"检测到的目标数量: {boxes_count}")
                                except TypeError as te:
                                    print(f"警告: 无法获取boxes长度: {str(te)}")
                    except Exception as e:
                        error_msg = f"图像 {img_path} 检测错误: {str(e)}"
                        print(error_msg)
                        import traceback
                        traceback.print_exc()
                        self.processed_results.append({
                            "path": img_path,
                            "result": None,
                            "error": error_msg
                        })
                
                # 处理完所有图像后，如果有结果，将最后一个结果设为当前结果
                if self.processed_results and any(item["result"] is not None for item in self.processed_results):
                    for item in reversed(self.processed_results):
                        if item["result"] is not None:
                            self.results = [item["result"]]
                            break
                
            elif self.video_path or self.camera_id is not None:
                # 视频或摄像头检测
                cap = cv2.VideoCapture(self.camera_id if self.camera_id is not None else self.video_path)
                if not cap.isOpened():
                    return
                    
                prev_time = time.time()
                frame_count = 0
                
                while self.running:
                    ret, frame = cap.read()
                    if not ret:
                        if self.video_path:  # 如果是视频文件，播放结束后退出
                            break
                        continue
                        
                    self.frame = frame.copy()
                    
                    # 使用YOLO进行检测
                    try:
                        # 尝试检测
                        results = self.model(frame)
                        
                        # 处理结果 - 添加空值检查
                        if results and len(results) > 0 and results[0] is not None:
                            # 检查是否为OBB模型结果
                            if hasattr(results[0], 'obb') and results[0].obb is not None:
                                print("检测到视频帧的OBB模型结果")
                                # 使用OBB属性进行处理
                                try:
                                    # 在图像上绘制检测结果
                                    self.processed_frame = results[0].plot()
                                    
                                    # 获取OBB模型的类别和置信度
                                    if hasattr(results[0].obb, 'cls') and results[0].obb.cls is not None:
                                        self.detection_count = len(results[0].obb.cls)  # 更新检测到的目标数量
                                        classes = results[0].names
                                        
                                        # 保存OBB检测结果到数据库
                                        if self.username:  # 确保有用户名
                                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            for i in range(len(results[0].obb.cls)):
                                                try:
                                                    # 获取类别ID和名称
                                                    cls_id = int(results[0].obb.cls[i].item())
                                                    cls_name = classes[cls_id]
                                                    
                                                    # 获取置信度
                                                    conf = float(results[0].obb.conf[i].item())
                                                    conf_str = f"{conf:.2f}"
                                                    
                                                    # 获取旋转框坐标 (xyxyxyxy 格式)
                                                    if hasattr(results[0].obb, 'xyxyxyxy') and results[0].obb.xyxyxyxy is not None:
                                                        obb_points = results[0].obb.xyxyxyxy[i].tolist()
                                                        
                                                        # 根据检测类型保存到对应的数据库表
                                                        if self.video_path:
                                                            # 视频检测
                                                            self.db.save_video_detection(
                                                                self.username,
                                                                self.video_path,
                                                                self.frame_count,
                                                                cls_name,
                                                                conf_str,
                                                                None,  # 矩形框为None
                                                                bbox_type='obb',
                                                                obb_points=obb_points
                                                            )
                                                            print(f"已保存视频OBB检测结果到数据库: 用户={self.username}, 文件={self.video_path}, 类别={cls_name}, 置信度={conf_str}, 帧号={self.frame_count}")
                                                        elif self.camera_id is not None:
                                                            # 实时检测
                                                            self.db.save_realtime_detection(
                                                                self.username,
                                                                self.camera_id,
                                                                cls_name,
                                                                conf_str,
                                                                None,  # 矩形框为None
                                                                bbox_type='obb',
                                                                obb_points=obb_points
                                                            )
                                                            print(f"已保存实时OBB检测结果到数据库: 用户={self.username}, 摄像头ID={self.camera_id}, 类别={cls_name}, 置信度={conf_str}")
                                                except Exception as db_err:
                                                    print(f"保存OBB检测结果到数据库时出错: {str(db_err)}")
                                                    import traceback
                                                    traceback.print_exc()
                                    else:
                                        self.detection_count = 1  # OBB模型可能没有明确的目标数量
                                    
                                    self.error_message = ""
                                except Exception as obb_err:
                                    print(f"OBB结果处理错误: {str(obb_err)}")
                                    self.detection_count = 0
                                    self.processed_frame = frame.copy()
                                    cv2.putText(self.processed_frame, "OBB结果处理错误", (50, 50),
                                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                                    self.error_message = f"OBB结果处理错误: {str(obb_err)}"
                            # 检查是否有boxes属性
                            elif hasattr(results[0], 'boxes') and results[0].boxes is not None:
                                self.detection_count = len(results[0].boxes)
                                # 在图像上绘制检测结果
                                self.processed_frame = results[0].plot()
                                self.error_message = ""
                                
                                # 保存检测结果到数据库
                                if self.username:  # 确保有用户名
                                    self.frame_count += 1  # 增加帧计数
                                    classes = results[0].names
                                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    for box in results[0].boxes:
                                        try:
                                            # 获取类别ID和名称
                                            cls_id = int(box.cls[0])
                                            cls_name = self.model.names.get(cls_id, "未知类别")
                                            
                                            # 获取置信度
                                            conf = f"{box.conf[0].item():.2f}"
                                            
                                            # 根据检测类型保存到对应的数据库表
                                            if self.video_path:
                                                # 视频检测 - 检查是否有旋转框坐标
                                                if hasattr(box, 'xyxyxyxy') and box.xyxyxyxy is not None and len(box.xyxyxyxy) > 0:
                                                    # 获取旋转框坐标
                                                    coords = [round(x) for x in box.xyxyxyxy[0].flatten().tolist()]
                                                    obb_points = coords
                                                    
                                                    # 保存OBB检测结果
                                                    try:
                                                        print(f"正在保存视频OBB检测结果到数据库: 用户={self.username}, 文件={self.video_path}, 类别={cls_name}, 置信度={conf}, 帧号={self.frame_count}")
                                                        self.db.save_video_detection(
                                                            self.username,
                                                            self.video_path,
                                                            self.frame_count,
                                                            cls_name,
                                                            conf,
                                                            None,  # 矩形框为None
                                                            bbox_type='obb',
                                                            obb_points=obb_points
                                                        )
                                                        print(f"视频OBB检测结果保存成功: 类别={cls_name}, 置信度={conf}, 帧号={self.frame_count}")
                                                    except Exception as save_err:
                                                        print(f"保存视频OBB检测结果失败: {str(save_err)}")
                                                        import traceback
                                                        traceback.print_exc()
                                                else:
                                                    # 获取边界框坐标 (x1, y1, x2, y2 格式)
                                                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                                                    
                                                    # 转换为 (x, y, width, height) 格式
                                                    x, y = x1, y1
                                                    width, height = x2 - x1, y2 - y1
                                                    
                                                    # 保存矩形框检测结果
                                                    try:
                                                        print(f"正在保存视频矩形框检测结果到数据库: 用户={self.username}, 文件={self.video_path}, 类别={cls_name}, 置信度={conf}, 帧号={self.frame_count}")
                                                        self.db.save_video_detection(
                                                            self.username,
                                                            self.video_path,
                                                            self.frame_count,
                                                            cls_name,
                                                            conf,
                                                            (x, y, width, height),
                                                            bbox_type='rect'
                                                        )
                                                        print(f"视频矩形框检测结果保存成功: 类别={cls_name}, 置信度={conf}, 帧号={self.frame_count}")
                                                    except Exception as save_err:
                                                        print(f"保存视频矩形框检测结果失败: {str(save_err)}")
                                                        import traceback
                                                        traceback.print_exc()
                                            elif self.camera_id is not None:
                                                    # 实时检测
                                                    try:
                                                        if hasattr(box, 'xyxyxyxy') and box.xyxyxyxy is not None and len(box.xyxyxyxy) > 0:
                                                            # 获取旋转框坐标
                                                            coords = [round(x) for x in box.xyxyxyxy[0].flatten().tolist()]
                                                            obb_points = coords
                                                            
                                                            # 保存旋转框坐标到数据库
                                                            print(f"正在保存实时检测OBB结果到数据库: 用户={self.username}, 摄像头ID={self.camera_id}, 类别={cls_name}, 置信度={conf}")
                                                            self.db.save_realtime_detection(
                                                                self.username,
                                                                self.camera_id,
                                                                cls_name,
                                                                conf,
                                                                None,  # 矩形框为None
                                                                bbox_type='obb',
                                                                obb_points=obb_points
                                                            )
                                                            print(f"实时检测OBB结果保存成功: 类别={cls_name}, 置信度={conf}")
                                                        else:
                                                            # 保存矩形框坐标到数据库
                                                            print(f"正在保存实时检测矩形框结果到数据库: 用户={self.username}, 摄像头ID={self.camera_id}, 类别={cls_name}, 置信度={conf}")
                                                            self.db.save_realtime_detection(
                                                                self.username,
                                                                self.camera_id,
                                                                cls_name,
                                                                conf,
                                                                (x, y, width, height),  # 使用元组格式，而不是列表
                                                                bbox_type='rect'
                                                            )
                                                            print(f"实时检测矩形框结果保存成功: 类别={cls_name}, 置信度={conf}")
                                                    except Exception as save_err:
                                                        print(f"保存实时检测结果失败: {str(save_err)}")
                                                        import traceback
                                                        traceback.print_exc()
                                        except Exception as db_err:
                                            print(f"保存检测结果到数据库时出错: {str(db_err)}")
                                            import traceback
                                            traceback.print_exc()
                            else:
                                self.detection_count = 0
                                # 如果没有boxes属性，显示原始帧并添加错误文本
                                self.processed_frame = frame.copy()
                                cv2.putText(self.processed_frame, "检测结果无效(缺少boxes和obb属性)", (50, 50), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                                self.error_message = "检测结果无效: 缺少boxes和obb属性"
                        else:
                            self.detection_count = 0
                            # 如果检测失败，显示原始帧并添加错误文本
                            self.processed_frame = frame.copy()
                            cv2.putText(self.processed_frame, "未检测到目标", (50, 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            self.error_message = "未检测到目标"
                    except Exception as detect_err:
                        self.detection_count = 0
                        # 如果检测过程出错，显示原始帧并添加错误文本
                        self.processed_frame = frame.copy()
                        cv2.putText(self.processed_frame, f"检测错误", (50, 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        self.error_message = f"检测错误: {str(detect_err)}"
                        print(f"视频帧检测错误: {str(detect_err)}")
                        import traceback
                        traceback.print_exc()
                    
                    # 计算FPS
                    frame_count += 1
                    current_time = time.time()
                    if current_time - prev_time >= 1.0:
                        self.fps = frame_count / (current_time - prev_time)
                        frame_count = 0
                        prev_time = current_time
                
                cap.release()
        except Exception as e:
            error_msg = f"YOLO检测错误: {str(e)}"
            print(error_msg)
            self.error_message = error_msg
            import traceback
            traceback.print_exc()
        finally:
            # 检测完成后的处理
            print("\n===== 检测完成 =====\n")

    def stop(self):
        self.running = False


class ImageDetectionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_path = "pt/LWGA.pt"  # 默认模型路径
        self.selected_files = []  # 存储选择的多个图像文件路径
        self.current_preview_index = 0  # 当前预览的图像索引
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("图像检测")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 图像选择区域
        select_layout = QHBoxLayout()
        self.path_label = QLabel("未选择图像")
        self.path_label.setStyleSheet("background-color: white; padding: 8px; border-radius: 4px;")
        select_layout.addWidget(self.path_label, 1)
        
        self.select_btn = QPushButton("选择图像")
        self.select_btn.setStyleSheet("""
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
        self.select_btn.clicked.connect(self.select_image)
        select_layout.addWidget(self.select_btn)
        
        layout.addLayout(select_layout)
        
        # 图像预览控制区域
        preview_control_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("上一张")
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.prev_btn.clicked.connect(self.show_prev_image)
        self.prev_btn.setEnabled(False)
        preview_control_layout.addWidget(self.prev_btn)
        
        self.preview_info = QLabel("0/0")
        self.preview_info.setAlignment(Qt.AlignCenter)
        preview_control_layout.addWidget(self.preview_info, 1)
        
        self.next_btn = QPushButton("下一张")
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.next_btn.clicked.connect(self.show_next_image)
        self.next_btn.setEnabled(False)
        preview_control_layout.addWidget(self.next_btn)
        
        layout.addLayout(preview_control_layout)
        
        # 图像预览区域
        self.image_preview = QLabel("图像预览区域")
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            padding: 10px;
            min-height: 300px;
        """)
        layout.addWidget(self.image_preview)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                width: 1px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 检测按钮
        self.detect_btn = QPushButton("开始检测")
        self.detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.detect_btn.setEnabled(False)
        self.detect_btn.clicked.connect(self.detect_image)
        layout.addWidget(self.detect_btn)
        
        # 结果显示区域
        self.result_label = QLabel("检测结果将在这里显示")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            padding: 10px;
            min-height: 100px;
        """)
        layout.addWidget(self.result_label)
        
        # 创建定时器用于更新进度
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_progress)
    
    def select_image(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图像", "", "图像文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_paths:
            self.selected_files = file_paths
            self.current_preview_index = 0
            
            # 更新路径标签
            if len(file_paths) == 1:
                self.path_label.setText(file_paths[0])
            else:
                self.path_label.setText(f"已选择 {len(file_paths)} 个图像文件")
            
            # 启用检测按钮
            self.detect_btn.setEnabled(True)
            
            # 更新预览控制按钮状态
            self.update_preview_controls()
            
            # 显示第一张图像预览
            self.show_preview(0)
    
    def update_preview_controls(self):
        # 更新预览信息和按钮状态
        if self.selected_files:
            self.preview_info.setText(f"{self.current_preview_index + 1}/{len(self.selected_files)}")
            self.prev_btn.setEnabled(self.current_preview_index > 0)
            self.next_btn.setEnabled(self.current_preview_index < len(self.selected_files) - 1)
        else:
            self.preview_info.setText("0/0")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
    
    def show_preview(self, index):
        if 0 <= index < len(self.selected_files):
            file_path = self.selected_files[index]
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_preview.setPixmap(pixmap)
            else:
                self.image_preview.setText(f"无法加载图像: {os.path.basename(file_path)}")
            self.current_preview_index = index
            self.update_preview_controls()
    
    def show_prev_image(self):
        if self.current_preview_index > 0:
            self.current_preview_index -= 1
            # 检查是否有检测结果
            if hasattr(self, 'yolo_thread') and hasattr(self.yolo_thread, 'processed_results') and self.yolo_thread.processed_results:
                # 显示检测结果
                self.show_detection_result(self.current_preview_index)
            else:
                # 显示原始图像预览
                self.show_preview(self.current_preview_index)
            # 更新导航按钮状态
            self.update_preview_controls()
    
    def show_next_image(self):
        if self.current_preview_index < len(self.selected_files) - 1:
            self.current_preview_index += 1
            # 检查是否有检测结果
            if hasattr(self, 'yolo_thread') and hasattr(self.yolo_thread, 'processed_results') and self.yolo_thread.processed_results:
                # 显示检测结果
                self.show_detection_result(self.current_preview_index)
            else:
                # 显示原始图像预览
                self.show_preview(self.current_preview_index)
            # 更新导航按钮状态
            self.update_preview_controls()
    
    def update_progress(self):
        if hasattr(self, 'yolo_thread') and self.yolo_thread.isRunning():
            if self.yolo_thread.total_images > 0:
                progress = int((self.yolo_thread.current_image_index + 1) / self.yolo_thread.total_images * 100)
                self.progress_bar.setValue(progress)
                self.result_label.setText(f"正在处理: {self.yolo_thread.current_image_index + 1}/{self.yolo_thread.total_images}")
    
    def detect_image(self):
        try:
            self.result_label.setText("检测中...")
            self.detect_btn.setEnabled(False)
            
            # 检查模型文件是否存在
            if not os.path.exists(self.model_path):
                QMessageBox.critical(self, "错误", f"模型文件 {self.model_path} 不存在!")
                self.result_label.setText("检测失败: 模型文件不存在")
                self.detect_btn.setEnabled(True)
                return
            
            # 显示进度条
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            
            # 获取当前用户名
            parent = self.parent()
            while parent and not hasattr(parent, 'current_username'):
                parent = parent.parent()
            
            username = ""
            if parent and hasattr(parent, 'current_username'):
                username = parent.current_username
            
            # 创建并启动检测线程
            if len(self.selected_files) == 1:
                # 单图像模式
                self.yolo_thread = YOLOThread(self.model_path, image_path=self.selected_files[0], username=username)
            else:
                # 多图像模式
                self.yolo_thread = YOLOThread(self.model_path, image_paths=self.selected_files, username=username)
                # 启动定时器更新进度
                self.update_timer.start(500)  # 每500毫秒更新一次
            
            self.yolo_thread.finished.connect(self.detection_finished)
            self.yolo_thread.start()
        except Exception as e:
            self.result_label.setText(f"检测错误: {str(e)}")
            self.detect_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def detection_finished(self):
        try:
            # 停止进度更新定时器
            if hasattr(self, 'update_timer') and self.update_timer.isActive():
                self.update_timer.stop()
            
            # 隐藏进度条
            self.progress_bar.setVisible(False)
            
            # 检查模型是否成功加载
            if not hasattr(self.yolo_thread, 'model'):
                self.result_label.setText("检测失败: 模型未能成功加载")
                print("错误: YOLO模型未能成功加载")
                return
            
            # 处理多图像检测结果
            if hasattr(self.yolo_thread, 'processed_results') and self.yolo_thread.processed_results:
                # 多图像模式
                total_images = len(self.yolo_thread.processed_results)
                successful_detections = sum(1 for item in self.yolo_thread.processed_results if item["result"] is not None)
                failed_detections = total_images - successful_detections
                
                # 统计所有检测到的目标
                total_detections = 0
                class_counts = {}
                
                for item in self.yolo_thread.processed_results:
                    if item["result"] is not None:
                        result = item["result"]
                        # 检查是否为OBB模型结果
                        if hasattr(result, 'obb') and result.obb is not None:
                            # OBB模型结果，暂不计数
                            pass
                        # 检查是否有boxes属性
                        elif hasattr(result, 'boxes') and result.boxes is not None:
                            try:
                                boxes_count = len(result.boxes)
                                total_detections += boxes_count
                                
                                # 统计各类别数量
                                classes = result.names
                                for box in result.boxes:
                                    try:
                                        cls_id = int(box.cls[0])
                                        cls_name = self.model.names.get(cls_id, "未知类别")
                                        if cls_name in class_counts:
                                            class_counts[cls_name] += 1
                                        else:
                                            class_counts[cls_name] = 1
                                    except (IndexError, TypeError, KeyError) as box_err:
                                        print(f"处理检测框错误: {str(box_err)}")
                                        continue
                            except TypeError as te:
                                print(f"警告: 无法获取boxes长度: {str(te)}")
                
                # 构建结果文本
                result_text = f"批量检测完成! 共处理 {total_images} 张图像\n"
                result_text += f"成功: {successful_detections} 张, 失败: {failed_detections} 张\n"
                result_text += f"共检测到 {total_detections} 个目标\n"
                
                # 添加各类别统计
                if class_counts:
                    for cls_name, count in class_counts.items():
                        result_text += f"{cls_name}: {count} 个\n"
                
                self.result_label.setText(result_text)
                
                # 显示当前选中图像的检测结果
                self.show_detection_result(self.current_preview_index)
                return
                
            # 处理单图像检测结果
            if self.yolo_thread.results and len(self.yolo_thread.results) > 0 and self.yolo_thread.results[0] is not None:
                # 获取检测结果
                results = self.yolo_thread.results[0]
                print(f"处理检测结果: 类型={type(results)}")
                
                # 检查结果对象的属性
                print(f"结果对象属性: {dir(results)}")
                
                # 检查是否为OBB模型结果
                if hasattr(results, 'obb') and results.obb is not None:
                    print("检测到OBB模型结果")
                    # 使用OBB属性代替boxes
                    try:
                        # 显示检测结果图像
                        result_img = results.plot()
                        h, w, c = result_img.shape
                        qimg = QImage(result_img.data, w, h, w * c, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimg)
                        pixmap = pixmap.scaled(600, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.image_preview.setPixmap(pixmap)
                        
                        # 构建简单结果文本
                        self.result_label.setText("检测完成! 使用OBB模型检测成功")
                        return
                    except Exception as obb_err:
                        print(f"OBB结果处理错误: {str(obb_err)}")
                        # 继续检查其他属性
                
                # 确保results有boxes属性
                if not hasattr(results, 'boxes') or results.boxes is None:
                    error_msg = "检测失败: 未能获取有效的检测结果 (缺少boxes属性)"
                    self.result_label.setText(error_msg)
                    print(error_msg)
                    
                    # 尝试显示原始图像
                    try:
                        img = cv2.imread(self.selected_files[0])
                        if img is not None:
                            # 在原始图像上添加错误文本
                            cv2.putText(img, "检测失败", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            h, w, c = img.shape
                            qimg = QImage(img.data, w, h, w * c, QImage.Format_BGR888)
                            pixmap = QPixmap.fromImage(qimg)
                            pixmap = pixmap.scaled(600, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            self.image_preview.setPixmap(pixmap)
                    except Exception as img_err:
                        print(f"无法显示原始图像: {str(img_err)}")
                    
                    return
                    
                # 显示检测结果图像
                try:
                    result_img = results.plot()
                    h, w, c = result_img.shape
                    qimg = QImage(result_img.data, w, h, w * c, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    pixmap = pixmap.scaled(600, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_preview.setPixmap(pixmap)
                except Exception as plot_err:
                    print(f"无法绘制结果图像: {str(plot_err)}")
                    self.result_label.setText(f"检测完成但无法显示结果图像: {str(plot_err)}")
                    return
                
                # 显示检测统计信息
                try:
                    # 检查boxes是否为None
                    if results.boxes is None:
                        self.result_label.setText("检测完成但未检测到任何目标")
                        return
                        
                    # 尝试获取检测数量
                    try:
                        num_detections = len(results.boxes)
                    except TypeError:
                        self.result_label.setText("检测完成但无法获取目标数量")
                        return
                        
                    classes = results.names
                    class_counts = {}
                    
                    # 处理每个检测框
                    for box in results.boxes:
                        try:
                            cls_id = int(box.cls[0])
                            cls_name = self.model.names.get(cls_id, "未知类别")
                            if cls_name in class_counts:
                                class_counts[cls_name] += 1
                            else:
                                class_counts[cls_name] = 1
                        except (IndexError, TypeError, KeyError) as box_err:
                            print(f"处理检测框错误: {str(box_err)}")
                            continue
                    
                    # 构建结果文本
                    result_text = f"检测完成! 共检测到 {num_detections} 个目标\n"
                    for cls_name, count in class_counts.items():
                        result_text += f"{cls_name}: {count} 个\n"
                    
                    self.result_label.setText(result_text)
                except Exception as stats_err:
                    print(f"无法处理检测统计信息: {str(stats_err)}")
                    self.result_label.setText(f"检测完成但无法处理统计信息: {str(stats_err)}")
            else:
                # 检查是否有具体的错误信息
                error_msg = "检测失败或未检测到目标"
                if hasattr(self.yolo_thread, 'error_message') and self.yolo_thread.error_message:
                    error_msg += f": {self.yolo_thread.error_message}"
                self.result_label.setText(error_msg)
                print(f"检测结果为空: {error_msg}")
                
                # 尝试显示原始图像
                if self.selected_files:
                    try:
                        img = cv2.imread(self.selected_files[0])
                        if img is not None:
                            # 在原始图像上添加错误文本
                            cv2.putText(img, "未检测到目标", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            h, w, c = img.shape
                            qimg = QImage(img.data, w, h, w * c, QImage.Format_BGR888)
                            pixmap = QPixmap.fromImage(qimg)
                            pixmap = pixmap.scaled(600, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            self.image_preview.setPixmap(pixmap)
                    except Exception as img_err:
                        print(f"无法显示原始图像: {str(img_err)}")
        except Exception as e:
            error_msg = f"处理结果错误: {str(e)}"
            self.result_label.setText(error_msg)
            print(f"处理结果详细错误: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            # 确保清理数据库连接
            try:
                DetectionDatabase.cleanup_thread()
            except Exception as e:
                print(f"清理数据库连接时出错: {str(e)}")
                
            self.detect_btn.setEnabled(True)
    
    def show_detection_result(self, index):
        """显示指定索引图像的检测结果"""
        if not hasattr(self.yolo_thread, 'processed_results') or index >= len(self.yolo_thread.processed_results):
            return
            
        result_item = self.yolo_thread.processed_results[index]
        file_path = result_item["path"]
        result = result_item["result"]
        error = result_item["error"]
        
        if result is None:
            # 显示原始图像并添加错误信息
            try:
                img = cv2.imread(file_path)
                if img is not None:
                    # 在原始图像上添加错误文本
                    error_text = "检测失败" if error else "未检测到目标"
                    cv2.putText(img, error_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    h, w, c = img.shape
                    qimg = QImage(img.data, w, h, w * c, QImage.Format_BGR888)
                    pixmap = QPixmap.fromImage(qimg)
                    pixmap = pixmap.scaled(600, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_preview.setPixmap(pixmap)
            except Exception as img_err:
                print(f"无法显示原始图像: {str(img_err)}")
                self.image_preview.setText(f"无法加载图像: {os.path.basename(file_path)}")
        else:
            # 显示检测结果图像
            try:
                result_img = result.plot()
                h, w, c = result_img.shape
                qimg = QImage(result_img.data, w, h, w * c, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                pixmap = pixmap.scaled(600, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_preview.setPixmap(pixmap)
            except Exception as plot_err:
                print(f"无法绘制结果图像: {str(plot_err)}")
                self.image_preview.setText(f"无法显示检测结果: {os.path.basename(file_path)}")


class VideoDetectionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_path = "pt/best.pt"  # 默认模型路径
        self.yolo_thread = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_frame)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("视频检测")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 视频选择区域
        select_layout = QHBoxLayout()
        self.path_label = QLabel("未选择视频")
        self.path_label.setStyleSheet("background-color: white; padding: 8px; border-radius: 4px;")
        select_layout.addWidget(self.path_label, 1)
        
        self.select_btn = QPushButton("选择视频")
        self.select_btn.setStyleSheet("""
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
        self.select_btn.clicked.connect(self.select_video)
        select_layout.addWidget(self.select_btn)
        
        layout.addLayout(select_layout)
        
        # 视频预览区域
        self.video_preview = QLabel("视频预览区域")
        self.video_preview.setAlignment(Qt.AlignCenter)
        self.video_preview.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            padding: 10px;
            min-height: 300px;
        """)
        layout.addWidget(self.video_preview)
        
        # 控制按钮区域
        control_layout = QHBoxLayout()
        
        self.detect_btn = QPushButton("开始检测")
        self.detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.detect_btn.setEnabled(False)
        self.detect_btn.clicked.connect(self.detect_video)
        control_layout.addWidget(self.detect_btn)
        
        self.stop_btn = QPushButton("停止检测")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_detection)
        control_layout.addWidget(self.stop_btn)
        
        layout.addLayout(control_layout)
        
        # 结果显示区域
        self.result_label = QLabel("检测结果将在这里显示")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            padding: 10px;
            min-height: 100px;
        """)
        layout.addWidget(self.result_label)
    
    def select_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "", "视频文件 (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_path:
            self.path_label.setText(file_path)
            self.detect_btn.setEnabled(True)
            self.video_preview.setText(f"已选择视频: {os.path.basename(file_path)}")
    
    def detect_video(self):
        try:
            self.result_label.setText("视频检测中...")
            self.detect_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            # 检查模型文件是否存在
            if not os.path.exists(self.model_path):
                QMessageBox.critical(self, "错误", f"模型文件 {self.model_path} 不存在!")
                self.result_label.setText("检测失败: 模型文件不存在")
                self.detect_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                return
                
            # 创建进度条
            if not hasattr(self, 'progress_bar'):
                self.progress_bar = QProgressBar()
                self.layout().addWidget(self.progress_bar)
                self.progress_bar.setRange(0, 0)  # 不确定进度模式
            else:
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)
            
            # 获取当前用户名
            parent = self.parent()
            while parent and not hasattr(parent, 'current_username'):
                parent = parent.parent()
            
            username = ""
            if parent and hasattr(parent, 'current_username'):
                username = parent.current_username
            
            # 创建并启动检测线程
            self.yolo_thread = YOLOThread(self.model_path, video_path=self.path_label.text(), username=username)
            self.yolo_thread.start()
            
            # 启动定时器更新界面
            self.update_timer.start(30)  # 约30FPS
        except Exception as e:
            self.result_label.setText(f"检测错误: {str(e)}")
            self.detect_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def stop_detection(self):
        if self.yolo_thread and self.yolo_thread.isRunning():
            self.yolo_thread.stop()
            self.yolo_thread.wait()
            self.update_timer.stop()
            
            # 清理数据库连接
            try:
                from db.detection_db import DetectionDatabase
                DetectionDatabase.cleanup_thread()
                print("VideoDetectionPage: 成功清理数据库连接")
            except Exception as e:
                print(f"VideoDetectionPage: 清理数据库连接时出错: {str(e)}")
            
        self.result_label.setText("检测已停止")
        self.detect_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
    
    def update_frame(self):
        try:
            if self.yolo_thread and self.yolo_thread.processed_frame is not None:
                # 显示处理后的帧
                frame = self.yolo_thread.processed_frame
                if frame is None or not hasattr(frame, 'shape'):
                    return
                    
                h, w, c = frame.shape
                qimg = QImage(frame.data, w, h, w * c, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                pixmap = pixmap.scaled(600, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.video_preview.setPixmap(pixmap)
                
                # 更新结果信息
                self.result_label.setText(
                    f"检测中... FPS: {self.yolo_thread.fps:.1f} | "
                    f"检测到目标数: {self.yolo_thread.detection_count}"
                )
        except Exception as e:
            print(f"更新视频帧错误: {str(e)}")
            self.result_label.setText(f"视频处理错误: {str(e)}")
            # 停止检测
            self.stop_detection()


class RealtimeDetectionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_path = "pt/best.pt"  # 默认模型路径
        self.yolo_thread = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_frame)
        self.init_ui()
        self.is_detecting = False
        self.camera_open = False
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("实时检测")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 摄像头选择区域
        camera_layout = QHBoxLayout()
        camera_label = QLabel("选择摄像头:")
        camera_layout.addWidget(camera_label)
        
        self.camera_btn = QPushButton("打开摄像头")
        self.camera_btn.setStyleSheet("""
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
        self.camera_btn.clicked.connect(self.toggle_camera)
        camera_layout.addWidget(self.camera_btn)
        camera_layout.addStretch()
        
        layout.addLayout(camera_layout)
        
        # 视频预览区域
        self.camera_preview = QLabel("摄像头预览区域")
        self.camera_preview.setAlignment(Qt.AlignCenter)
        self.camera_preview.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            padding: 10px;
            min-height: 400px;
        """)
        layout.addWidget(self.camera_preview)
        
        # 控制按钮区域
        control_layout = QHBoxLayout()
        
        self.detect_btn = QPushButton("开始检测")
        self.detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.detect_btn.setEnabled(False)
        self.detect_btn.clicked.connect(self.toggle_detection)
        control_layout.addWidget(self.detect_btn)
        
        layout.addLayout(control_layout)
        
        # 结果显示区域
        self.result_label = QLabel("检测结果将在这里显示")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            padding: 10px;
            min-height: 100px;
        """)
        layout.addWidget(self.result_label)
    
    def toggle_camera(self):
        if not self.camera_open:
            try:
                # 打开摄像头
                self.camera_id = 0  # 默认摄像头ID
                
                # 测试摄像头是否可用
                cap = cv2.VideoCapture(self.camera_id)
                if not cap.isOpened():
                    QMessageBox.critical(self, "错误", "无法打开摄像头!")
                    return
                cap.release()
                
                self.camera_open = True
                self.camera_btn.setText("关闭摄像头")
                self.detect_btn.setEnabled(True)
                self.camera_preview.setText("摄像头已打开")
                
                # 创建摄像头预览线程
                self.preview_thread = QThread()
                self.preview_thread.run = self.preview_camera
                self.preview_thread.start()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开摄像头失败: {str(e)}")
        else:
            # 关闭摄像头
            self.camera_open = False
            self.camera_btn.setText("打开摄像头")
            self.detect_btn.setEnabled(False)
            self.camera_preview.setText("摄像头已关闭")
            
            if self.is_detecting:
                self.toggle_detection()
            
            if hasattr(self, 'preview_thread') and self.preview_thread.isRunning():
                self.preview_thread.terminate()
                self.preview_thread.wait()
    
    def preview_camera(self):
        cap = cv2.VideoCapture(self.camera_id)
        while self.camera_open and not self.is_detecting:
            ret, frame = cap.read()
            if not ret:
                continue
                
            # 转换为Qt图像并显示
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, c = rgb_frame.shape
            qimg = QImage(rgb_frame.data, w, h, w * c, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            pixmap = pixmap.scaled(600, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 使用信号槽更新UI（在主线程中）
            self.camera_preview.setPixmap(pixmap)
            
            # 降低CPU使用率
            time.sleep(0.03)
            
        cap.release()
    
    def toggle_detection(self):
        if not self.is_detecting:
            try:
                # 检查模型文件是否存在
                if not os.path.exists(self.model_path):
                    QMessageBox.critical(self, "错误", f"模型文件 {self.model_path} 不存在!")
                    return
                    
                # 开始检测
                self.is_detecting = True
                self.detect_btn.setText("停止检测")
                self.result_label.setText("实时检测中...")
                
                # 停止预览线程
                if hasattr(self, 'preview_thread') and self.preview_thread.isRunning():
                    self.preview_thread.terminate()
                    self.preview_thread.wait()
                
                # 获取当前用户名
                parent = self.parent()
                while parent and not hasattr(parent, 'current_username'):
                    parent = parent.parent()
                
                username = ""
                if parent and hasattr(parent, 'current_username'):
                    username = parent.current_username
                
                # 创建并启动检测线程
                self.yolo_thread = YOLOThread(self.model_path, camera_id=self.camera_id, username=username)
                self.yolo_thread.start()
                
                # 启动定时器更新界面
                self.update_timer.start(30)  # 约30FPS
            except Exception as e:
                self.is_detecting = False
                self.detect_btn.setText("开始检测")
                self.result_label.setText(f"检测错误: {str(e)}")
        else:
            # 停止检测
            if self.yolo_thread and self.yolo_thread.isRunning():
                self.yolo_thread.stop()
                self.yolo_thread.wait()
                self.update_timer.stop()
                
                # 清理数据库连接
                try:
                    from db.detection_db import DetectionDatabase
                    DetectionDatabase.cleanup_thread()
                    print("RealtimeDetectionPage: 成功清理数据库连接")
                except Exception as e:
                    print(f"RealtimeDetectionPage: 清理数据库连接时出错: {str(e)}")
            
            self.is_detecting = False
            self.detect_btn.setText("开始检测")
            self.result_label.setText("检测已停止")
            
            # 重新启动预览线程
            if self.camera_open:
                self.preview_thread = QThread()
                self.preview_thread.run = self.preview_camera
                self.preview_thread.start()
    
    def update_frame(self):
        try:
            if self.yolo_thread and self.yolo_thread.processed_frame is not None:
                # 显示处理后的帧
                frame = self.yolo_thread.processed_frame
                if frame is None or not hasattr(frame, 'shape'):
                    return
                
                # 将BGR格式转换为RGB格式，确保颜色正确显示
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, c = rgb_frame.shape
                qimg = QImage(rgb_frame.data, w, h, w * c, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                pixmap = pixmap.scaled(600, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.camera_preview.setPixmap(pixmap)
                
                # 更新结果信息
                self.result_label.setText(
                    f"检测中... FPS: {self.yolo_thread.fps:.1f} | "
                    f"检测到目标数: {self.yolo_thread.detection_count}"
                )
        except Exception as e:
            print(f"更新摄像头帧错误: {str(e)}")
            self.result_label.setText(f"实时检测处理错误: {str(e)}")
            # 停止检测
            self.toggle_detection()


class DetectionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_username = ""  # 添加当前用户名属性
        self.init_ui()
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建顶部导航栏
        nav_bar = QWidget()
        nav_bar.setStyleSheet("background-color: #ecf0f1; border-bottom: 1px solid #bdc3c7;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(10, 5, 10, 5)
        
        # 创建导航按钮
        self.nav_buttons = []
        nav_items = ["图像检测", "视频检测", "实时检测"]
        
        # 添加弹性空间，使导航按钮居中
        nav_layout.addStretch(1)
        
        for i, item in enumerate(nav_items):
            btn = QPushButton(item)
            btn.setCheckable(True)
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 14px;
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: #d5dbdb;
                }
                QPushButton:checked {
                    background-color: #3498db;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked=False, idx=i: self.change_page(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        # 添加弹性空间，使导航按钮居中
        nav_layout.addStretch(1)
        main_layout.addWidget(nav_bar)
        
        # 创建堆叠窗口用于切换子页面
        self.stack = QStackedWidget()
        
        # 创建子页面
        self.image_page = ImageDetectionPage()
        self.video_page = VideoDetectionPage()
        self.realtime_page = RealtimeDetectionPage()
        
        # 添加子页面到堆叠窗口
        self.stack.addWidget(self.image_page)
        self.stack.addWidget(self.video_page)
        self.stack.addWidget(self.realtime_page)
        
        main_layout.addWidget(self.stack)
        
        # 默认选中第一个页面
        self.nav_buttons[0].setChecked(True)
        self.stack.setCurrentIndex(0)
    
    def change_page(self, index):
        # 更新按钮状态
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        
        # 切换页面
        self.stack.setCurrentIndex(index)