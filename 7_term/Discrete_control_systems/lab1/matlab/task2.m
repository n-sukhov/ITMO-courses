run(fullfile(fileparts(mfilename('fullpath')), 'setup_lab1.m'));
mdl = 'task2_model';
load_system(fullfile(matlab_dir, [mdl '.slx']));
gains = find_system(mdl, 'SearchDepth', 1, 'BlockType', 'Gain');
for j = 1:numel(gains)
    set_param(gains{j}, 'Multiplication', 'Matrix(K*u)');
end
set_param(mdl, 'StartTime', '0', 'StopTime', '10', 'SolverType', 'Fixed-step', 'Solver', 'FixedStepDiscrete', 'FixedStep', num2str(T2), 'ReturnWorkspaceOutputs', 'on');
responses = cell(size(K_sets, 1), 1);
actual_poles = zeros(size(poles2));
errors = zeros(size(K_sets, 1), 1);
fig = figure('Color', 'w', 'Position', [100 100 1000 850]);
tiledlayout(3, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
for i = 1:size(K_sets, 1)
    K2 = K_sets(i, :);
    F = A2 - B2 * K2;
    actual_poles(i, :) = eig(F).';
    assert(norm(poly(F) - real(poly(poles2(i, :))), inf) < 1e-10, 'Ошибка расчёта K2, набор %d.', i);
    out = sim(mdl);
    y = out.get('task2_y');
    k = round(y.Time / T2);
    assert(max(abs(y.Time / T2 - k)) < 1e-7 && isequal(k(:), (0:50).'), 'task2: ожидаются 51 отсчёт с периодом T2.');
    reference = arrayfun(@(n) C2 * (F^n) * x02, k);
    errors(i) = max(abs(y.Data(:) - reference(:)));
    assert(errors(i) < 1e-8, 'task2: проверьте матрицы, -K2 и начальное состояние, набор %d.', i);
    responses{i} = y;
    nexttile;
    plot(y.Time, y.Data(:), '.-', 'LineWidth', 1.1, 'MarkerSize', 9);
    yline(0, '--k');
    grid on;
    xlabel('t = kT, с');
    ylabel('y(k)');
    title(sprintf('Набор %d: z_1=%s, z_2=%s', i, num2str(poles2(i, 1)), num2str(poles2(i, 2))));
end
exportgraphics(fig, fullfile(images_dir, 'task2_responses.png'), 'Resolution', 300, 'BackgroundColor', 'white');
save(fullfile(results_dir, 'task2_results.mat'), 'T2', 'A2', 'B2', 'C2', 'x02', 'poles2', 'actual_poles', 'K_sets', 'responses', 'errors');
save_scheme(mdl, fullfile(images_dir, 'task2_scheme.png'));
disp(table((1:5).', K_sets(:, 1), K_sets(:, 2), actual_poles(:, 1), actual_poles(:, 2), errors, 'VariableNames', {'set', 'k1', 'k2', 'z1', 'z2', 'max_error'}));
