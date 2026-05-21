import csv
import math
import os
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import matplotlib.pyplot as plt
import numpy as np

try:
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient
except ImportError:
    RemoteAPIClient = None


OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(OUT_DIR, "img", "raw")
PROC_DIR = os.path.join(OUT_DIR, "img", "processed")
RESULTS_DIR = os.path.join(OUT_DIR, "results")

ROBOT_PATH = "/PioneerP3DX"
CAMERA_PATH = "/PioneerP3DX/LineCamera"

START_SIMULATION = True
SET_ROBOT_POSE_FROM_SCRIPT = True
USE_STEPPING = False

IMG_W = 640
IMG_H = 480
ORTHO_VIEW_WIDTH_M = 0.187

LINE_CENTER_WORLD = np.array([0.0, 0.0], dtype=float)
LINE_LENGTH_M = 5.0
LINE_YAW_RAD = math.radians(0.0)

ROBOT_Z = 0.138
SETTLE_STEPS = 5
SETTLE_TIME_SEC = 0.10

CANNY_LOW = 50
CANNY_HIGH = 150
HOUGH_THRESHOLD = 50
HOUGH_MIN_LINE_LENGTH = 60
HOUGH_MAX_LINE_GAP = 20

DARK_THRESHOLD = 90
MIN_DETECTED_POINTS = 20

TESTS = [
    ("dist_0_00_angle_0", 0.00, 0.0, 0.0),
    ("dist_0_02_angle_0", 0.02, 0.0, 0.0),
    ("dist_0_04_angle_0", 0.04, 0.0, 0.0),
    ("dist_0_06_angle_0", 0.06, 0.0, 0.0),
    ("dist_0_08_angle_0", 0.08, 0.0, 0.0),

    ("dist_0_05_angle_p10", 0.05, 10.0, 0.0),
    ("dist_0_05_angle_m10", 0.05, -10.0, 0.0),
    ("dist_0_05_angle_p20", 0.05, 20.0, 0.0),
    ("dist_0_05_angle_m20", 0.05, -20.0, 0.0),
]

@dataclass
class LineEstimate:
    detected: bool
    d_m: float = float("nan")
    phi_rad: float = float("nan")
    points_count: int = 0
    method: str = "none"


def ensure_dirs() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROC_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)


def wrap_to_pi(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def wrap_to_half_pi(angle: float) -> float:
    angle = wrap_to_pi(angle)
    if angle > math.pi / 2.0:
        angle -= math.pi
    if angle < -math.pi / 2.0:
        angle += math.pi
    return angle

def line_angle_error_deg(phi_true_rad, phi_meas_rad):
    err = math.degrees(phi_meas_rad - phi_true_rad)
    err = (err + 90.0) % 180.0 - 90.0
    return err

def line_endpoints_world() -> Tuple[np.ndarray, np.ndarray]:
    direction = np.array([math.cos(LINE_YAW_RAD), math.sin(LINE_YAW_RAD)], dtype=float)
    p1 = LINE_CENTER_WORLD - 0.5 * LINE_LENGTH_M * direction
    p2 = LINE_CENTER_WORLD + 0.5 * LINE_LENGTH_M * direction
    return p1, p2


def desired_robot_pose(distance_m: float, rel_angle_deg: float, along_m: float) -> Tuple[float, float, float]:
    direction = np.array([math.cos(LINE_YAW_RAD), math.sin(LINE_YAW_RAD)], dtype=float)
    normal = np.array([-math.sin(LINE_YAW_RAD), math.cos(LINE_YAW_RAD)], dtype=float)
    pos = LINE_CENTER_WORLD + along_m * direction + distance_m * normal
    yaw = LINE_YAW_RAD + math.radians(rel_angle_deg)
    return float(pos[0]), float(pos[1]), float(yaw)


def world_to_camera_plane(point_world: np.ndarray, robot_x: float, robot_y: float, robot_yaw: float) -> np.ndarray:
    c = math.cos(robot_yaw)
    s = math.sin(robot_yaw)
    dx = float(point_world[0]) - robot_x
    dy = float(point_world[1]) - robot_y
    x_robot_forward = c * dx + s * dy
    y_robot_left = -s * dx + c * dy
    x_camera_right = -y_robot_left
    y_camera_forward = x_robot_forward
    return np.array([x_camera_right, y_camera_forward], dtype=float)


def fit_line_params(points_xy: np.ndarray) -> Tuple[float, float, float, float, float]:
    pts = points_xy.astype(np.float32)
    vx, vy, x0, y0 = cv2.fitLine(pts, cv2.DIST_L2, 0, 0.01, 0.01).reshape(-1)
    phi = math.atan2(float(vy), float(vx))
    phi = wrap_to_half_pi(phi)
    a = -float(vy)
    b = float(vx)
    n = math.sqrt(a * a + b * b)
    a /= n
    b /= n
    c = -(a * float(x0) + b * float(y0))
    d = c
    return d, phi, a, b, c


def true_line_in_camera(robot_x: float, robot_y: float, robot_yaw: float) -> Tuple[float, float]:
    p1_w, p2_w = line_endpoints_world()
    p1_c = world_to_camera_plane(p1_w, robot_x, robot_y, robot_yaw)
    p2_c = world_to_camera_plane(p2_w, robot_x, robot_y, robot_yaw)
    points = np.vstack([p1_c, p2_c])
    d, phi, _, _, _ = fit_line_params(points)
    return abs(d), phi


def image_to_metric_points(pixel_points_uv: np.ndarray, width: int, height: int) -> np.ndarray:
    mpp = ORTHO_VIEW_WIDTH_M / float(width)
    ortho_height_m = ORTHO_VIEW_WIDTH_M * float(height) / float(width)
    u = pixel_points_uv[:, 0].astype(float)
    v = pixel_points_uv[:, 1].astype(float)
    x = (u - 0.5 * (width - 1)) * mpp
    y = (0.5 * (height - 1) - v) * (ortho_height_m / float(height))
    return np.column_stack([x, y])


def detect_line_from_image(img_bgr: np.ndarray, debug_path: Optional[str] = None) -> LineEstimate:
    height, width = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, CANNY_LOW, CANNY_HIGH)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180.0,
        threshold=HOUGH_THRESHOLD,
        minLineLength=HOUGH_MIN_LINE_LENGTH,
        maxLineGap=HOUGH_MAX_LINE_GAP,
    )

    pts_uv: List[Tuple[int, int]] = []
    method = "hough"
    if lines is not None:
        for item in lines.reshape(-1, 4):
            x1, y1, x2, y2 = map(int, item)
            pts_uv.append((x1, y1))
            pts_uv.append((x2, y2))

    if len(pts_uv) < MIN_DETECTED_POINTS:
        method = "dark_mask"
        mask = gray < DARK_THRESHOLD
        ys, xs = np.where(mask)
        if len(xs) > 0:
            step = max(1, len(xs) // 3000)
            pts_uv = list(zip(xs[::step].astype(int), ys[::step].astype(int)))

    if len(pts_uv) < 2:
        if debug_path is not None:
            cv2.imwrite(debug_path, img_bgr)
        return LineEstimate(False, points_count=len(pts_uv), method="none")

    points_uv = np.array(pts_uv, dtype=np.float32)
    points_xy = image_to_metric_points(points_uv, width, height)
    d, phi, a, b, c = fit_line_params(points_xy)

    if debug_path is not None:
        debug = img_bgr.copy()
        if lines is not None:
            for item in lines.reshape(-1, 4):
                x1, y1, x2, y2 = map(int, item)
                cv2.line(debug, (x1, y1), (x2, y2), (0, 0, 255), 2)
        x0_px = int(np.mean(points_uv[:, 0]))
        y0_px = int(np.mean(points_uv[:, 1]))
        length = max(width, height)
        vx_px = math.cos(phi)
        vy_px = -math.sin(phi)
        p_a = (int(x0_px - length * vx_px), int(y0_px - length * vy_px))
        p_b = (int(x0_px + length * vx_px), int(y0_px + length * vy_px))
        cv2.line(debug, p_a, p_b, (0, 255, 0), 2)
        cv2.circle(debug, (width // 2, height // 2), 5, (255, 0, 0), -1)
        cv2.imwrite(debug_path, debug)

    return LineEstimate(True, abs(d), phi, len(pts_uv), method)


def connect_to_coppelia():
    if RemoteAPIClient is None:
        raise RuntimeError(
            "Не найден пакет coppeliasim_zmqremoteapi_client. Установите его: "
            "pip install coppeliasim-zmqremoteapi-client"
        )
    client = RemoteAPIClient()
    if hasattr(client, "require"):
        sim = client.require("sim")
    else:
        sim = client.getObject("sim")
    return client, sim


def get_handle(sim, path: str):
    try:
        return sim.getObject(path)
    except Exception as exc:
        raise RuntimeError(
            f"Не найден объект {path}. Проверьте имя/alias объекта в сцене CoppeliaSim."
        ) from exc


def get_camera_image_bgr(sim, cam) -> np.ndarray:
    data = sim.getVisionSensorImg(cam)
    if isinstance(data, tuple) and len(data) == 2:
        img, res = data
    elif isinstance(data, list) and len(data) == 2:
        img, res = data[0], data[1]
    else:
        raise RuntimeError("Неожиданный формат ответа sim.getVisionSensorImg")

    width, height = int(res[0]), int(res[1])
    if isinstance(img, bytes):
        arr = np.frombuffer(img, dtype=np.uint8)
    else:
        arr = np.array(img, dtype=np.uint8)
    arr = arr.reshape((height, width, 3))
    arr = cv2.flip(arr, 0)
    img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    return img_bgr


def wait_for_scene_update(client, sim) -> None:
    if USE_STEPPING:
        for _ in range(SETTLE_STEPS):
            client.step()
    else:
        for _ in range(SETTLE_STEPS):
            sim.wait(SETTLE_TIME_SEC)


def save_csv(rows: List[dict]) -> str:
    path = os.path.join(RESULTS_DIR, "measurements.csv")
    fieldnames = [
        "test",
        "robot_x_m",
        "robot_y_m",
        "robot_yaw_deg",
        "true_distance_m",
        "measured_distance_m",
        "distance_error_m",
        "true_angle_deg",
        "measured_angle_deg",
        "angle_error_deg",
        "detected",
        "points_count",
        "method",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    return path


def plot_results(rows: List[dict]) -> None:
    idx = np.arange(1, len(rows) + 1)
    detected = np.array([bool(r["detected"]) for r in rows], dtype=bool)
    dist_err = np.array([float(r["distance_error_m"]) for r in rows], dtype=float)
    ang_err = np.array([float(r["angle_error_deg"]) for r in rows], dtype=float)
    true_d = np.array([float(r["true_distance_m"]) for r in rows], dtype=float)
    meas_d = np.array([float(r["measured_distance_m"]) for r in rows], dtype=float)
    true_phi = np.array([float(r["true_angle_deg"]) for r in rows], dtype=float)
    meas_phi = np.array([float(r["measured_angle_deg"]) for r in rows], dtype=float)

    plt.figure(figsize=(9, 5))
    plt.plot(idx, true_d, marker="o", label="Истинное расстояние")
    plt.plot(idx, meas_d, marker="s", label="Измеренное расстояние")
    plt.xlabel("Номер опыта")
    plt.ylabel("Расстояние, м")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "distance_true_vs_measured.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.plot(idx, dist_err * 100.0, marker="o")
    plt.xlabel("Номер опыта")
    plt.ylabel("Ошибка расстояния, см")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "distance_error.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.plot(idx, true_phi, marker="o", label="Истинный угол")
    plt.plot(idx, meas_phi, marker="s", label="Измеренный угол")
    plt.xlabel("Номер опыта")
    plt.ylabel("Угол линии, град")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "angle_true_vs_measured.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.plot(idx, ang_err, marker="o")
    plt.xlabel("Номер опыта")
    plt.ylabel("Ошибка угла, град")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "angle_error.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.bar(idx, detected.astype(int))
    plt.xlabel("Номер опыта")
    plt.ylabel("Детекция: 1 — успешно, 0 — нет")
    plt.ylim(-0.05, 1.05)
    plt.grid(True, axis="y")
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "detection_success.png"), dpi=200)
    plt.close()


def run_experiment() -> None:
    ensure_dirs()
    client, sim = connect_to_coppelia()
    robot = get_handle(sim, ROBOT_PATH)
    cam = get_handle(sim, CAMERA_PATH)

    if USE_STEPPING:
        client.setStepping(True)

    if START_SIMULATION:
        state = sim.getSimulationState()
        if state == sim.simulation_stopped:
            sim.startSimulation()
            time.sleep(0.5)

    rows: List[dict] = []
    for i, (name, distance_m, rel_angle_deg, along_m) in enumerate(TESTS, start=1):
        robot_x, robot_y, robot_yaw = desired_robot_pose(distance_m, rel_angle_deg, along_m)
        if SET_ROBOT_POSE_FROM_SCRIPT:
            sim.setObjectPosition(robot, -1, [robot_x, robot_y, ROBOT_Z])
            sim.setObjectOrientation(robot, -1, [0.0, 0.0, robot_yaw])
            wait_for_scene_update(client, sim)

        img_bgr = get_camera_image_bgr(sim, cam)
        raw_path = os.path.join(RAW_DIR, f"{i:02d}_{name}.png")
        debug_path = os.path.join(PROC_DIR, f"{i:02d}_{name}_detected.png")
        cv2.imwrite(raw_path, img_bgr)

        estimate = detect_line_from_image(img_bgr, debug_path=debug_path)
        true_d, true_phi = true_line_in_camera(robot_x, robot_y, robot_yaw)

        if estimate.detected:
            measured_d = estimate.d_m
            measured_phi = estimate.phi_rad
            d_err = measured_d - true_d
            phi_err = line_angle_error_deg(true_phi, measured_phi)
        else:
            measured_d = float("nan")
            measured_phi = float("nan")
            d_err = float("nan")
            phi_err = float("nan")

        row = {
            "test": name,
            "robot_x_m": f"{robot_x:.4f}",
            "robot_y_m": f"{robot_y:.4f}",
            "robot_yaw_deg": f"{math.degrees(robot_yaw):.4f}",
            "true_distance_m": f"{true_d:.5f}",
            "measured_distance_m": f"{measured_d:.5f}",
            "distance_error_m": f"{d_err:.5f}",
            "true_angle_deg": f"{math.degrees(true_phi):.5f}",
            "measured_angle_deg": f"{math.degrees(measured_phi):.5f}",
            "angle_error_deg": f"{phi_err:.5f}",
            "detected": estimate.detected,
            "points_count": estimate.points_count,
            "method": estimate.method,
        }
        rows.append(row)
        print(
            f"[{i:02d}] {name}: detected={estimate.detected}, "
            f"d_true={true_d:.3f} m, d_meas={measured_d:.3f} m, "
            f"phi_true={math.degrees(true_phi):.2f} deg, phi_meas={math.degrees(measured_phi):.2f} deg"
        )

    csv_path = save_csv(rows)
    plot_results(rows)

    success_rate = sum(1 for r in rows if r["detected"]) / len(rows)
    print("\nГотово")
    print(f"CSV: {csv_path}")
    print(f"Сырые изображения: {RAW_DIR}")
    print(f"Изображения с детекцией: {PROC_DIR}")
    print(f"Графики: {RESULTS_DIR}")
    print(f"Доля успешных детекций: {success_rate:.3f}")


if __name__ == "__main__":
    run_experiment()
