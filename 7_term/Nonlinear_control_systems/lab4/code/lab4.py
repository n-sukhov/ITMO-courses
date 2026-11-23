from pathlib import Path
from math import sin, cos
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

h = 0.001
t = np.linspace(0, 10, 10001)


def system1(x):
    x1, x2 = x
    f1 = x2 + sin(x1) + x1**2
    phi = -x1 - sin(x1) - x1**2
    z2 = x2 - phi
    phi_dot = (-1 - cos(x1) - 2*x1)*f1
    u = (phi_dot - x1**2 - x1 - z2)/(2 + sin(x1))
    return np.array([f1, x1**2 + (2 + sin(x1))*u]), u


def system2(x):
    x1, x2 = x
    z2 = x2 + x1
    u = x1**3 - x1 - 2*z2
    return np.array([x2 - x1**3, x1 + u]), u


def system3(x):
    x1, x2, x3, x4 = x
    s, c = sin(x1), cos(x1)
    a, g2 = 1 - s, 2 - sin(x3)
    f1, f2, f3 = c - x2, x1 + x3, x1*x3 + g2*x4
    phi1 = c + x1
    z2 = x2 - phi1
    phi2 = a*f1 - z2
    z3 = x3 - phi2
    p, q = a*a - c*f1, -a - 1  # Производные phi2 по x1, x2.
    numerator = p*f1 + q*f2 - x1*x3 - z2 - z3
    phi3 = numerator/g2
    z4 = x4 - phi3
    p_x1 = -2*a*c + s*f1 + c*s
    numerator_x1 = p_x1*f1 - p*s + c*f2 + q - x3 + a + p
    numerator_x2 = c*f1 - p - 1 + q
    numerator_x3 = q - x1 - 1
    phi3_grad = np.array([numerator_x1/g2, numerator_x2/g2,
                         numerator_x3/g2 + numerator*cos(x3)/g2**2])
    phi3_dot = float(phi3_grad @ np.array([f1, f2, f3]))
    u = (phi3_dot - x2*x3 - g2*z3 - z4)/2
    return np.array([f1, f2, f3, x2*x3 + 2*u]), u


def rk4(system, initial):
    x = np.empty((len(t), len(initial)))
    x[0] = initial
    for i in range(len(t) - 1):
        k1 = system(x[i])[0]
        k2 = system(x[i] + h*k1/2)[0]
        k3 = system(x[i] + h*k2/2)[0]
        k4 = system(x[i] + h*k3)[0]
        x[i + 1] = x[i] + h*(k1 + 2*k2 + 2*k3 + k4)/6
    return x


plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"],
                     "font.size": 11, "mathtext.fontset": "stix"})
images = Path(__file__).resolve().parents[1] / "tex" / "images"
images.mkdir(parents=True, exist_ok=True)
problems = [(system1, [1, -0.5], [0, 0]),
            (system2, [1, -0.5], [0, 0]),
            (system3, [0.5, 1, -0.5, 0.25], [0, 1, 0, 0])]

for number, (system, initial, equilibrium) in enumerate(problems, 1):
    x = rk4(system, initial)[::10]
    u = np.array([system(state)[1] for state in x])
    deviations = x - equilibrium
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2),
                             gridspec_kw={"width_ratios": [1.2, 1]})
    for i in range(x.shape[1]):
        label = r"$x_2-1$" if number == 3 and i == 1 else rf"$x_{i+1}$"
        axes[0].plot(t[::10], deviations[:, i], label=label, linewidth=1.35)
    axes[0].set_ylabel(r"$x_i-x_i^*$")
    axes[0].legend(ncol=2, loc="upper right", fontsize=10)
    axes[1].plot(t[::10], u, color="#1f77b4", linewidth=1.35)
    axes[1].set_ylabel(r"$u$")
    for ax in axes:
        ax.set_xlabel(r"$t$, с")
        ax.grid(True, alpha=0.35, linewidth=0.6)
        ax.axhline(0, color="black", linewidth=0.55, alpha=0.5)
        ax.set_xlim(0, 10)
    fig.tight_layout(pad=0.7, w_pad=1)
    fig.savefig(images / f"system{number}.png", dpi=240)
    plt.close(fig)
