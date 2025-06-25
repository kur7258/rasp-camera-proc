import cv2
from flask import Flask, Response

# Pi Camera 모듈용 라이브러리
from picamera2 import Picamera2
import numpy as np

app = Flask(__name__)

def gen_frames_usb():
    """
    USB 웹캠(예: /dev/video0)에서 프레임을 읽어오는 제너레이터
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("카메라를 열 수 없습니다.")
    while True:
        success, frame = cap.read()
        if not success:
            break
        # JPEG로 인코딩
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        # MJPEG 스트림 형식으로 반환
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    cap.release()

# Pi Camera 모듈용 (picamera2 사용)
def gen_frames_picamera():
    """
    라즈베리파이 카메라 모듈(Pi Camera)에서 프레임을 읽어오는 제너레이터
    """
    picam2 = Picamera2()
    picam2.start()
    try:
        while True:
            frame = picam2.capture_array()
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        picam2.close()

# gen_frames = gen_frames_usb  # USB 웹캠용
gen_frames = gen_frames_picamera  # Pi Camera 모듈용

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>Raspberry Pi Camera Stream</title>
    </head>
    <body>
        <h1>실시간 카메라 스트림</h1>
        <img src="/video_feed" width="640" height="480">
    </body>
    </html>
    '''

if __name__ == '__main__':
    # 0.0.0.0으로 바인딩해야 외부에서 접속 가능
    app.run(host='0.0.0.0', port=5000, threaded=True)
