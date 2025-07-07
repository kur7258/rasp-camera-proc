import cv2
import numpy as np
import requests
from ultralytics import YOLO

# YOLOv8n 모델 로드
model = YOLO('yolov8s.pt')

# MJPEG 스트림 URL
url = 'http://192.168.0.21:5000/video_feed'
stream = requests.get(url, stream=True)

bytes_data = b''

for chunk in stream.iter_content(chunk_size=1024):
    bytes_data += chunk
    a = bytes_data.find(b'\xff\xd8')  # JPEG 시작
    b = bytes_data.find(b'\xff\xd9')  # JPEG 끝
    if a != -1 and b != -1 and b > a:
        jpg = bytes_data[a:b+2]
        bytes_data = bytes_data[b+2:]
        # JPEG 이미지를 OpenCV 이미지로 변환
        img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            # YOLOv8n으로 객체 탐지
            results = model(img)
            boxes = results[0].boxes
            names = results[0].names
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = f"{names[cls]} {conf:.2f}"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.2  # 더 작게
                thickness = 1     # 더 얇게
                color = (0, 255, 0)
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 1)
                cv2.putText(img, label, (x1, y1 - 5), font, font_scale, color, thickness, cv2.LINE_AA)
            cv2.imshow('YOLOv8s Detection (Custom Style)', img)
            if cv2.waitKey(1) == 27:  # ESC 키로 종료
                break

cv2.destroyAllWindows()

