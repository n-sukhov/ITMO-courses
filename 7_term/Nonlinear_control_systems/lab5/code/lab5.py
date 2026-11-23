from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

dt, epsilon = 0.001, 0.1
t = np.linspace(0, 12, 12001)
theta1, theta2 = 1, -1
a1, a2 = 2, 2


def rk4(f, x, h):
    k1 = f(x)
    k2 = f(x + h*k1/2)
    k3 = f(x + h*k2/2)
    k4 = f(x + h*k3)
    return x + h*(k1 + 2*k2 + 2*k3 + k4)/6


def model(x, case):
    x1, x2 = x
    if case == 1:
        s = x1 + x2 + np.sin(x1)
        beta = abs((1 + np.cos(x1))*(x2 + np.sin(x1))) + x1**2 + 1
        f, g = [x2 + np.sin(x1), theta1*x1**2], 2 + theta2
        u_eq = ((1 + np.cos(x1))*x1 - theta1*x1**2)/g
    else:
        s = 3*x1 + x2
        beta = abs(x2) + 2*abs(x1*np.sin(x1)) + 2*abs(x1*x2)/3 + 1
        f, g = [x2 + a1*x1*np.sin(x1), a2*x1*x2], 3
        u_eq = 3*x1 - a1*x1*np.sin(x1) + a2*x1**2
    return np.array(f), g, s, beta, u_eq


def rhs(x, case, mode):
    f, g, s, beta, _ = model(x, case)
    u = -beta*(np.clip(s/epsilon, -1, 1) if mode == "sat" else mode)
    return f + [0, g*u]


def slide(x, h, case):
    x1 = (x[0]*np.exp(-h) if case == 1 else
          rk4(lambda q: (-3 + a1*np.sin(q))*q, x[0], h))
    return np.array([x1, -x1 - np.sin(x1) if case == 1 else -3*x1])


def simulate(case, continuous=False):
    x = np.empty((len(t), 2))
    x[0] = [1, 0] if case == 1 else [1.5, 0]
    t_star = np.inf
    for i in range(len(t) - 1):
        if continuous:
            x[i+1] = rk4(lambda q: rhs(q, case, "sat"), x[i], dt)
        elif t[i] >= t_star:
            x[i+1] = slide(x[i], dt, case)
        else:
            s = model(x[i], case)[2]
            f = lambda q: rhs(q, case, np.sign(s))
            x[i+1] = rk4(f, x[i], dt)
            s_next = model(x[i+1], case)[2]
            if s*s_next <= 0:
                # Пересечение s=0 и переход к идеальному скольжению.
                h = dt*s/(s - s_next)
                t_star = t[i] + h
                x[i+1] = slide(rk4(f, x[i], h), dt - h, case)
    values = [model(q, case) for q in x]
    s = np.array([v[2] for v in values])
    u = np.array([-v[3]*np.clip(v[2]/epsilon, -1, 1) if continuous else
                  v[4] if time >= t_star else -v[3]*np.sign(v[2])
                  for time, v in zip(t, values)])
    return np.column_stack((x, s, u))


plt.rcParams.update({"font.family": "Times New Roman", "font.size": 11,
                     "mathtext.fontset": "stix"})
images = Path(__file__).resolve().parents[1]/"tex"/"images"
images.mkdir(parents=True, exist_ok=True)
for name, results, labels in [
    ("task1_comparison", [simulate(1), simulate(1, True)], ["Разрывный", "Непрерывный"]),
    ("task2_sliding", [simulate(2)], ["Разрывный"]),
]:
    fig, axes = plt.subplots(2, 2, figsize=(8, 5), sharex=True)
    for result, label in zip(results, labels):
        for ax, y, title in zip(axes.flat, result.T, [r"$x_1$", r"$x_2$", "$s$", "$u$"]):
            ax.plot(t, y, label=label, linewidth=1.55)
            ax.set(ylabel=title, xlim=(0, 12))
    for ax in axes.flat:
        ax.grid(True, color="0.87", linewidth=0.6)
        ax.axhline(0, color="0.5", linewidth=0.6, zorder=0)
    if len(results) == 2:
        axes[0, 0].legend(fontsize=10)
        for bound in [-epsilon, epsilon]:
            axes[1, 0].axhline(bound, color="0.5", linestyle="--", linewidth=0.8)
    for ax in axes[1]:
        ax.set_xlabel("t, с")
    fig.tight_layout(pad=0.8)
    fig.savefig(images/f"{name}.png", dpi=190)
    plt.close(fig)