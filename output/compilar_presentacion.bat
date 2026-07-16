@echo off
REM Compila presentacion_mip.tex a PDF con MiKTeX (instalado via winget).
REM Uso: doble clic, o ejecutar desde la carpeta output.
setlocal
set "MIKTEX=%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64"
if exist "%MIKTEX%\pdflatex.exe" set "PATH=%MIKTEX%;%PATH%"
cd /d "%~dp0"

REM Que MiKTeX instale paquetes faltantes sin preguntar
initexmf --set-config-value=[MPM]AutoInstall=1 >nul 2>&1

echo Compilando (pasada 1 de 2)...
pdflatex -interaction=nonstopmode presentacion_mip.tex >nul
echo Compilando (pasada 2 de 2)...
pdflatex -interaction=nonstopmode presentacion_mip.tex >nul

if exist presentacion_mip.pdf (
  echo.
  echo ============================================
  echo   LISTO:  presentacion_mip.pdf
  echo ============================================
  start "" presentacion_mip.pdf
) else (
  echo.
  echo Hubo un error. Revisa presentacion_mip.log
)
pause
