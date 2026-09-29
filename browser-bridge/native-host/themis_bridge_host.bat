@echo off
setlocal

rem Native Messaging nao herda necessariamente o ambiente do Hermes Desktop.
rem Deriva HERMES_HOME a partir da instalacao do proprio plugin:
rem <HERMES_HOME>\plugins\themis\browser-bridge\native-host
for %%I in ("%~dp0..\..\..\..") do set "THEMIS_HERMES_HOME=%%~fI"

rem Override explicito, se existir.
if defined HERMES_PYTHON if exist "%HERMES_PYTHON%" (
    set "THEMIS_PYTHON=%HERMES_PYTHON%"
    goto :run
)

rem Runtime gerenciado atual do Hermes.
for /d %%P in ("%THEMIS_HERMES_HOME%\tools\python-*") do (
    if exist "%%~fP\python.exe" (
        set "THEMIS_PYTHON=%%~fP\python.exe"
        goto :run
    )
)

rem Compatibilidade com layouts antigos.
if exist "%THEMIS_HERMES_HOME%\hermes-agent\venv\Scripts\python.exe" (
    set "THEMIS_PYTHON=%THEMIS_HERMES_HOME%\hermes-agent\venv\Scripts\python.exe"
    goto :run
)

if exist "%THEMIS_HERMES_HOME%\runtime\Scripts\python.exe" (
    set "THEMIS_PYTHON=%THEMIS_HERMES_HOME%\runtime\Scripts\python.exe"
    goto :run
)

rem Nao usar "python" do PATH: pode ser Python de outro aplicativo.
exit /b 127

:run
"%THEMIS_PYTHON%" "%~dp0themis_bridge_host.py" %*
exit /b %ERRORLEVEL%