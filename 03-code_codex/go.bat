@echo off
setlocal
rem Match UTF-8 C string output with the Windows console code page.
chcp 65001 >nul
rem Usage: .\go [filename.py OR filename.c OR filename]
rem With no argument, run the current D8 path exercise.
if "%~1"=="" (
    set "study_source=%~dp0d8-path-report.py"
    goto run_python
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
    echo [COMPILE FAILED - old exe NOT run. Fix the FIRST error above.]
    exit /b 1
)
"%study_exe%"
exit /b %errorlevel%

:run_python
if not exist "%study_source%" (
    echo [SOURCE NOT FOUND] "%study_source%"
    exit /b 2
)
"D:\working software\python\python.exe" "%study_source%"
exit /b %errorlevel%
