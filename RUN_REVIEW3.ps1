param([ValidateSet('Menu','Prepare','Preflight','Development','Freeze','Frozen','Report','FrozenAnswers','Launch','Test','Screen')][string]$Mode='Menu')
$ErrorActionPreference='Stop'
$App=Join-Path $PSScriptRoot 'application'
Set-Location $App
$Python=Join-Path $App '.venv\Scripts\python.exe'
function Invoke-Checked { param([string]$Command,[string[]]$Arguments) & $Command @Arguments; if ($LASTEXITCODE -ne 0) { throw "$Command failed with exit code $LASTEXITCODE" } }
if ($Mode -eq 'Menu') {
 Write-Host 'Review 3: Prepare | Preflight | Development | Screen | Freeze | Frozen | FrozenAnswers | Report | Test | Launch'
 $Mode=Read-Host 'Choose mode (first use: Prepare)'
 if ($Mode -notin @('Prepare','Preflight','Development','Screen','Freeze','Frozen','Report','FrozenAnswers','Test','Launch')) { throw 'Unknown mode' }
}
if ($Mode -eq 'Prepare') {
 if (!(Test-Path $Python)) { Invoke-Checked 'py' @('-3.12','-m','venv','.venv') }
 Invoke-Checked $Python @('-m','pip','install','--upgrade','pip')
 Invoke-Checked $Python @('-m','pip','install','torch==2.14.1','--index-url','https://download.pytorch.org/whl/cpu')
 Invoke-Checked $Python @('-m','pip','install','-r','requirements-review3.txt')
 if (Get-Command npm.cmd -ErrorAction SilentlyContinue) {
   Push-Location frontend
   try { Invoke-Checked 'npm.cmd' @('ci'); Invoke-Checked 'npm.cmd' @('run','build') } finally { Pop-Location }
 } elseif (!(Test-Path 'frontend\dist\index.html')) { throw 'Install Node.js LTS to build the frontend' }
 Invoke-Checked $Python @('research/review3/finalization/workflow.py','test')
 Invoke-Checked $Python @('research/review3/finalization/workflow.py','preflight')
 Write-Host 'Prepared. Run this workflow again and choose Launch or Development.'
} else {
 if (!(Test-Path $Python)) { throw 'Choose Prepare first' }
 $env:OMP_NUM_THREADS='2';$env:MKL_NUM_THREADS='2'
 Invoke-Checked $Python @('research/review3/finalization/workflow.py',$Mode.ToLower())
}
