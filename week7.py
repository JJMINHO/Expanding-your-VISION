import cv2
import numpy as np
import os

# 한글 경로 에러 방지용 이미지 읽기 함수
def imread_robust(filepath):
    try:
        img_array = np.fromfile(filepath, np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception:
        return None

# 가장자리 왜곡 방지를 위한 원통형 투영 변환
def warp_to_cylinder(img, focal_length=None):
    h, w = img.shape[:2]
    focal_length = w * 0.8 if focal_length is None else focal_length

    y_indices, x_indices = np.indices((h, w))
    theta = (x_indices - w / 2) / focal_length
    h_cyl = (y_indices - h / 2) / focal_length

    x_orig = focal_length * np.tan(theta) + w / 2
    y_orig = focal_length * (h_cyl / np.cos(theta)) + h / 2

    map_x, map_y = x_orig.astype(np.float32), y_orig.astype(np.float32)
    warped_img = cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

    crop_margin = int(w * 0.05)
    return warped_img[:, crop_margin: w - crop_margin]

# 거리 변환을 이용한 경계선 페더링(자연스러운 블렌딩) 마스크 생성
def get_distance_transform_mask(mask):
    mask_uint8 = (mask * 255).astype(np.uint8)
    dist = cv2.distanceTransform(mask_uint8, cv2.DIST_L2, 5)
    cv2.normalize(dist, dist, 0, 1.0, cv2.NORM_MINMAX)
    return dist

# 상하좌우 검은 여백을 깎아내는 크롭 함수
def crop_perfect_rectangle(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    x, y, w, h = cv2.boundingRect(thresh)
    cropped = img[y:y + h, x:x + w]
    thresh_cropped = thresh[y:y + h, x:x + w]

    top, bottom, left, right = 0, cropped.shape[0] - 1, 0, cropped.shape[1] - 1

    while top < bottom and left < right:
        has_black_top = np.any(thresh_cropped[top, left:right + 1] == 0)
        has_black_bottom = np.any(thresh_cropped[bottom, left:right + 1] == 0)
        has_black_left = np.any(thresh_cropped[top:bottom + 1, left] == 0)
        has_black_right = np.any(thresh_cropped[top:bottom + 1, right] == 0)

        if not (has_black_top or has_black_bottom or has_black_left or has_black_right):
            break

        if has_black_top: top += 1
        if has_black_bottom: bottom -= 1
        if has_black_left: left += 1
        if has_black_right: right -= 1

    return cropped[top:bottom + 1, left:right + 1]


class PanoramaStitcher:
    def __init__(self):
        self.detector = cv2.SIFT_create()
        self.matcher = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))

    def extract_and_match(self, img_src, img_dst):
        # SIFT 특징점 추출 및 FLANN 매칭 (Lowe's Ratio Test 적용)
        kp1, des1 = self.detector.detectAndCompute(cv2.cvtColor(img_src, cv2.COLOR_BGR2GRAY), None)
        kp2, des2 = self.detector.detectAndCompute(cv2.cvtColor(img_dst, cv2.COLOR_BGR2GRAY), None)

        good_matches = [m for m, n in self.matcher.knnMatch(des1, des2, k=2) if m.distance < 0.7 * n.distance]

        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 2)
        return src_pts, dst_pts

    def compute_homography_svd(self, src_pts, dst_pts):
        # DLT 알고리즘 구현: SVD를 이용한 homography 행렬 계산
        A = []
        for (x, y), (u, v) in zip(src_pts.reshape(-1, 2), dst_pts.reshape(-1, 2)):
            A.extend([[-x, -y, -1, 0, 0, 0, u * x, u * y, u],
                      [0, 0, 0, -x, -y, -1, v * x, v * y, v]])

        U, S, Vt = np.linalg.svd(np.array(A), full_matrices=True)
        H = Vt[-1].reshape(3, 3)
        return H / H[2, 2]

    def get_robust_homography(self, src_pts, dst_pts):
        # RANSAC으로 이상치 제거 후 SVD 재계산
        _, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        mask = mask.ravel().astype(bool)
        return self.compute_homography_svd(src_pts[mask], dst_pts[mask])

    def manual_warp_perspective(self, src, H, canvas_shape):
        # Backward Mapping 기반 수동 워핑 (벡터화로 최적화)
        h, w = canvas_shape[:2]
        H_inv = np.linalg.inv(H)

        y_idx, x_idx = np.indices((h, w))
        coords = np.stack([x_idx.ravel(), y_idx.ravel(), np.ones_like(x_idx).ravel()])

        src_coords = H_inv @ coords
        src_x = np.round(src_coords[0] / src_coords[2]).astype(int)
        src_y = np.round(src_coords[1] / src_coords[2]).astype(int)

        valid = (src_x >= 0) & (src_x < src.shape[1]) & (src_y >= 0) & (src_y < src.shape[0])

        dst, mask = np.zeros((h, w, 3), dtype=src.dtype), np.zeros((h, w), dtype=np.float32)
        dst_y, dst_x = coords[1][valid].astype(int), coords[0][valid].astype(int)

        dst[dst_y, dst_x] = src[src_y[valid], src_x[valid]]
        mask[dst_y, dst_x] = 1.0

        return dst, mask

    def get_transformed_corners(self, img, H):
        # 변환 후, 이미지의 모서리가 위치할 좌표 계산
        h, w = img.shape[:2]
        corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
        return cv2.perspectiveTransform(corners, H).reshape(-1, 2)

    def run_4_images(self, images):
        # img1을 기준으로 특징점 매칭 및 homography 연산
        H_0to1 = self.get_robust_homography(*self.extract_and_match(images[0], images[1]))
        H_2to1 = self.get_robust_homography(*self.extract_and_match(images[2], images[1]))
        H_3to2 = self.get_robust_homography(*self.extract_and_match(images[3], images[2]))

        # chaining 적용
        H_matrices = [H_0to1, np.eye(3), H_2to1, H_2to1 @ H_3to2]

        # 파노라마 전체 캔버스 크기 계산
        all_corners = np.vstack([self.get_transformed_corners(images[i], H_matrices[i]) for i in range(4)])
        min_x, min_y = np.int32(all_corners.min(axis=0))
        max_x, max_y = np.int32(all_corners.max(axis=0))

        canvas_w, canvas_h = max_x - min_x, max_y - min_y
        T = np.array([[1, 0, -min_x], [0, 1, -min_y], [0, 0, 1]], dtype=np.float64)

        blended_canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.float32)
        weight_sum = np.zeros((canvas_h, canvas_w), dtype=np.float32)

        # 각 이미지 워핑 및 거리 기반 페더링 블렌딩 적용
        for i in range(4):
            warped_img, mask = self.manual_warp_perspective(images[i], T @ H_matrices[i], (canvas_h, canvas_w))
            dist_mask = get_distance_transform_mask(mask)

            for c in range(3):
                blended_canvas[:, :, c] += warped_img[:, :, c] * dist_mask
            weight_sum += dist_mask

        weight_sum[weight_sum == 0] = 1.0
        for c in range(3):
            blended_canvas[:, :, c] /= weight_sum

        return np.clip(blended_canvas, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    img_paths = [os.path.join(current_dir, f"img{i}.jpeg") for i in range(4)]
    images = [imread_robust(path) for path in img_paths]

    if any(img is None for img in images):
        print("이미지를 찾을 수 없습니다. 다시 확인해주세요.")
        exit()

    print("-> 원통형 투영 전처리 중...")
    images = [warp_to_cylinder(img) for img in images]

    print("-> 파노라마 스티칭 진행 중...")
    result_original = PanoramaStitcher().run_4_images(images)

    # 원본 이미지 저장 및 출력
    cv2.imshow("1. Original Panorama", result_original)
    cv2.imencode('.jpg', result_original)[1].tofile(os.path.join(current_dir, "Panorama_Result_Original.jpg"))

    print("-> 시네마틱 크롭 진행 중...")
    result_cropped = crop_perfect_rectangle(result_original)

    # 크롭된 이미지 저장 및 출력
    cv2.imshow("2. Cropped Cinematic Panorama", result_cropped)
    cv2.imencode('.jpg', result_cropped)[1].tofile(os.path.join(current_dir, "Panorama_Result_Cropped.jpg"))

    print("✅ 모든 작업 완료!")
    cv2.waitKey(0)
    cv2.destroyAllWindows()