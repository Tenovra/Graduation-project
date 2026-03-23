from ultralytics import YOLO
import time
import warnings

def main():
    model = YOLO('yolov8m-obb-LWGA-C2f.yaml') # build from YAML and transfer weights
    # for k, v in model.model.named_parameters():
    #     print("参数名称:", k)
    model.train(
        data='E:/bishe/ultralytics-main/datasets/shipdetection.yaml',
        # data='shipdetection.yaml',
        epochs=10,
        imgsz=1024,
        batch=1, #-1自适应
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

