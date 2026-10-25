@echo off
rem Convertitore Audio - a cura di Massimiliano Mascioli Trippa
rem Crea "dist\Convertitore Audio.exe" e "dist\ConvertitoreAudio-Windows.zip".
rem Serve Python 3.9+ da https://www.python.org (con "tcl/tk" incluso, opzione predefinita).
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")

%PY% -m venv .venv-build || goto :error
.venv-build\Scripts\python -m pip install --quiet --upgrade pip || goto :error
.venv-build\Scripts\python -m pip install --quiet -r requirements-build.txt || goto :error
.venv-build\Scripts\pyinstaller --noconfirm --clean ConvertitoreAudio.spec || goto :error

powershell -NoProfile -Command "Compress-Archive -Force -Path 'dist\Convertitore Audio.exe' -DestinationPath 'dist\ConvertitoreAudio-Windows.zip'" || goto :error

echo.
echo Fatto:
echo   dist\Convertitore Audio.exe
echo   dist\ConvertitoreAudio-Windows.zip
pause
exit /b 0

:error
echo.
echo Errore durante la creazione del programma.
pause
exit /b 1
