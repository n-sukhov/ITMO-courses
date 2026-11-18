param(
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $projectDir 'build'
$outputDir = Join-Path $projectDir 'output\pdf'

New-Item -ItemType Directory -Force $buildDir, $outputDir | Out-Null

if ($Clean) {
    Get-ChildItem -LiteralPath $buildDir -Force |
        Where-Object { $_.Name -ne '.gitignore' } |
        Remove-Item -Recurse -Force
}

$xelatex = (Get-Command xelatex -ErrorAction Stop).Source
$arguments = @(
    '--aux-directory=build'
    '--output-directory=output/pdf'
    '-interaction=nonstopmode'
    '-file-line-error'
    '-synctex=1'
    'main.tex'
)

Push-Location $projectDir
try {
    1..2 | ForEach-Object {
        & $xelatex @arguments
        if ($LASTEXITCODE -ne 0) {
            throw "XeLaTeX failed with exit code $LASTEXITCODE."
        }
    }
}
finally {
    Pop-Location
}

$syncTeXFile = Join-Path $outputDir 'main.synctex.gz'
if (Test-Path -LiteralPath $syncTeXFile) {
    Move-Item -LiteralPath $syncTeXFile -Destination $buildDir -Force
}

Write-Host "Done: $outputDir\main.pdf"
