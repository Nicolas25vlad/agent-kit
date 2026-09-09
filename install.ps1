$ErrorActionPreference = 'Stop'

$root = (Resolve-Path $PSScriptRoot).Path
$bin = Join-Path $env:LOCALAPPDATA 'agent-kit\bin'
$wrapper = Join-Path $bin 'agent.cmd'
$python = Get-Command python -ErrorAction SilentlyContinue
$pythonArgs = ''
if (-not $python) {
  $py = Get-Command py -ErrorAction SilentlyContinue
  $python = $py
  $pythonArgs = '-3'
}

if (-not $python) { throw 'Python 3.9+ não encontrado. Instale Python e execute este script novamente.' }

New-Item -ItemType Directory -Force -Path $bin | Out-Null
$run = if ($python.Source -match '\s') { "`"$($python.Source)`"" } else { $python.Source }
("@echo off`r`nset `"PYTHONPATH=$root\src;%PYTHONPATH%`"`r`n$run $pythonArgs -m agent_kit %*`r`n") | Set-Content -Encoding ascii $wrapper

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User') -split ';' | Where-Object { $_ }
if ($userPath -notcontains $bin) {
  [Environment]::SetEnvironmentVariable('Path', (($userPath + $bin) -join ';'), 'User')
}

$env:Path = "$bin;$env:Path"
Write-Output "agent-kit instalado em $wrapper"
Write-Output 'Teste: agent repo info'
