import os
import sys
import shutil
from pyecharts.globals import CurrentConfig

def ensure_echarts_available():
    """
    确保echarts库可用，如果本地不存在则从CDN下载
    设置pyecharts全局配置使用本地JS文件
    """
    # 确保charts目录存在
    os.makedirs("charts", exist_ok=True)
    
    # 确保echarts目录存在
    echarts_dir = "charts/assets"
    os.makedirs(echarts_dir, exist_ok=True)
    
    # 下载echarts库到本地（如果不存在）
    echarts_js_path = os.path.join(echarts_dir, "echarts.min.js")
    if not os.path.exists(echarts_js_path):
        try:
            import requests
            # 从CDN下载echarts库
            response = requests.get("https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js")
            with open(echarts_js_path, "wb") as f:
                f.write(response.content)
            print("成功下载echarts库到本地")
        except Exception as e:
            print(f"下载echarts库失败: {e}")
            # 如果下载失败，尝试使用在线CDN
            return None
    
    # 设置pyecharts的全局配置
    # 使用相对路径，这样在HTML中可以正确引用
    CurrentConfig.ONLINE_HOST = "./assets/"
    
    # 修改pyecharts生成的HTML文件，确保正确引用本地JS文件
    return echarts_js_path

def fix_chart_html(html_path):
    """
    修复生成的HTML文件，确保正确引用echarts库
    """
    if not os.path.exists(html_path):
        return
    
    try:
        # 读取HTML文件内容
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否已经包含了正确的echarts引用
        if "./assets/echarts.min.js" in content:
            return
        
        # 替换CDN引用为本地引用
        content = content.replace(
            "https://assets.pyecharts.org/assets/echarts.min.js", 
            "./assets/echarts.min.js"
        )
        content = content.replace(
            "https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js",
            "./assets/echarts.min.js"
        )
        
        # 写回文件
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"已修复图表HTML文件: {html_path}")
    except Exception as e:
        print(f"修复HTML文件失败: {e}")