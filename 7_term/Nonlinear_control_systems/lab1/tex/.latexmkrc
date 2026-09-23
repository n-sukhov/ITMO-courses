# latexmk: служебные файлы отдельно, готовый PDF отдельно.
$aux_dir = 'build';
$out_dir = 'output/pdf';
$pdf_mode = 5;
$xelatex = 'xelatex --aux-directory=build %O -synctex=0 %S';
