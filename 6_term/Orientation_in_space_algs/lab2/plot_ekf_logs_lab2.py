import argparse
import math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse


def wrap_angle(a):
    return (a + np.pi) % (2.0 * np.pi) - np.pi


def rmse(a):
    a = np.asarray(a, dtype=float)
    return float(np.sqrt(np.mean(a * a)))


def add_cov_ellipse(ax, x, y, P2, nsig=2.0):
    vals, vecs = np.linalg.eigh(P2)
    vals = np.maximum(vals, 1e-12)

    order = vals.argsort()[::-1]
    vals = vals[order]
    vecs = vecs[:, order]

    angle = math.degrees(math.atan2(vecs[1, 0], vecs[0, 0]))

    width = 2.0 * nsig * np.sqrt(vals[0])
    height = 2.0 * nsig * np.sqrt(vals[1])

    ellipse = Ellipse(
        xy=(x, y),
        width=width,
        height=height,
        angle=angle,
        fill=False,
        linewidth=1.0
    )

    ax.add_patch(ellipse)


def process_file(csv_path, out_dir):
    csv_path = Path(csv_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)

    ex_ekf = df["x_ekf"] - df["x_true"]
    ey_ekf = df["y_ekf"] - df["y_true"]
    eth_ekf = wrap_angle(df["theta_ekf"].to_numpy() - df["theta_true"].to_numpy())

    ex_odom = df["x_odom"] - df["x_true"]
    ey_odom = df["y_odom"] - df["y_true"]
    eth_odom = wrap_angle(df["theta_odom"].to_numpy() - df["theta_true"].to_numpy())

    pos_err_ekf = np.sqrt(ex_ekf ** 2 + ey_ekf ** 2)
    pos_err_odom = np.sqrt(ex_odom ** 2 + ey_odom ** 2)

    summary = {
        "file": csv_path.name,
        "rmse_pos_ekf_m": rmse(pos_err_ekf),
        "rmse_pos_odom_m": rmse(pos_err_odom),
        "rmse_theta_ekf_rad": rmse(eth_ekf),
        "rmse_theta_odom_rad": rmse(eth_odom),
        "mean_nis": float(np.nanmean(df["nis"])),
        "mean_nees": float(np.nanmean(df["nees"]))
    }

    stem = csv_path.stem

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.plot(df["x_true"], df["y_true"], label="истинная траектория")
    ax.plot(df["x_odom"], df["y_odom"], label="одометрия")
    ax.plot(df["x_ekf"], df["y_ekf"], label="EKF")

    step = max(len(df) // 20, 1)

    for i in range(0, len(df), step):
        P2 = np.array([
            [df["Pxx"].iloc[i], df["Pxy"].iloc[i]],
            [df["Pxy"].iloc[i], df["Pyy"].iloc[i]]
        ])

        add_cov_ellipse(
            ax,
            df["x_ekf"].iloc[i],
            df["y_ekf"].iloc[i],
            P2,
            nsig=2.0
        )

    ax.set_xlabel("x, м")
    ax.set_ylabel("y, м")
    ax.set_title("Траектории и ковариационные эллипсы EKF")
    ax.axis("equal")
    ax.grid(True)
    ax.legend()

    fig.tight_layout()
    fig.savefig(out_dir / f"{stem}_trajectory.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(df["t"], pos_err_odom, label="одометрия")
    ax.plot(df["t"], pos_err_ekf, label="EKF")

    ax.set_xlabel("t, c")
    ax.set_ylabel("ошибка положения, м")
    ax.set_title("Ошибка положения")
    ax.grid(True)
    ax.legend()

    fig.tight_layout()
    fig.savefig(out_dir / f"{stem}_position_error.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(df["t"], np.sqrt(df["Pxx"]), label="sigma x")
    ax.plot(df["t"], np.sqrt(df["Pyy"]), label="sigma y")
    ax.plot(df["t"], np.sqrt(df["Ptt"]), label="sigma theta")

    ax.set_xlabel("t, c")
    ax.set_ylabel("стандартное отклонение")
    ax.set_title("Ковариация EKF")
    ax.grid(True)
    ax.legend()

    fig.tight_layout()
    fig.savefig(out_dir / f"{stem}_covariance.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(df["t"], df["nis"], label="NIS")
    ax.plot(df["t"], df["nees"], label="NEES")

    ax.set_xlabel("t, c")
    ax.set_ylabel("значение")
    ax.set_title("NIS и NEES")
    ax.grid(True)
    ax.legend()

    fig.tight_layout()
    fig.savefig(out_dir / f"{stem}_nis_nees.png", dpi=200)
    plt.close(fig)

    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", nargs="+")
    parser.add_argument("--out", default="plots_lab2")

    args = parser.parse_args()

    summaries = []

    for csv_file in args.csv:
        summaries.append(process_file(csv_file, args.out))

    summary_df = pd.DataFrame(summaries)

    print(summary_df.to_string(index=False))

    Path(args.out).mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(Path(args.out) / "summary_metrics.csv", index=False)


if __name__ == "__main__":
    main()