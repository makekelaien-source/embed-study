@echo off
chcp 65001 >nul
rem Usage: type  go hello   (compiles hello.c then runs it, only if compile succeeded)
set GCC=D:\embedded\mingw64\bin\gcc.exe
"%GCC%" -Wall -o %1.exe %1.c
if %errorlevel%==0 (
    %1.exe
) else (
    echo.
    echo [COMPILE FAILED - old exe NOT run. Fix the FIRST error above.]
)
