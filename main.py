import cv2
from flask import Flask, Response

# Pi Camera 모듈용 라이브러리
# from picamera2 import Picamera2
import numpy as np

app = Flask(__name__)

fire_img = cv2.imread('fire_sample.png', cv2.IMREAD_UNCHANGED)  # (H, W, 4)

def overlay_fire(frame, fire_img, x, y):
    fh, fw = fire_img.shape[:2]
    roi = frame[y:y+fh, x:x+fw]
    fire_rgb = fire_img[..., :3]
    alpha = fire_img[..., 3:] / 255.0
    blended = (roi * (1 - alpha) + fire_rgb * alpha).astype(np.uint8)
    frame[y:y+fh, x:x+fw] = blended
    return frame

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
        # 불 이미지 합성
        frame = overlay_fire(frame, fire_img, x=197, y=221)
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

gen_frames = gen_frames_usb  # USB 웹캠용
# gen_frames = gen_frames_picamera  # Pi Camera 모듈용

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
        <style>
            #cam-container {
                position: relative;
                display: inline-block;
            }
            #coords {
                position: absolute;
                top: 10px;
                left: 10px;
                background: rgba(0,0,0,0.5);
                color: #fff;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 16px;
                pointer-events: none;
                z-index: 10;
            }
        </style>
    </head>
    <body>
        <h1>실시간 카메라 스트림</h1>
        <div id="cam-container">
            <img id="cam" src="/video_feed" width="640" height="480" style="display:block;">
            <div id="coords">x: -, y: -</div>
        </div>
        <script>
            const cam = document.getElementById('cam');
            const coords = document.getElementById('coords');
            cam.addEventListener('mousemove', function(e) {
                const rect = cam.getBoundingClientRect();
                const x = Math.round(e.clientX - rect.left);
                const y = Math.round(e.clientY - rect.top);
                coords.textContent = `x: ${x}, y: ${y}`;
                coords.style.display = 'block';
                coords.style.left = (x + 10) + 'px';
                coords.style.top = (y + 10) + 'px';
            });
            cam.addEventListener('mouseleave', function() {
                coords.textContent = 'x: -, y: -';
                coords.style.display = 'block';
                coords.style.left = '10px';
                coords.style.top = '10px';
            });
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    # 0.0.0.0으로 바인딩해야 외부에서 접속 가능
    app.run(host='0.0.0.0', port=5000, threaded=True)
