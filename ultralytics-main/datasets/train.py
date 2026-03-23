from ultralytics import YOLO
import time

def main():
    # model = YOLO('yolov8m-obb.yaml').load('yolov8m-obb.pt')  # build from YAML and transfer weights
    model = YOLO('yolov8m-obb.yaml')  # build from YAML and transfer weights
    model.train(
        data='E:/bishe/ultralytics-main/datasets/shipdetection.yaml',
        # data='shipdetection.yaml',
        epochs=10,
        imgsz=1024,
        batch=4, #-1自适应
        device=[0, ],
        workers=0,
        # optimizer = 'AdamW', 优化器。如 ‘SGD’、‘Adam’、‘AdamW’、‘RMSProp’，根据任务需求选择适合的优化器。
        save = True,
        save_period=-1, #禁用检查点
        cache=True,
        verbose=True,
    )


if __name__ == '__main__':
    main()

