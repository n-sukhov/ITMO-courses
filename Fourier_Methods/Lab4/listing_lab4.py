# %%
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, ifft, fftfreq, fftshift, ifftshift
from scipy import signal
%matplotlib widget

# %% [markdown]
# Util-функции

# %%
def draw_plots(rows, cols, width, height, subplot_data, legend_loc="best", legend_fontsize="small"):
    fig, axes = plt.subplots(rows, cols, figsize=(width, height))
    axes = axes.flatten() if rows * cols > 1 else [axes]

    flat_data = [item for row in subplot_data for item in row]

    for idx, data in enumerate(flat_data):
        if idx >= len(axes):
            raise ValueError(f"Too many subplots provided in 'subplot_data': expected at most {rows * cols}, got more.")
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
        ) = data + [None] * (12 - len(data))

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
            ax.legend(loc=legend_loc, fontsize=legend_fontsize)
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

# %%
g = lambda t: 7 if (1 <= t <= 4) else 0
u = lambda t, b, c, d: g(t) + b * np.random.uniform(-1, 1) + c * np.sin(d * t)

# %% [markdown]
# # Задание 1.1

# %%
W_1 = lambda T, p: 1 / (T * p + 1)

# %%
T_range = [0.2, 0.8, 1.6]
a_range = [2, 4, 7]
b = 0.5
c = 0
d = 10
plots_11 = []

t_start, t_end = 0, 5
num_points = 2 ** 15
t = np.linspace(t_start, t_end, num_points)
dt = t[1] - t[0]

freq = fftshift(fft.fftfreq(len(t), dt))

def calc_spectrum(signal):
    spectrum = np.abs(fftshift(fft.fft(signal)))
    return freq, spectrum

time_subplot_data = []
spectrum_subplot_data = []
freq_response_subplot_data = []
for i, a_val in enumerate(a_range):
    time_row = []
    spectrum_row = []
    freq_response_row = []
    
    for j, T_val in enumerate(T_range):
        g_signal = np.array([g(ti, a_val) for ti in t])
        u_signal = np.array([u(ti, a_val, b, c, d) for ti in t])
        
        sys = signal.TransferFunction([1], [T_val, 1])
        _, y_signal, _ = signal.lsim(sys, U=u_signal, T=t)
        
        f_g, spec_g = calc_spectrum(g_signal)
        f_u, spec_u = calc_spectrum(u_signal)
        f_y, spec_y = calc_spectrum(y_signal)
        
        w = 2 * np.pi * freq
        W_mag = 1 / np.sqrt(1 + (T_val * w)**2)
        
        # Маски для отображения только положительных частот
        afc_mask = freq >= 0
        omega_mask = np.abs(freq) < 10
        
        time_plot = [
            [t, t, t],
            [g_signal, u_signal, y_signal],
            ['Исходный g(t)', 'Зашумленный u(t)', 'Отфильтрованный y(t)'],
            'Время, с', 'Амплитуда',
            ['g', 'b', 'r'],
            ['-', '-', '-'],
            [1.2, 1.0, 1.5],
            [None, None, None],
            [None, None, None],
            f'a={a_val}, T={T_val} с',
        ]
        time_row.append(time_plot)

        spectrum_plot = [
            [f_g[omega_mask], f_u[omega_mask], f_y[omega_mask]],
            [spec_g[omega_mask], spec_u[omega_mask], spec_y[omega_mask]],
            ['|G(f)|', '|U(f)|', '|Y(f)|'],
            'Частота, Гц', 'Амплитуда',
            ['g', 'b', 'r'],
            ['-', '-', '-'],
            [1.2, 1.0, 1.5],
            [None, None, None],
            [None, None, None],
            f'Спектры (a={a_val}, T={T_val})',
        ]
        spectrum_row.append(spectrum_plot)
        
        freq_response_plot = [
            [freq[afc_mask]],
            [W_mag[afc_mask]],
            ['|W(iω)|'],
            'Частота, Гц', 'Амплитуда',
            ['m'],
            ['-'],
            [1.5],
            [None],
            [None],
            f'АЧХ фильтра (T={T_val})',
        ]
        freq_response_row.append(freq_response_plot)
    
    time_subplot_data.append(time_row)
    spectrum_subplot_data.append(spectrum_row)
    freq_response_subplot_data.append(freq_response_row)

draw_plots(
    rows=3,
    cols=3,
    width=12,
    height=10,
    subplot_data=time_subplot_data,
    legend_loc='upper right',
    legend_fontsize='x-small'
)

draw_plots(
    rows=3,
    cols=3,
    width=12,
    height=10,
    subplot_data=spectrum_subplot_data,
    legend_loc='upper right',
    legend_fontsize='x-small'
)

draw_plots(
    rows=3,
    cols=3,
    width=12,
    height=10,
    subplot_data=freq_response_subplot_data,
    legend_loc='upper right',
    legend_fontsize='x-small'
)

# %%


# %%


# %%



