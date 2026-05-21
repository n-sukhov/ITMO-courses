import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse


SEED = 42
DT = 0.1
N_STEPS = 700
MAX_RANGE = 6.5
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
IMG_DIR = os.path.join(BASE_DIR, "img")

LANDMARKS_TRUE = np.array([
    [3.5, 0.5],
    [6.0, 3.5],
    [3.2, 7.0],
    [-1.0, 7.7],
    [-4.2, 5.5],
    [-4.4, 1.5],
    [-1.0, -1.0],
    [2.0, 3.8],
], dtype=float)

Q_BASE = np.diag([0.12 ** 2, np.deg2rad(1.5) ** 2])
R_BASE = np.diag([0.02 ** 2, 0.02 ** 2, np.deg2rad(0.7) ** 2])
P0_ROBOT = np.diag([0.35 ** 2, 0.35 ** 2, np.deg2rad(8.0) ** 2])


def normalize_angle(a):
    return (a + np.pi) % (2.0 * np.pi) - np.pi


def control_input(k):
    t = k * DT
    v = 0.75 + 0.08 * np.sin(0.20 * t)
    omega = 0.19 + 0.04 * np.sin(0.17 * t)
    return np.array([v, omega], dtype=float)


def motion_model(x, u, dt):
    y = x.copy()
    v, omega = u
    theta = x[2]
    y[0] = x[0] + v * dt * np.cos(theta)
    y[1] = x[1] + v * dt * np.sin(theta)
    y[2] = normalize_angle(x[2] + omega * dt)
    return y


def predict(mu, P, u, R, dt):
    n = mu.size
    v, omega = u
    theta = mu[2]

    F = np.eye(n)
    F[0, 2] = -v * dt * np.sin(theta)
    F[1, 2] = v * dt * np.cos(theta)

    mu = mu.copy()
    mu[0] = mu[0] + v * dt * np.cos(theta)
    mu[1] = mu[1] + v * dt * np.sin(theta)
    mu[2] = normalize_angle(mu[2] + omega * dt)

    P = F @ P @ F.T
    P[:3, :3] += R
    P = 0.5 * (P + P.T)
    return mu, P


def measurement_model(robot_pose, landmark_pos):
    x, y, theta = robot_pose
    dx = landmark_pos[0] - x
    dy = landmark_pos[1] - y
    r = np.sqrt(dx * dx + dy * dy)
    b = normalize_angle(np.arctan2(dy, dx) - theta)
    return np.array([r, b], dtype=float)


def generate_measurements(x_true, landmarks, Q, max_range, rng):
    measurements = []
    sigma_r = np.sqrt(Q[0, 0])
    sigma_b = np.sqrt(Q[1, 1])

    for lm_id, lm in enumerate(landmarks):
        z_true = measurement_model(x_true, lm)
        if z_true[0] <= max_range:
            z = z_true.copy()
            z[0] += rng.normal(0.0, sigma_r)
            z[1] = normalize_angle(z[1] + rng.normal(0.0, sigma_b))
            measurements.append((lm_id, z))

    return measurements


def initialize_landmark(mu, P, lm_id, z, Q, landmark_to_index):
    r, b = z
    x, y, theta = mu[:3]
    alpha = normalize_angle(theta + b)

    lm = np.array([
        x + r * np.cos(alpha),
        y + r * np.sin(alpha),
    ], dtype=float)

    n_old = mu.size
    n_new = n_old + 2
    mu_new = np.zeros(n_new)
    mu_new[:n_old] = mu
    mu_new[n_old:n_new] = lm

    Gx = np.array([
        [1.0, 0.0, -r * np.sin(alpha)],
        [0.0, 1.0,  r * np.cos(alpha)],
    ])

    Gz = np.array([
        [np.cos(alpha), -r * np.sin(alpha)],
        [np.sin(alpha),  r * np.cos(alpha)],
    ])

    P_new = np.zeros((n_new, n_new))
    P_new[:n_old, :n_old] = P

    cross = Gx @ P[:3, :]
    P_new[n_old:n_new, :n_old] = cross
    P_new[:n_old, n_old:n_new] = cross.T
    P_new[n_old:n_new, n_old:n_new] = Gx @ P[:3, :3] @ Gx.T + Gz @ Q @ Gz.T
    P_new = 0.5 * (P_new + P_new.T)

    landmark_to_index[lm_id] = n_old
    return mu_new, P_new


def update_landmark(mu, P, lm_id, z, Q, landmark_to_index):
    lm_index = landmark_to_index[lm_id]
    x, y, theta = mu[:3]
    mx, my = mu[lm_index:lm_index + 2]

    dx = mx - x
    dy = my - y
    q = dx * dx + dy * dy
    q = max(q, 1e-12)
    sqrt_q = np.sqrt(q)

    z_hat = np.array([
        sqrt_q,
        normalize_angle(np.arctan2(dy, dx) - theta),
    ])

    innovation = np.array([
        z[0] - z_hat[0],
        normalize_angle(z[1] - z_hat[1]),
    ])

    n = mu.size
    H = np.zeros((2, n))

    H[0, 0] = -dx / sqrt_q
    H[0, 1] = -dy / sqrt_q
    H[0, 2] = 0.0
    H[1, 0] = dy / q
    H[1, 1] = -dx / q
    H[1, 2] = -1.0

    H[0, lm_index] = dx / sqrt_q
    H[0, lm_index + 1] = dy / sqrt_q
    H[1, lm_index] = -dy / q
    H[1, lm_index + 1] = dx / q

    S = H @ P @ H.T + Q
    K = P @ H.T @ np.linalg.inv(S)

    mu = mu + K @ innovation
    mu[2] = normalize_angle(mu[2])

    I = np.eye(n)
    P = (I - K @ H) @ P @ (I - K @ H).T + K @ Q @ K.T
    P = 0.5 * (P + P.T)

    nis = float(innovation.T @ np.linalg.inv(S) @ innovation)
    return mu, P, nis


def covariance_ellipse_params(P2, n_std=2.0):
    vals, vecs = np.linalg.eigh(P2)
    vals = np.maximum(vals, 0.0)
    order = vals.argsort()[::-1]
    vals = vals[order]
    vecs = vecs[:, order]
    angle = np.degrees(np.arctan2(vecs[1, 0], vecs[0, 0]))
    width = 2.0 * n_std * np.sqrt(vals[0])
    height = 2.0 * n_std * np.sqrt(vals[1])
    return width, height, angle


def run_ekf_slam(q_factor=1.0, r_factor=1.0, max_range=MAX_RANGE, seed=SEED):
    rng = np.random.default_rng(seed)
    Q = Q_BASE * q_factor
    R = R_BASE * r_factor

    x_true = np.array([0.0, 0.0, np.deg2rad(8.0)], dtype=float)
    mu = np.array([0.25, -0.25, np.deg2rad(4.0)], dtype=float)
    P = P0_ROBOT.copy()
    landmark_to_index = {}

    true_history = np.zeros((N_STEPS + 1, 3))
    est_history = np.zeros((N_STEPS + 1, 3))
    visible_count_history = np.zeros(N_STEPS + 1)
    nis_history = []

    true_history[0] = x_true
    est_history[0] = mu[:3]

    for k in range(1, N_STEPS + 1):
        u = control_input(k - 1)

        process_noise = rng.multivariate_normal(np.zeros(3), R)
        x_true = motion_model(x_true, u, DT)
        x_true += process_noise
        x_true[2] = normalize_angle(x_true[2])

        mu, P = predict(mu, P, u, R, DT)

        measurements = generate_measurements(x_true, LANDMARKS_TRUE, Q, max_range, rng)
        visible_count_history[k] = len(measurements)

        for lm_id, z in measurements:
            if lm_id not in landmark_to_index:
                mu, P = initialize_landmark(mu, P, lm_id, z, Q, landmark_to_index)
            else:
                mu, P, nis = update_landmark(mu, P, lm_id, z, Q, landmark_to_index)
                nis_history.append(nis)

        true_history[k] = x_true
        est_history[k] = mu[:3]

    pos_errors = est_history[:, :2] - true_history[:, :2]
    theta_errors = np.array([normalize_angle(a) for a in est_history[:, 2] - true_history[:, 2]])
    pos_error_norm = np.linalg.norm(pos_errors, axis=1)
    rmse_position = float(np.sqrt(np.mean(pos_error_norm ** 2)))
    rmse_x = float(np.sqrt(np.mean(pos_errors[:, 0] ** 2)))
    rmse_y = float(np.sqrt(np.mean(pos_errors[:, 1] ** 2)))
    rmse_theta_deg = float(np.rad2deg(np.sqrt(np.mean(theta_errors ** 2))))

    landmark_errors = []
    estimated_landmarks = {}
    for lm_id, start_index in landmark_to_index.items():
        est_lm = mu[start_index:start_index + 2]
        estimated_landmarks[lm_id] = est_lm
        landmark_errors.append(np.linalg.norm(est_lm - LANDMARKS_TRUE[lm_id]))

    mean_landmark_error = float(np.mean(landmark_errors)) if landmark_errors else np.nan
    max_landmark_error = float(np.max(landmark_errors)) if landmark_errors else np.nan

    result = {
        "true_history": true_history,
        "est_history": est_history,
        "pos_errors": pos_errors,
        "theta_errors": theta_errors,
        "pos_error_norm": pos_error_norm,
        "visible_count_history": visible_count_history,
        "nis_history": np.array(nis_history),
        "mu": mu,
        "P": P,
        "landmark_to_index": landmark_to_index,
        "estimated_landmarks": estimated_landmarks,
        "metrics": {
            "q_factor": q_factor,
            "r_factor": r_factor,
            "max_range": max_range,
            "steps": N_STEPS,
            "landmarks_total": LANDMARKS_TRUE.shape[0],
            "landmarks_initialized": len(landmark_to_index),
            "rmse_position": rmse_position,
            "rmse_x": rmse_x,
            "rmse_y": rmse_y,
            "rmse_theta_deg": rmse_theta_deg,
            "mean_landmark_error": mean_landmark_error,
            "max_landmark_error": max_landmark_error,
            "mean_visible_landmarks": float(np.mean(visible_count_history[1:])),
            "mean_nis": float(np.mean(nis_history)) if nis_history else np.nan,
        },
    }
    return result


def plot_nominal_result(result, img_dir=IMG_DIR):
    os.makedirs(img_dir, exist_ok=True)

    true_history = result["true_history"]
    est_history = result["est_history"]
    P = result["P"]
    landmark_to_index = result["landmark_to_index"]
    estimated_landmarks = result["estimated_landmarks"]
    pos_errors = result["pos_errors"]
    theta_errors = result["theta_errors"]
    pos_error_norm = result["pos_error_norm"]
    visible_count_history = result["visible_count_history"]
    nis_history = result["nis_history"]
    t = np.arange(N_STEPS + 1) * DT

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.plot(true_history[:, 0], true_history[:, 1], label="Истинная траектория")
    ax.plot(est_history[:, 0], est_history[:, 1], "--", label="Оцененная траектория EKF-SLAM")
    ax.scatter(LANDMARKS_TRUE[:, 0], LANDMARKS_TRUE[:, 1], marker="*", s=140, label="Истинные метки")

    if estimated_landmarks:
        ids = sorted(estimated_landmarks.keys())
        est_lm_arr = np.array([estimated_landmarks[i] for i in ids])
        ax.scatter(est_lm_arr[:, 0], est_lm_arr[:, 1], marker="x", s=70, label="Оцененные метки")

        for lm_id in ids:
            idx = landmark_to_index[lm_id]
            lm = estimated_landmarks[lm_id]
            width, height, angle = covariance_ellipse_params(P[idx:idx + 2, idx:idx + 2], n_std=2.0)
            ell = Ellipse(xy=lm, width=width, height=height, angle=angle, fill=False, linewidth=1.2)
            ax.add_patch(ell)
            ax.text(lm[0] + 0.12, lm[1] + 0.12, str(lm_id), fontsize=9)

    ax.set_title("EKF-SLAM: траектория робота и карта меток")
    ax.set_xlabel("x, м")
    ax.set_ylabel("y, м")
    ax.axis("equal")
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(img_dir, "trajectory_landmarks.png"), dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(t, pos_errors[:, 0], label="Ошибка x")
    ax.plot(t, pos_errors[:, 1], label="Ошибка y")
    ax.plot(t, np.rad2deg(theta_errors), label="Ошибка theta, град")
    ax.set_title("Ошибки оценки состояния робота")
    ax.set_xlabel("t, с")
    ax.set_ylabel("Ошибка")
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(img_dir, "robot_state_errors.png"), dpi=220)
    plt.close(fig)

    cumulative_rmse = np.sqrt(np.cumsum(pos_error_norm ** 2) / np.arange(1, N_STEPS + 2))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(t, pos_error_norm, label="Текущая ошибка положения")
    ax.plot(t, cumulative_rmse, "--", label="Накопленный RMSE")
    ax.set_title("Ошибка положения робота и RMSE")
    ax.set_xlabel("t, с")
    ax.set_ylabel("Ошибка, м")
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(img_dir, "position_rmse.png"), dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(t, visible_count_history)
    ax.set_title("Количество видимых меток во времени")
    ax.set_xlabel("t, с")
    ax.set_ylabel("Количество меток")
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(os.path.join(img_dir, "visible_landmarks.png"), dpi=220)
    plt.close(fig)

    if nis_history.size > 0:
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(nis_history)
        ax.axhline(2.0, linestyle="--", label="Ожидаемое среднее NIS для 2 измерений")
        ax.set_title("NIS для измерений дальность-азимут")
        ax.set_xlabel("Номер обновления")
        ax.set_ylabel("NIS")
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(img_dir, "nis.png"), dpi=220)
        plt.close(fig)


def run_sensitivity_experiments(img_dir=IMG_DIR):
    os.makedirs(img_dir, exist_ok=True)
    experiments = [
        ("Базовый", 1.0, 1.0, MAX_RANGE),
        ("Q x 4", 4.0, 1.0, MAX_RANGE),
        ("R x 4", 1.0, 4.0, MAX_RANGE),
        ("Радиус 4 м", 1.0, 1.0, 4.0),
    ]

    rows = []
    for name, q_factor, r_factor, max_range in experiments:
        res = run_ekf_slam(q_factor=q_factor, r_factor=r_factor, max_range=max_range, seed=SEED)
        m = res["metrics"]
        rows.append([
            name,
            m["rmse_position"],
            m["rmse_theta_deg"],
            m["mean_landmark_error"],
            m["landmarks_initialized"],
            m["mean_visible_landmarks"],
            m["mean_nis"],
        ])

    labels = [r[0] for r in rows]
    rmse_values = [r[1] for r in rows]
    landmark_values = [r[3] for r in rows]

    x = np.arange(len(labels))
    width = 0.36
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - width / 2, rmse_values, width, label="RMSE положения, м")
    ax.bar(x + width / 2, landmark_values, width, label="Средняя ошибка меток, м")
    ax.set_title("Чувствительность EKF-SLAM к шумам и радиусу наблюдения")
    ax.set_ylabel("Ошибка, м")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.grid(True, axis="y")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(img_dir, "noise_sensitivity.png"), dpi=220)
    plt.close(fig)

    table_path = os.path.join(img_dir, "sensitivity_results.csv")
    with open(table_path, "w", encoding="utf-8") as f:
        f.write("experiment,rmse_position_m,rmse_theta_deg,mean_landmark_error_m,initialized_landmarks,mean_visible_landmarks,mean_nis\n")
        for row in rows:
            f.write(",".join([str(row[0])] + [f"{v:.6f}" if isinstance(v, float) else str(v) for v in row[1:]]) + "\n")

    return rows


def print_metrics(metrics):
    print("\nИтоговые метрики базового эксперимента")
    print(f"Количество шагов: {metrics['steps']}")
    print(f"Всего меток: {metrics['landmarks_total']}")
    print(f"Инициализировано меток: {metrics['landmarks_initialized']}")
    print(f"Среднее число видимых меток: {metrics['mean_visible_landmarks']:.3f}")
    print(f"RMSE положения робота: {metrics['rmse_position']:.4f} м")
    print(f"RMSE по x: {metrics['rmse_x']:.4f} м")
    print(f"RMSE по y: {metrics['rmse_y']:.4f} м")
    print(f"RMSE по theta: {metrics['rmse_theta_deg']:.4f} град")
    print(f"Средняя ошибка по меткам: {metrics['mean_landmark_error']:.4f} м")
    print(f"Максимальная ошибка по меткам: {metrics['max_landmark_error']:.4f} м")
    print(f"Среднее NIS: {metrics['mean_nis']:.4f}")


def print_sensitivity_table(rows):
    print("\nИсследование чувствительности")
    print(f"{'Эксперимент':<14} {'RMSE, м':>10} {'theta, град':>12} {'Ошибка меток, м':>16} {'Метки':>8} {'Видно':>8} {'NIS':>8}")

    for row in rows:
        name, rmse, theta_rmse, lm_err, initialized, visible, nis = row
        print(f"{name:<14} {rmse:>10.4f} {theta_rmse:>12.4f} {lm_err:>16.4f} {initialized:>8} {visible:>8.3f} {nis:>8.3f}")


def main():
    os.makedirs(IMG_DIR, exist_ok=True)

    nominal = run_ekf_slam(q_factor=1.0, r_factor=1.0, max_range=MAX_RANGE, seed=SEED)
    plot_nominal_result(nominal, IMG_DIR)
    rows = run_sensitivity_experiments(IMG_DIR)

    print_metrics(nominal["metrics"])
    print_sensitivity_table(rows)
    print("\nСохраненные файлы:")
    print(f"  {IMG_DIR}/trajectory_landmarks.png")
    print(f"  {IMG_DIR}/robot_state_errors.png")
    print(f"  {IMG_DIR}/position_rmse.png")
    print(f"  {IMG_DIR}/visible_landmarks.png")
    print(f"  {IMG_DIR}/nis.png")
    print(f"  {IMG_DIR}/noise_sensitivity.png")
    print(f"  {IMG_DIR}/sensitivity_results.csv")


if __name__ == "__main__":
    main()
