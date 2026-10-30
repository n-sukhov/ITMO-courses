# Оформление графиков в MATLAB

- Белый фон; один шрифт на всех графиках: Times New Roman, 12–14 pt.
- Основные линии — 1.8–2 pt, вспомогательные — тоньше и пунктиром.
- Подписывай оси и единицы: `t, с`, `u, В`. Заголовок должен описывать график.
- Используй спокойные контрастные цвета и лёгкую сетку. Легенда не должна закрывать кривые.
- Подбирай `xlim`, чтобы переходный процесс был хорошо виден.
- Для нескольких полей используй `tiledlayout` и `nexttile`.
- В отчёт сохраняй файл через `exportgraphics`, без скриншотов: PNG 300 dpi или векторный PDF.

## Минимальный пример

```matlab
fig = figure('Color', 'white', 'Position', [100 100 1000 560]);
ax = axes(fig, 'Color', 'white', 'FontName', 'Times New Roman', ...
    'FontSize', 12, 'XColor', 'black', 'YColor', 'black');
plot(ax, t, y, 'LineWidth', 1.8, 'Color', [0 0.35 0.70]);
grid(ax, 'on');
ax.GridAlpha = 0.18;
xlabel(ax, 't, с');
ylabel(ax, 'h(t)');
title(ax, 'Переходная характеристика', 'FontWeight', 'normal');
xlim(ax, [t(1) t(end)]);
exportgraphics(fig, 'plot.png', 'Resolution', 300, ...
    'BackgroundColor', 'white');
% Векторный вариант:
% exportgraphics(fig, 'plot.pdf', 'ContentType', 'vector', ...
%     'BackgroundColor', 'white');
```

## Для `y_step.slx` и `lab1.mlx`

Источник данных — `out.y_step` в формате `Timeseries`; параметры блока `Step` берутся из открытой модели `y_step`.

Скрипт читает время скачка из блока `Step` и отсчитывает время графика от этого момента. Для переходной характеристики нужны единичный скачок и нулевые начальные условия. Установившееся значение этой эталонной модели равно 1.

На графике отмечаются уровень 1, полоса ±2% и фактическое время установления. Показатели вычисляются через `stepinfo`. Допуск задаёт переменная `settlingBand`: `0.02` означает 2%, `0.05` — 5%.

PNG сохраняется в `../tex/images/reference_step.png` — это имя уже предусмотрено в отчёте. Для надписей с кириллицей использован интерпретатор `tex`; запись `\sigma` в MATLAB-строке для `sprintf` выводит символ σ.

Справка MathWorks: [выгрузка из Simulink](https://www.mathworks.com/help/simulink/slref/toworkspace.html), [показатели переходного процесса](https://www.mathworks.com/help/control/ref/dynamicsystem.stepinfo.html), [экспорт графиков](https://www.mathworks.com/help/matlab/ref/exportgraphics.html).
