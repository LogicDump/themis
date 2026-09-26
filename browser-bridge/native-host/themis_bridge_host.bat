@echo off
setlocal
if defined HERMES_PYTHON (
    "%HERMES_PYTHON%" "%~dp0themis_bridge_host.py" %*
) else (
    if defined HERMES_HOME if exist "%HERMES_HOME%\hermes-agent\venv\Scripts\python.exe" set "THEMIS_PYTHON=%HERMES_HOME%\hermes-agent\venv\Scripts\python.exe"
    if not defined THEMIS_PYTHON if defined HERMES_HOME if exist "%HERMES_HOME%\runtime\Scripts\python.exe" set "THEMIS_PYTHON=%HERMES_HOME%\runtime\Scripts\python.exe"
    if defined THEMIS_PYTHON (
        "%THEMIS_PYTHON%" "%~dp0themis_bridge_host.py" %*
    ) else (
        python "%~dp0themis_bridge_host.py" %*
    )
)
