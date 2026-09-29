@echo off
setlocal

rem The browser launches this process outside the Hermes Desktop environment.
rem Resolve the Hermes-owned Python from this plugin's installed location.
for %%I in ("%~dp0..\..\..\..") do set "THEMIS_HERMES_HOME=%%~fI"

if defined HERMES_PYTHON if exist "%HERMES_PYTHON%" (
    set "THEMIS_PYTHON=%HERMES_PYTHON%"
    goto :run
)

if exist "%THEMIS_HERMES_HOME%\hermes-agent\venv\Scripts\python.exe" (
    set "THEMIS_PYTHON=%THEMIS_HERMES_HOME%\hermes-agent\venv\Scripts\python.exe"
    goto :run
)

if exist "%THEMIS_HERMES_HOME%\hermes-agent\.venv\Scripts\python.exe" (
    set "THEMIS_PYTHON=%THEMIS_HERMES_HOME%\hermes-agent\.venv\Scripts\python.exe"
    goto :run
)

if exist "%THEMIS_HERMES_HOME%\runtime\Scripts\python.exe" (
    set "THEMIS_PYTHON=%THEMIS_HERMES_HOME%\runtime\Scripts\python.exe"
    goto :run
)

if exist "%THEMIS_HERMES_HOME%\.venv\Scripts\python.exe" (
    set "THEMIS_PYTHON=%THEMIS_HERMES_HOME%\.venv\Scripts\python.exe"
    goto :run
)

if exist "%THEMIS_HERMES_HOME%\pm-runtime\Scripts\python.exe" (
    set "THEMIS_PYTHON=%THEMIS_HERMES_HOME%\pm-runtime\Scripts\python.exe"
    goto :run
)

rem Deliberately do not fall back to an arbitrary "python" from PATH.
exit /b 127

:run
"%THEMIS_PYTHON%" "%~dp0themis_bridge_host.py" %*
exit /b %ERRORLEVEL%
