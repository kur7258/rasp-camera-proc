import cv2

# fire_sample.png 읽기
img = cv2.imread('fire_sample.png', cv2.IMREAD_UNCHANGED)

# 원본 크기 확인
h, w = img.shape[:2]

# 1/3 크기로 리사이즈
resized = cv2.resize(img, (w // 3, h // 3), interpolation=cv2.INTER_AREA)

# 저장
cv2.imwrite('fire_sample_small.png', resized)
print('fire_sample_small.png로 저장 완료!')