@echo off
REM branch.bat — create feature branch, commit, show diff vs master
REM Usage: branch <feature-name>

if "%1"=="" (
    echo Usage: %0 ^<feature-name^>
    exit /b 1
)

set BRANCH_NAME=feature/%1
echo === Creating branch: %BRANCH_NAME% ===
git checkout -b %BRANCH_NAME%
if %%ERRORLEVEL%% neq 0 (
    echo Failed to create branch
    exit /b %%ERRORLEVEL%%
)

git add -A
git commit -m "feat: %1"
if %%ERRORLEVEL%% neq 0 (
    echo Nothing to commit or commit failed
)

echo.
echo === Changes (diff vs master) ===
git fetch origin master 2>nul
git diff master...%BRANCH_NAME% --stat
echo.
echo === Branch '%BRANCH_NAME%' is ready ===
echo Next step: git push origin %BRANCH_NAME%
echo Then: merge to master + deploy
