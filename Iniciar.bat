@echo off
setlocal
title Control TV VIZIO
cd /d "%~dp0"

rem Buscar Python (primero el lanzador "py", luego "python")
set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
    echo No se encontro Python.
    echo Instalalo desde https://www.python.org/downloads/
    echo y marca la casilla "Add Python to PATH".
    pause
    exit /b 1
)

rem Instalar la libreria la primera vez
%PY% -c "import pyvizio" >nul 2>nul
if errorlevel 1 (
    echo Instalando lo necesario, espera un momento...
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo No se pudo instalar. Revisa tu conexion a internet.
        pause
        exit /b 1
    )
)

if not exist vizio_config.json goto emparejar

:menu
cls
echo ==============================
echo      CONTROL TV VIZIO
echo ==============================
echo  1. Ver estado
echo  2. Encender
echo  3. Apagar
echo  4. Subir volumen
echo  5. Bajar volumen
echo  6. Silencio
echo  7. Cambiar entrada (HDMI)
echo  8. Abrir app
echo  9. Boton del control remoto
echo 10. Emparejar de nuevo
echo  0. Salir
echo.
set "op="
set /p "op=Elige una opcion: "

if "%op%"=="1" %PY% vizio.py estado & goto pausa
if "%op%"=="2" %PY% vizio.py encender & goto pausa
if "%op%"=="3" %PY% vizio.py apagar & goto pausa
if "%op%"=="4" goto subir
if "%op%"=="5" goto bajar
if "%op%"=="6" %PY% vizio.py silencio & goto pausa
if "%op%"=="7" goto entrada
if "%op%"=="8" goto app
if "%op%"=="9" goto tecla
if "%op%"=="10" goto emparejar
if "%op%"=="0" exit /b 0
goto menu

:subir
set "n=1"
set /p "n=Cuantos niveles? [1]: "
%PY% vizio.py volumen subir %n%
goto pausa

:bajar
set "n=1"
set /p "n=Cuantos niveles? [1]: "
%PY% vizio.py volumen bajar %n%
goto pausa

:entrada
%PY% vizio.py entradas
echo.
set "nombre="
set /p "nombre=Escribe el nombre de la entrada (ej. HDMI-1): "
if defined nombre %PY% vizio.py entrada "%nombre%"
goto pausa

:app
set "nombre="
set /p "nombre=Nombre de la app (ej. Netflix, YouTube): "
if defined nombre %PY% vizio.py app "%nombre%"
goto pausa

:tecla
%PY% vizio.py tecla
echo.
set "nombre="
set /p "nombre=Escribe el boton (ej. HOME, OK, UP, BACK): "
if defined nombre %PY% vizio.py tecla "%nombre%"
goto pausa

:emparejar
cls
echo Enciende el televisor antes de continuar.
set "ip=192.168.100.2"
set /p "ip=IP del televisor [192.168.100.2]: "
%PY% vizio.py emparejar --ip %ip%
pause
if exist vizio_config.json goto menu
exit /b 1

:pausa
echo.
pause
goto menu
