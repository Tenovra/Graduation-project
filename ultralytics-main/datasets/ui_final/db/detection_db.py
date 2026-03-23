import sqlite3
import os
import threading
from datetime import datetime

class DetectionDatabase:
    _instance = None
    _lock = threading.Lock()
    _local = threading.local()
    
    @classmethod
    def get_instance(cls):
        """获取数据库单例实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_connection(cls):
        """获取当前线程的数据库连接"""
        if not hasattr(cls._local, 'connection'):
            # 确保data目录存在
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            db_path = os.path.join(data_dir, 'detection_results.db')
            cls._local.connection = sqlite3.connect(db_path)
            cls._local.connection.execute('PRAGMA foreign_keys = ON')
        return cls._local.connection
    
    @classmethod
    def cleanup_thread(cls):
        """清理当前线程的数据库连接"""
        if hasattr(cls._local, 'connection'):
            try:
                cls._local.connection.close()
            except Exception as e:
                print(f"关闭数据库连接时出错: {str(e)}")
            finally:
                del cls._local.connection
    
    def __init__(self):
        """初始化数据库，创建必要的表"""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        self.db_path = os.path.join(data_dir, 'detection_results.db')
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建图像检测结果表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            image_path TEXT NOT NULL,
            class_name TEXT NOT NULL,
            confidence TEXT NOT NULL,
            bbox_type TEXT DEFAULT 'rect',
            obb_points TEXT
        )
        ''')
        
        # 创建视频检测结果表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            video_path TEXT NOT NULL,
            frame_number INTEGER NOT NULL,
            class_name TEXT NOT NULL,
            confidence TEXT NOT NULL,
            bbox_type TEXT DEFAULT 'rect',
            obb_points TEXT
        )
        ''')
        
        # 创建实时检测结果表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS realtime_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            camera_id TEXT NOT NULL,
            class_name TEXT NOT NULL,
            confidence TEXT NOT NULL,
            bbox_type TEXT DEFAULT 'rect',
            obb_points TEXT
        )
        ''')
        
        conn.commit()
    
    def save_image_detection(self, username, image_path, class_name, confidence, 
                             bbox=None, bbox_type='rect', obb_points=None):
        """保存图像检测结果到数据库
        
        Args:
            username: 用户名
            image_path: 图像路径
            class_name: 检测类别名称
            confidence: 置信度
            bbox: 边界框 (x, y, width, height) 或 None
            bbox_type: 边界框类型 ('rect' 或 'obb')
            obb_points: OBB边界框点坐标列表 或 None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if bbox_type == 'rect' and bbox is not None:
            # 不再保存x, y, width, height
            cursor.execute('''
            INSERT INTO image_detections 
            (username, timestamp, image_path, class_name, confidence, bbox_type)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, timestamp, image_path, class_name, confidence, bbox_type))
        else:  # OBB 类型
            obb_str = str(obb_points) if obb_points else None
            cursor.execute('''
            INSERT INTO image_detections 
            (username, timestamp, image_path, class_name, confidence, bbox_type, obb_points)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, timestamp, image_path, class_name, confidence, 
                  bbox_type, obb_str))
        
        conn.commit()
    
    def save_video_detection(self, username, video_path, frame_number, class_name, confidence, 
                             bbox=None, bbox_type='rect', obb_points=None):
        """保存视频检测结果到数据库
        
        Args:
            username: 用户名
            video_path: 视频路径
            frame_number: 帧号
            class_name: 检测类别名称
            confidence: 置信度
            bbox: 边界框 (x, y, width, height) 或 None
            bbox_type: 边界框类型 ('rect' 或 'obb')
            obb_points: OBB边界框点坐标列表 或 None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if bbox_type == 'rect' and bbox is not None:
            # 不再保存x, y, width, height
            cursor.execute('''
            INSERT INTO video_detections 
            (username, timestamp, video_path, frame_number, class_name, confidence, bbox_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, timestamp, video_path, frame_number, class_name, confidence, bbox_type))
        else:  # OBB 类型
            obb_str = str(obb_points) if obb_points else None
            cursor.execute('''
            INSERT INTO video_detections 
            (username, timestamp, video_path, frame_number, class_name, confidence, 
             bbox_type, obb_points)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, timestamp, video_path, frame_number, class_name, 
                  confidence, bbox_type, obb_str))
        
        conn.commit()
    
    def save_realtime_detection(self, username, camera_id, class_name, confidence, 
                                bbox=None, bbox_type='rect', obb_points=None):
        """保存实时检测结果到数据库
        
        Args:
            username: 用户名
            camera_id: 摄像头ID
            class_name: 检测类别名称
            confidence: 置信度
            bbox: 边界框 (x, y, width, height) 或 None
            bbox_type: 边界框类型 ('rect' 或 'obb')
            obb_points: OBB边界框点坐标列表 或 None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if bbox_type == 'rect' and bbox is not None:
            # 不再保存x, y, width, height
            cursor.execute('''
            INSERT INTO realtime_detections 
            (username, timestamp, camera_id, class_name, confidence, bbox_type)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, timestamp, camera_id, class_name, confidence, bbox_type))
        else:  # OBB 类型
            obb_str = str(obb_points) if obb_points else None
            cursor.execute('''
            INSERT INTO realtime_detections 
            (username, timestamp, camera_id, class_name, confidence, 
             bbox_type, obb_points)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, timestamp, camera_id, class_name, 
                  confidence, bbox_type, obb_str))
        
        conn.commit()