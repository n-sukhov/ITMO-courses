# %%
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.integrate import quad
import warnings
from scipy.integrate import IntegrationWarning
warnings.filterwarnings("ignore", category=IntegrationWarning)  
%matplotlib widget

# %% [markdown]
# Util-функции

# %%
def draw_plots(rows, cols, width, height, subplot_data):
    fig, axes = plt.subplots(rows, cols, figsize=(width, height))
    axes = axes.flatten() if rows * cols > 1 else [axes]

    flat_data = [item for row in subplot_data for item in row]

    for idx, data in enumerate(flat_data):
        if idx >= len(axes):
            raise ValueError(f"Too many subplots provided in \
                'subplot_data': expected at most {rows * cols}, got more.")
        if not data:
            continue

        ax = axes[idx]

        (
            x_arrays, y_arrays,
            labels,
            x_label, y_label,
            colors, linestyles,
            linewidth, markers,
            markersizes, title,
            markerevery
        ) = data + (None,) * (12 - len(data))

        num_plots = len(y_arrays)

        for i in range(num_plots):
            x = x_arrays[i]
            y = y_arrays[i]

            label = labels[i] if labels and i < len(labels) else None
            color = colors[i] if colors and i < len(colors) else None
            linestyle = linestyles[i] if linestyles and i < len(linestyles) else '-'
            lw = linewidth[i] if linewidth and i < len(linewidth) else 2
            marker = markers[i] if markers and i < len(markers) else None
            markersize = markersizes[i] if markersizes and i < len(markersizes) else None
            mevery = markerevery[i] if markerevery and i < len(markerevery) else None

            ax.plot(x, y,
                    label=label,
                    color=color,
                    linestyle=linestyle,
                    linewidth=lw,
                    marker=marker,
                    markersize=markersize,
                    markevery=mevery)

        if labels:
            ax.legend()
        ax.grid(True)
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)
        if title:
            ax.set_title(title)
    
    for idx in range(len(flat_data), len(axes)):
        fig.delaxes(axes[idx])
        
    plt.gca().set_axisbelow(True) 
    plt.tight_layout()
    plt.show()

# %% [markdown]
# Наборы значений

# %%
ab = ((1, 3), (2, 2), (3, 1))

# %% [markdown]
# # Задание 1
# 
# #### Функции

# %%
rect_func = lambda t, a, b: a if abs(t) <= b else 0
triangle_func = lambda t, a, b: a - abs(a * t / b) if abs(t) <= b else 0
card_sin = lambda t, a, b: a * np.sin(b * t) / (b * t)
hauss = lambda t, a, b: a * np.exp(- b * t * t)
two_way_attenuation = lambda t, a, b: a * np.exp(- b * abs(t))

# %% [markdown]
# #### Фурье-образы функций

# %%
fourier_transform_rect_func = lambda w, a, b: a * np.sqrt(2) * np.sin(w * b) / (w * np.sqrt(np.pi))
fourier_transform_triangle_func = lambda w, a, b: 2 * np.sqrt(2) * a * np.sin(w * b / 2) ** 2 / (w * w * b * np.sqrt(np.pi))
fourier_transform_card_sin = lambda w, a, b: np.sqrt(np.pi / 2) * a / b if abs(w) < b else 0
fourier_transform_hauss = lambda w, a, b: a * np.sqrt(1 / (2 * b)) * np.exp(- w * w / (4 * b))
fourier_transform_two_way_attenuation = lambda w, a, b: a * b * np.sqrt(2 / np.pi) / (b * b + w * w)

# %% [markdown]
# #### Проверка равенства Парсеваля

# %%
def parseval_check(function_1, function_2, args):
    limits=(-np.inf, np.inf)
    t_integrand = lambda t: np.abs(function_1(t, *args))**2
    t_integral, _ = quad(t_integrand, limits[0], limits[1], limit=1000)

    w_integrand = lambda w: np.abs(function_2(w, *args))**2
    w_integral, _ = quad(w_integrand, limits[0], limits[1], limit=1000)

    relative_error = np.abs(t_integral - w_integral) / max(t_integral, w_integral)
    latex_output = r"""\noindent
$\text{$|||f(t)||^2 - ||f(\omega)||^2| = %.3e$}$\\
$||f(t)||^2 = %.5f$\\
$||f(\omega)||^2 = %.5f$\\
""" % (relative_error, t_integral, w_integral)

    print(latex_output)

# %% [markdown]
# ### Построим графики

# %%
t_spaces = [
    np.linspace(-12, 12, 1000), 
    np.linspace(-12, 12, 1000), 
    np.linspace(-12, 12, 1000), 
    np.linspace(-12, 12, 1000), 
    np.linspace(-12, 12, 1000)
]
w_spaces = [
    np.linspace(-12, 12, 1000), 
    np.linspace(-12, 12, 1000), 
    np.linspace(-12, 12, 1000), 
    np.linspace(-12, 12, 1000), 
    np.linspace(-12, 12, 1000)
]
ft = [
    [[rect_func(t, a, b) for t in t_spaces[0]] for (a, b) in ab],
    [[triangle_func(t, a, b) for t in t_spaces[1]] for (a, b) in ab],
    [[card_sin(t, a, b) for t in t_spaces[2]] for (a, b) in ab],
    [[hauss(t, a, b) for t in t_spaces[3]] for (a, b) in ab],
    [[two_way_attenuation(t, a, b) for t in t_spaces[4]] for (a, b) in ab]
]
fw = [
    [[fourier_transform_rect_func(w, a, b) for w in w_spaces[0]] for (a, b) in ab],
    [[fourier_transform_triangle_func(w, a, b) for w in w_spaces[1]] for (a, b) in ab],
    [[fourier_transform_card_sin(w, a, b) for w in w_spaces[2]] for (a, b) in ab],
    [[fourier_transform_hauss(w, a, b) for w in w_spaces[3]] for (a, b) in ab],
    [[fourier_transform_two_way_attenuation(w, a, b) for w in w_spaces[4]] for (a, b) in ab]
]

# %%
colors = ['blue', 'green', 'red']
linestyles = ['-', '-', '-']
labels = [f"(a={a}, b={b})" for (a, b) in ab]

subplot_data = []

for i in range(5):
    time_plot = (
        [t_spaces[i]] * len(ab),
        ft[i],
        labels,
        "t, sec", "f(t)",
        colors, linestyles,
        [1.5]*len(ab),
        [None]*len(ab),
        [None]*len(ab)
    )

    freq_plot = (
        [w_spaces[i]] * len(ab),
        fw[i],
        labels,
        "w, rad/sec", "f(w)",
        colors, linestyles,
        [1.5]*len(ab),
        [None]*len(ab),
        [None]*len(ab)
    )

    subplot_data.append([time_plot, freq_plot])

# %% [markdown]
# #### Прямоугольная функция

# %%
draw_plots(rows=2, cols=1, width=9, height=6, subplot_data=[[plot] for plot in subplot_data[0]])
for a, b in ab:
    print(r"\newline\noindent$a=%.2f, b=%.2f:$\\" % (a, b)) 
    parseval_check(rect_func, fourier_transform_rect_func, (a, b))

# %% [markdown]
# #### Треугольная функция

# %%
draw_plots(rows=2, cols=1, width=9, height=6, subplot_data=[[plot] for plot in subplot_data[1]])
for a, b in ab:
    print(r"\newline\noindent$a=%.2f, b=%.2f:$\\" % (a, b)) 
    parseval_check(triangle_func, fourier_transform_triangle_func, (a, b))

# %% [markdown]
# #### Кардинальный синус

# %%
draw_plots(rows=2, cols=1, width=9, height=6, subplot_data=[[plot] for plot in subplot_data[2]])
for a, b in ab:
    print(r"\newline\noindent$a=%.2f, b=%.2f:$\\" % (a, b)) 
    parseval_check(card_sin, fourier_transform_card_sin, (a, b))

# %% [markdown]
# #### Функция Гаусса

# %%
draw_plots(rows=2, cols=1, width=9, height=6, subplot_data=[[plot] for plot in subplot_data[3]])
for a, b in ab:
    print(r"\newline\noindent$a=%.2f, b=%.2f:$\\" % (a, b)) 
    parseval_check(hauss, fourier_transform_hauss, (a, b))

# %% [markdown]
# #### Двустороннее затухание

# %%
draw_plots(rows=2, cols=1, width=9, height=6, subplot_data=[[plot] for plot in subplot_data[4]])
for a, b in ab:
    print(r"\newline\noindent$a=%.2f, b=%.2f:$\\" % (a, b)) 
    parseval_check(two_way_attenuation, fourier_transform_two_way_attenuation, (a, b))

# %% [markdown]
# # Задание 2
# 

# %%
c_coefs = (-2, -1, 1, 2)
g = lambda t, c: 3 if abs(t+c) <= 1 else 0
fourier_transform_g = lambda w, c: 3 * np.sqrt(2) * np.sin(w) * np.exp(1j * w * c) / (w * np.sqrt(np.pi))
t_space = np.linspace(-8, 8, 1000)
w_space = np.linspace(-8, 8, 1000)
gt = [[g(t,c) for t in t_space] for c in c_coefs]
gw = [[fourier_transform_g(w, c) for w in w_space] for c in c_coefs]

# %%
colors = ['blue', 'green', 'red', 'magenta']
linestyles = ['--']
labels = [f"c={c}" for c in c_coefs]

subplot_data2 = [[
    (
    [t_space] * len(c_coefs),
    gt,
    labels,
    "t, sec", "g(t)",
    colors, linestyles * len(c_coefs),
    [1.5]*len(c_coefs),
    [None]*len(c_coefs),
    [None]*len(c_coefs)
    )
]]

# %%
draw_plots(rows=1, cols=1, width=9, height=4, subplot_data=subplot_data2)

# %%
Re_gw = [np.real(gw_i) for gw_i in gw]
Im_gw = [np.imag(gw_i) for gw_i in gw]
abs_gw = [np.abs(gw_i) for gw_i in gw]

# %%
linestyles = ['-', '-', '--', '--']
Re_gw_plot = (
    [w_space] * len(c_coefs),
    Re_gw,
    labels,
    "w, rad/sec", "Re(g(w))",
    colors, linestyles,
    [1.5]*len(c_coefs),
    [None]*len(c_coefs),
    [None]*len(c_coefs),
    'Вещественная часть'
)
Im_gw_plot = (
    [w_space] * len(c_coefs),
    Im_gw,
    labels,
    "w, rad/sec", "Im(g(w))",
    colors, linestyles,
    [1.5]*len(c_coefs),
    [None]*len(c_coefs),
    [None]*len(c_coefs),
    'Мнимая часть'
)
abs_gw_plot = (
    [w_space] * len(c_coefs),
    abs_gw,
    labels,
    "w, rad/sec", "|g(w)|",
    colors, linestyles,
    [0.5]*len(c_coefs),
    ['o', 'o', 'o', 'o'],
    [2]*len(c_coefs),
    'Модуль', [12,13,14,15]
)
subplot_data3 = [[Re_gw_plot], [Im_gw_plot], [abs_gw_plot]]

# %%
draw_plots(rows=3, cols=1, width=9, height=12, subplot_data=subplot_data3)


