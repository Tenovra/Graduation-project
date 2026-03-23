from ultralytics import YOLO


def validate_model(model_path, data_config):
    # 加载训练好的模型
    model = YOLO(model_path)

    # 执行验证
    results = model.val(
        data=data_config,
        batch=4,  # 根据GPU显存调整
        imgsz=1024,  # 训练时使用的图像尺寸
        conf=0.25,  # 置信度阈值
        iou=0.5,  # IoU阈值
        workers=0,
        device=[0, ],
        split='val',  # 验证集划分
        verbose=True  # 显示详细结果（关键参数）
    )


if __name__ == '__main__':
    # 配置文件路径（根据实际路径修改）
    config_path = r'E:/project/back/ultralytics-main/datasets/shipdetection.yaml'  # 确保指向正确的yaml文件

    # 训练好的模型路径
    model_path = r'E:/project/back/ultralytics-main/datasets/pt/LWGA_200.pt'  # 修改为你的模型路径

    validate_model(model_path, config_path)
