# Expanding-your-VISION
Cinematic Panorama Stitcher: A professional tool to create a single unified 32:9 photo from 4 input images.

# Cinematic Panorama Stitcher

본 프로젝트는 OpenCV의 기하학적 원리(Homography, SVD, Backward Mapping)를 이용하여 4장의 이미지를 하나의 파노라마 이미지로 만드는 프로그램입니다.

단순한 평면 투영을 넘어, **Cylindrical Projection**과 **Distance Transform 기반 페더링**, 그리고 **크롭** 기능을 추가로 적용하여 상용 파노라마 소프트웨어 수준의 매끄러운 결과물을 생성합니다.

---

# 주요 기능

### 시네마틱 파노라마 생성
**4-Image Seamless Stitching:** 직접 촬영한 4장의 소스 이미지를 분석하여 하나의 초광각 파노라마로 정합합니다. 기준점(Reference)을 중심으로 좌우 이미지를 연쇄적으로 정렬하는 **Matrix Chaining** 기술을 통해 오차 없는 파노라마 뷰를 제공합니다.

### 왜곡 없는 광각 뷰 
**Perspective Distortion Correction:** 일반적인 Planar Projection에서 발생하는 양 끝단이 늘어나는 현상을 방지합니다. 스티칭 전 모든 이미지를 **원통형 좌표계**로 변환하여, 시야각이 넓어져도 실제 눈으로 보는 것과 유사한 반듯한 비율을 유지합니다.

### 경계선 없는 자연스러운 블렌딩
**Distance Transform Feathering:** 사진과 사진이 만나는 지점의 노출 차이와 경계선을 제거합니다. **거리 변환** 알고리즘을 활용해 이미지 중심부에서 테두리로 갈수록 투명해지는 가중치 마스크를 생성하여, 여러 장의 사진이 마치 한 장처럼 자연스럽게 변환합니다.

### 자동 크롭
**Cinematic Precision Crop:** 스티칭 후 발생하는 불규칙한 검은색 여백을 자동으로 제거합니다. 사방에서 픽셀을 정밀하게 분석한 후, 여백을 제거하여 별도의 편집 없이도 32:9 울트라와이드 비율의 깔끔한 직사각형 최종 결과물을 출력합니다.

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
