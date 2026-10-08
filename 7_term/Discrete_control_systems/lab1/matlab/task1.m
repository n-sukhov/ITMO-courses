mdl = 'pic8';
load_system('C:\Users\Nickolay\Desktop\ITMO-courses\7_term\Discrete_control_systems\lab1\matlab\pic8.slx');
load_system('simulink');

zoh = find_system(mdl, 'SearchDepth', 1, 'BlockType', 'ZeroOrderHold');
set_param(zoh{1}, 'SampleTime', '0.2');

set_param(mdl, 'StartTime', '0', 'StopTime', '10', ...
    'SolverType', 'Fixed-step', 'Solver', 'ode4', ...
    'FixedStep', '0.01', 'ReturnWorkspaceOutputs', 'on');

logBlock = [mdl '/Task1Output'];
if getSimulinkBlockHandle(logBlock) == -1
    add_block('simulink/Sinks/To Workspace', logBlock, ...
        'VariableName', 'task1_y', 'SaveFormat', 'Timeseries', ...
        'MaxDataPoints', 'inf', 'Position', [950 400 1050 435]);
    add_line(mdl, 'Integrator/1', 'Task1Output/1', 'autorouting', 'on');
end

open_system(mdl);

K_values = [0, 2.5, 2.4, 1, 1.25];
figure;
tiledlayout(3, 2);

for i = 1:numel(K_values)
    set_param([mdl '/K_FB'], 'Gain', num2str(K_values(i)));
    out = sim(mdl);
    y = out.get('task1_y');

    nexttile;
    plot(y.Time, y.Data, 'LineWidth', 1.5);
    yline(1, '--k');
    grid on;
    xlabel('t, с');
    ylabel('y(t)');
    title(sprintf('K_{FB} = %g', K_values(i)));
end
