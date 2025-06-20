# %%
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq, fftshift
from scipy import signal
import pandas as pd
from datetime import datetime
%matplotlib widget
np.random.seed(17)

# %% [markdown]
# Util-функции

# %%
def draw_plots(rows, cols, width, height, subplot_data, legend_loc="best", legend_fontsize="small"):
    fig, axes = plt.subplots(rows, cols, figsize=(width, height))
    axes = axes.flatten() if rows * cols > 1 else [axes]

    flat_data = [item for row in subplot_data for item in row]

    for idx, data in enumerate(flat_data):
        if idx >= len(axes):
            raise ValueError(f"Too many subplots provided in 'subplot_data': \
                             expected at most {rows * cols}, got more.")
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
g = lambda t, a: a if (1 <= t <= 4) else 0
u = lambda t, a, b, c, d: g(t, a) + b * np.random.uniform(-1, 1) + c * np.sin(d * t)

# %% [markdown]
# # Задание 1.1

# %%
def calc_spectrum(signal, dt):
    spectrum = fftshift(np.abs(fft(signal)))
    freq = 2 * np.pi * fftshift(fftfreq(len(signal), dt))
    return freq, spectrum

# %%
T_range = [0.025, 0.1, 0.4]
a_range = [2, 8, 16]
b = 0.5
c = 0
d = 10
plots_11 = []

N = 2 ** 15
t = np.linspace(0, 20, N)
dt = t[1] - t[0]

time_subplot_data = []
spectrum_subplot_data = []
freq_response_subplot_data = []

for i, a in enumerate(a_range):
    time_row = []
    spectrum_row = []
    freq_response_row = []
    
    for j, T in enumerate(T_range):
        g_signal = np.array([g(ti, a) for ti in t])
        u_signal = np.array([u(ti, a, b, c, d) for ti in t])
        
        W = signal.TransferFunction([1], [T, 1])
        _, y_signal, _ = signal.lsim(W, U=u_signal, T=t)
        
        freq_g, func_g = calc_spectrum(g_signal, dt)
        freq_u, func_u = calc_spectrum(u_signal, dt)
        freq_y, func_y = calc_spectrum(y_signal, dt)
        
        w = freq_g
        W_mag = 1 / np.sqrt(1 + (T * w)**2)
        
        afc_mask = (freq_g >= 0) & (freq_g < 100)
        omega_mask = np.abs(freq_g) < 40
        
        time_plot = [
            [t[t < 7]] * 3,
            [u_signal[t < 7], g_signal[t < 7], y_signal[t < 7]],
            ['u(t)', 'g(t)', 'y(t), filtered'],
            't', 'Amplitude',
            ['g', 'b', 'r'],
            ['-'] * 3,
            [0.5, 1.0, 0.75],
            [None] * 3,
            [None] * 3,
            f'a={a}, T={T}',
        ]
        time_row.append(time_plot)

        spectrum_plot = [
            [freq_u[omega_mask], freq_g[omega_mask], freq_y[omega_mask]],
            [2.0 / N * func_u[omega_mask],
             2.0 / N * func_g[omega_mask],
             2.0 / N * func_y[omega_mask]
            ],
            ['|u_hat(ω)|', '|g_hat(ω)|', 'y_hat(ω)|'],
            'ω', 'Amplitude',
            ['b', "#09FF00", 'r'],
            ['-', ':', '-'],
            [1.0, 1.0, 1.0],
            [None] * 3,
            [None] * 3,
            f'a={a}, T={T}',
        ]
        spectrum_row.append(spectrum_plot)
        
        target = 1/np.sqrt(2)
        idx = np.argmin(np.abs(W_mag[afc_mask] - target))
        cutoff_freq = freq_g[afc_mask][idx]
        cutoff_amp = W_mag[afc_mask][idx]

        freq_response_plot = [
            [freq_g[afc_mask], [cutoff_freq, cutoff_freq], [0, cutoff_freq]],
            [W_mag[afc_mask], [0, cutoff_amp], [cutoff_amp, cutoff_amp]],
            ['|W(iω)|', "ω_c", None],
            'ω', '|W(iω)|',
            ['m', 'b', 'b'],
            ['-', '--', '--'],
            [1.5, 0.9, 0.9],
            [None] * 3,
            [None] * 3,
            f'T={T}',
        ]
        freq_response_row.append(freq_response_plot)
    
    time_subplot_data.append(time_row)
    spectrum_subplot_data.append(spectrum_row)
    if i == 0:
        freq_response_subplot_data.append(freq_response_row)

draw_plots(
    rows=3,
    cols=3,
    width=12,
    height=10,
    subplot_data=time_subplot_data,
    legend_loc='upper right',
    legend_fontsize='xx-small'
)

draw_plots(
    rows=3,
    cols=3,
    width=12,
    height=10,
    subplot_data=spectrum_subplot_data,
    legend_loc='upper right'
)

draw_plots(
    rows=1,
    cols=3,
    width=12,
    height=3,
    subplot_data=freq_response_subplot_data,
    legend_loc='upper right'
)

# %% [markdown]
# # Задание 1.2

# %%
a = 1
b = 0
c_range = [0.1, 0.5]
d_range = [20, 25, 30]

a1 = 0
a2 = b2 = 625
b1_range = [5, 20, 70, 200] 

N = 2 ** 15
t = np.linspace(0, 20, N)
dt = t[1] - t[0]

time_subplot_data = []
spectrum_subplot_data = []
freq_response_subplot_data = []

for i, c in enumerate(c_range):
    time_row = []
    spectrum_row = []
    freq_response_row = []
    
    for j, b1 in enumerate(b1_range):
        for k, d in enumerate(d_range):
            g_signal = np.array([g(ti, a) for ti in t])
            u_signal = np.array([u(ti, a, b, c, d) for ti in t])
            
            W = signal.TransferFunction([1, a1, a2], [1, b1, b2])
            _, y_signal, _ = signal.lsim(W, U=u_signal, T=t)
            
            freq_g, func_g = calc_spectrum(g_signal, dt)
            freq_u, func_u = calc_spectrum(u_signal, dt)
            freq_y, func_y = calc_spectrum(y_signal, dt)
            
            w = freq_g
            W_mag = np.abs((1j*w)**2 + a1*(1j*w) + a2) / np.abs((1j*w)**2 + b1*(1j*w) + b2)
            
            afc_mask = (freq_g >= 0) & (freq_g < 120)
            omega_mask = np.abs(freq_g) < 35
            t_mask = t < 7

            time_plot = [
                [t[t_mask]] * 3,
                [u_signal[t_mask], g_signal[t_mask], y_signal[t_mask]],
                ['u(t)', 'g(t)', 'y(t), filtered'],
                't', 'Amplitude',
                ['g', 'b', 'r'],
                ['-'] * 3,
                [1.0, 1.0, 1.0],
                [None] * 3,
                [None] * 3,
                f'b1={b1:.2f}, c={c}, d={d}',
            ]
            time_row.append(time_plot)
            
            spectrum_plot = [
                [freq_u[omega_mask], freq_g[omega_mask], freq_y[omega_mask]],
                [2.0 / N * func_u[omega_mask],
                 2.0 / N * func_g[omega_mask],
                 2.0 / N * func_y[omega_mask]],
                ['|u_hat(ω)|', '|g_hat(ω)|', 'y_hat(ω)|'],
                'ω', 'Amplitude',
                ['b', "#039D71", 'r'],
                ['-', ':', '-'],
                [1.0, 2.0, 1.0],
                [None] * 3,
                [None] * 3,
                f'b1={b1}, c={c}, d={d}',
            ]
            spectrum_row.append(spectrum_plot)
            
            if c == c_range[0] and d == d_range[0]:
                freq_response_plot = [
                    [freq_g[afc_mask]],
                    [W_mag[afc_mask]],
                    ['|W(iω)|'],
                    'ω', '|W(iω)|',
                    ['m'],
                    ['-'],
                    [1.5],
                    [None],
                    [None],
                    f'b1={b1}',
                ]
                freq_response_row.append(freq_response_plot)
    
    time_subplot_data.append([time_row])
    spectrum_subplot_data.append([spectrum_row])
    freq_response_subplot_data.append(freq_response_row)

for tsd in time_subplot_data:
    draw_plots(
        rows=4,
        cols=3,
        width=12,
        height=12,
        subplot_data=tsd,
        legend_loc='upper right',
        legend_fontsize='xx-small'
    )

for ssd in spectrum_subplot_data:
    draw_plots(
        rows=4,
        cols=3,
        width=12,
        height=12,
        subplot_data=ssd,
        legend_loc='upper right'
    )

draw_plots(
    rows=2,
    cols=2,
    width=10,
    height=8,
    subplot_data=freq_response_subplot_data,
    legend_loc='upper right'
)

# %% [markdown]
# # Задание 2

# %%
data = pd.read_csv('SBER_DATA.csv', sep=';', parse_dates=['<DATE>'], 
                  date_parser=lambda x: datetime.strptime(x, '%y%m%d'))
data = data.sort_values('<DATE>')

dates = data['<DATE>'].values
prices = data['<CLOSE>'].values
t_days = np.arange(len(dates))

time_constants_days = [1, 7, 30, 90, 365]

filtered_signals = []
for tc in time_constants_days:
    W = signal.TransferFunction([1], [tc, 1])
    _, y_signal, _ = signal.lsim(W, U=prices, T=t_days, X0=prices[0] * tc)
    filtered_signals.append(y_signal)

plot_data = []

for i, tc in enumerate(time_constants_days):
    if tc == 1:
        tc_label = "1 день"
    elif tc == 7:
        tc_label = "1 неделя"
    elif tc == 30:
        tc_label = "1 месяц"
    elif tc == 90:
        tc_label = "3 месяца"
    else:
        tc_label = "1 год"

    plot_data.append([
        [dates] * 2,
        [prices, filtered_signals[i]],
        ['Цена открытия', f'Сглаживание'],
        'Дата', 'Цена, руб.',
        ['g', 'r'],
        ['-'] * 2,
        [0.7, 1.0],
        [None] * 2,
        [None] * 2,
        f'T={tc_label}'
    ])

draw_plots(
    rows=6,
    cols=1,
    width=12,
    height=26,
    subplot_data=[plot_data],
    legend_loc='lower right'
)


