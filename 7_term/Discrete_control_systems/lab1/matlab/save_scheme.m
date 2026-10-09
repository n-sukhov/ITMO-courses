function save_scheme(mdl, filename)
try
    open_system(mdl);
    print(['-s' mdl], '-dpng', filename);
catch e
    warning('lab1:SchemeExport', 'Схема %s не сохранена: %s. Экспортируйте её вручную в %s.', mdl, e.message, filename);
end
end
