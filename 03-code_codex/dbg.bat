@echo off
setlocal
rem Shared study tool: debug Python with pdb, or compile C and open GDB.
chcp 65001 >nul
if "%~1"=="" (
    echo Usage: .\dbg filename.py OR filename.c
    exit /b 2
)
set "study_source=%~f1"
if /I "%~x1"==".py" goto run_python
if /I not "%~x1"==".c" set "study_source=%~f1.c"
if not exist "%study_source%" (
    echo [SOURCE NOT FOUND] "%study_source%"
    exit /b 2
)
for %%F in ("%study_source%") do set "study_exe=%%~dpnF.exe"
"D:\embedded\mingw64\bin\gcc.exe" -std=c11 -Wall -Wextra -Wpedantic -g3 -O0 -finput-charset=UTF-8 -fexec-charset=UTF-8 "%study_source%" -o "%study_exe%"
if errorlevel 1 (
    echo [COMPILE FAILED - GDB NOT started. Fix the FIRST error above.]
    exit /b 1
)
"D:\embedded\mingw64\bin\gdb.exe" "%study_exe%"
exit /b %errorlevel%

:run_python
if not exist "%study_source%" (
    echo [SOURCE NOT FOUND] "%study_source%"
    exit /b 2
)
"D:\working software\python\python.exe" -m pdb "%study_source%"
exit /b %errorlevel%
