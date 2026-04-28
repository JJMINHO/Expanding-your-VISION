# Expanding-your-VISION
This is a tool makes unified photo using 4 photos

# Cinematic Panorama Stitcher

> A robust, Python-based image stitching tool that manually estimates homography and seamlessly blends multiple images into a 32:9 cinematic cylindrical panorama.

본 프로젝트는 OpenCV의 기하학적 원리(Homography, SVD, Backward Mapping)를 이용하여 4장의 이미지를 하나의 파노라마 이미지로 만드는 프로그램입니다.

단순한 평면 투영을 넘어, **Cylindrical Projection**과 **Distance Transform 기반 페더링**, 그리고 **크롭** 기능을 추가로 적용하여 상용 파노라마 소프트웨어 수준의 매끄러운 결과물을 생성합니다.

---

## 핵심 구현 사항

### 수학적 원리 구현
* **Manual Homography Estimation (SVD):** SIFT 알고리즘으로 추출한 특징점들을 바탕으로 $Ax=0$ 형태의 선형 방정식을 세우고, SVD(`np.linalg.svd`)를 활용해 변환 행렬 $H$를 직접 계산합니다.
* **Backward Mapping Warping:** 파이썬 환경의 연산 병목을 해결하기 위해 중첩 `for`문 대신 `np.indices`를 활용하여 픽셀을 역방향으로 복사(Backward Mapping)하는 워핑을 벡터화(Vectorization)하여 직접 구현했습니다.
* **Matrix Chaining (4-Image Stitching):** 2번째 이미지를 중앙(Reference)으로 설정하고, 3->2 변환 행렬과 2->1 변환 행렬을 곱하는 연쇄 법칙($H_{3\to1} = H_{2\to1} H_{3\to2}$)을 통해 4장의 사진을 완벽하게 이어붙였습니다.

### 추가 기능 
* **Cylindrical Projection (원통형 투영):** 시야각이 넓어질수록 파노라마 양끝이 부채꼴처럼 비정상적으로 늘어나는 투시 왜곡(Perspective Distortion)을 방지하기 위해, 스티칭 전 이미지를 원통형 좌표계로 구부려주는 전처리 로직을 추가했습니다.
* **Distance Transform Feathering (거리 기반 알파 블렌딩):** 사진 간 노출 차이로 인해 생기는 칼로 자른 듯한 경계선(Seam)을 없애기 위해, `cv2.distanceTransform`을 이용해 중심부에서 가장자리로 갈수록 0에 수렴하는 정교한 가중치 마스크를 생성하여 이미지를 자연스럽게 녹여냈습니다.
* **Cinematic Precision Crop (정밀 크롭 알고리즘):** 파노라마 생성 후 생기는 상하좌우의 불규칙한 검은색 여백을 1픽셀도 남기지 않고 깎아내어(Shaving algorithm), 32:9 비율의 깔끔한 직사각형 뷰를 자동으로 추출합니다.

---

## 결과 데모 

### 원본 소스 이미지

<table>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/950ca7bc-de10-49f1-9116-1569c3ebba89" alt="Image 1"></td>
    <td><img src="https://github.com/user-attachments/assets/50ed4f66-5c18-4ac3-bf08-2cf33f39fcda" alt="Image 2"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/3bfcc671-4cbc-4df3-a3b6-5bd9070e4b04" alt="Image 3"></td>
    <td><img src="https://github.com/user-attachments/assets/304361ab-03fe-495e-96c9-3238fdf056b2" alt="Image 4"></td>
  </tr>
</table>

<br>

### Original Cylindrical Panorama
<img src="https://github.com/user-attachments/assets/1e0a2c0e-8223-4156-af40-12500e7506fd" alt="Original Cylindrical Panorama" width="100%">

<br>

### Cropped Cinematic Panorama
<img src="https://github.com/user-attachments/assets/f519c531-7e44-4722-8546-323d095f32b2" alt="Cropped Cinematic Panorama" width="100%">

---

## 실행 방법 

### Requirements
* Python 3.x
* OpenCV (`cv2`)
* NumPy

### Execution
1. 본 저장소를 Clone 하거나 다운로드합니다.
2. 터미널에서 스크립트가 있는 경로로 이동합니다.
3. 스티칭할 4장의 이미지(`img0.jpeg` ~ `img3.jpeg`)가 스크립트와 동일한 폴더에 있는지 확인합니다.
4. 아래 명령어를 실행합니다.

```bash
python image_stitching.py
```
*사용자의 환경에 따라 작동방법은 달라질 수 있습니다.
