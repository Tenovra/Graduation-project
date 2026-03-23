# Graduation-project
Introducing the swin-transformer module on yolov8  
>关于数据集以及处理：
```txt
数据集：HRSC6
标注格式：OBB
图片格式：bmp
标注格式处理：XML->DOTA->通过绘制旋转框查看labels是否正确->TXT格式(YOLO支持)
注：每个目标的类别和四个顶点坐标（x1,y1,x2,y2,x3,y3,x4,y4）。然后将训练集按照8：2的比例划分为训练集和测试集
分类：Warcraft（军舰），Aircraft carrier（航母），Merchant ship（货船），Submarine（潜艇）
```
>超参数设置：

| 参数名称       | 参数值  | 描述         |
| ---------- | ---- | ---------- |
| batch_size | 16   | 每个训练批次的样本数 |
| epoch      | 200  | 训练轮数       |
| optimizer  | SGD  | 优化器选择      |
| imgsz      | 1024 | 输入图像尺寸     |
| 模型选择       | m    | 使用中等尺寸模型   |
| Lr0        | 1e2  | 初始学习率      |
>LWGA参数设置

| 参数名称       | 参数值         | 描述       |
| ---------- | ----------- | -------- |
| stage      | 3           | 注意力类型    |
| att_kernal | 11          | MRA卷积核大小 |
| mlp_ratio  | 2.0         | MLP扩展比率  |
| drop_path  | 0.1         | 随即深度比率   |
| act_layer  | GELU        | 激活函数     |
| norm_layer | BatchNorm2d | 归一化处理    |

>必要环境
```
cuda=12.1
pytorch=1.12.1
python=3.8
```
`pip install timm -i https://mirrors.bfsu.edu.cn/pypi/web/simple`  
`pip install antialiased_cnns`  
`pip install -U openmim`  
`mim install mmcv-full`  
`mim install mmdet`  
`cd /datasets/train_LWGA/detection  pip install -v -e .`  
`cd /ultralytics   pip install -e .`  
>目录结构
```
UI界面目录：datasets/ui_final/
网络模型训练：datasets/train_LWGA.py
网络模型结构：datasets/yolov8-obb-LWGA.yaml
```
>标注格式转换  
`Tools/xml_to_dota.py`  
`Tools/dota_drawed.py`  
`Tools/dota_to_yolo.py`  

