auditFolder = 'C:/Users/Nickolay/Desktop/ITMO-courses/tmp/pdfs/dcs-lab4-review/model-audit';
codeFolder = 'C:/Users/Nickolay/Desktop/ITMO-courses/7_term/Discrete_control_systems/lab4/code';
cd(auditFolder);
Simulink.fileGenControl('set', 'CacheFolder', fullfile(auditFolder, 'cache'), ...
    'CodeGenFolder', fullfile(auditFolder, 'codegen'), 'createDir', true);
diary(fullfile(auditFolder, 'matlab_defaults.txt'));
for modelName = ["lab4_continuous", "lab4_pid", "lab4_pid_kalman", "lab4_pitch"]
    load_system(fullfile(codeFolder, modelName + ".slx"));
    fprintf('\nMODEL %s\n', modelName);
    blocks = find_system(modelName, 'SearchDepth', 1, 'Type', 'Block');
    for index = 1:numel(blocks)
        block = blocks{index};
        fprintf('BLOCK %s | type=%s\n', block, get_param(block, 'BlockType'));
        dialog = get_param(block, 'DialogParameters');
        for parameter = ["Numerator", "Denominator", "InitialStates", "InitialCondition", "InitialOutput", "SampleTime", "Time", "Before", "After", "Mean", "Variance", "Seed", "Inputs", "Gain", "Multiplication", "A", "B", "C", "D", "LinearizePole"]
            if isfield(dialog, parameter)
                fprintf('  %s=%s\n', parameter, get_param(block, parameter));
            end
        end
    end
    close_system(modelName, 0);
end
diary off;
