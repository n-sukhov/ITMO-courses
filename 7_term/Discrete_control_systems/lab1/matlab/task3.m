run(fullfile(fileparts(mfilename('fullpath')), 'setup_lab1.m'));
models = {'task3_harmonic', 'task3_disturbance'};
variables = {'harmonic_y', 'disturbance_y'};
periods = [T_h T_d];
stop_times = [160 10];
responses = cell(2, 1);
errors = zeros(2, 1);
for i = 1:2
    mdl = models{i};
    load_system(fullfile(matlab_dir, [mdl '.slx']));
    set_param(mdl, 'StartTime', '0', 'StopTime', num2str(stop_times(i)), 'SolverType', 'Fixed-step', 'Solver', 'FixedStepDiscrete', 'FixedStep', num2str(periods(i)), 'ReturnWorkspaceOutputs', 'on');
    out = sim(mdl);
    y = out.get(variables{i});
    t = y.Time(:);
    k = round(t / periods(i));
    assert(max(abs(t / periods(i) - k)) < 1e-7 && isequal(k, (0:round(stop_times(i) / periods(i))).'), '%s: неверные период или число отсчётов.', mdl);
    if i == 1
        reference = amplitude_h * sin(omega_h * t);
        caption = 'g(k) = sin(0.08kT), T = 0.2 с';
    else
        reference = 2 * exp(-t) .* sin(3 * t) + 0.1 * t.^2;
        caption = 'g(k) = 2e^{-kT}sin(3kT) + 0.1(kT)^2, T = 0.25 с';
    end
    errors(i) = max(abs(y.Data(:) - reference));
    assert(errors(i) < 1e-8, '%s: выход не совпадает с заданной функцией.', mdl);
    responses{i} = y;
    fig = figure('Color', 'w', 'Position', [100 100 1000 400]);
    plot(t, reference, '-k', t, y.Data(:), '.b', 'LineWidth', 1.1, 'MarkerSize', 8);
    grid on;
    xlabel('t = kT, с');
    ylabel('g(k)');
    title(caption);
    legend('Заданная функция', 'Simulink', 'Location', 'best');
    exportgraphics(fig, fullfile(images_dir, [mdl '_signal.png']), 'Resolution', 300, 'BackgroundColor', 'white');
    save_scheme(mdl, fullfile(images_dir, [mdl '_scheme.png']));
end
save(fullfile(results_dir, 'task3_results.mat'), 'T_h', 'amplitude_h', 'omega_h', 'G_h', 'B_h', 'H_h', 'x0_h', 'T_d', 'G_d', 'B_d', 'H_d', 'x0_d', 'responses', 'errors');
disp(table(models.', errors, 'VariableNames', {'model', 'max_error'}));
