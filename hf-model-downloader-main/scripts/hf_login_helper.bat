@echo off
setlocal ENABLEDELAYEDEXPANSION

echo.
echo ==============================
echo   Hugging Face Login Helper
echo   (4 strategies + fail-safes)
echo ==============================
echo.

set "HF_CACHE=%USERPROFILE%\.cache\huggingface"
set "HF_TOKEN_FILE=%HF_CACHE%\token"
set "HF_STORED_TOKENS=%HF_CACHE%\stored_tokens"

if not exist "%HF_CACHE%" (
  echo [INFO] Creating cache directory "%HF_CACHE%".
  mkdir "%HF_CACHE%" >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] Failed to create "%HF_CACHE%".
    goto :END
  )
)

echo Backing up any existing Hugging Face token files...
if exist "%HF_TOKEN_FILE%" (
  copy /Y "%HF_TOKEN_FILE%" "%HF_TOKEN_FILE%.bak" >nul 2>&1
)
if exist "%HF_STORED_TOKENS%" (
  copy /Y "%HF_STORED_TOKENS%" "%HF_STORED_TOKENS%.bak" >nul 2>&1
)

echo.
echo IMPORTANT: Your token will be visible while typing in this window.
echo It should look like: hf_xxx...  (copied from https://huggingface.co/settings/tokens)
echo.
set /p HF_TOKEN=Enter your Hugging Face token: 
if "%HF_TOKEN%"=="" (
  echo [ERROR] No token entered. Aborting.
  goto :END
)

set /p HF_TOKEN_NAME=Short nickname for this token [ShadowByte2]: 
if "%HF_TOKEN_NAME%"=="" set "HF_TOKEN_NAME=ShadowByte2"

echo.
echo ===== Strategy 1: hf auth login (recommended) =====
call :TryHfAuthLogin
if %ERRORLEVEL% EQU 0 goto :SUCCESS

echo.
echo ===== Strategy 2: python -m huggingface_hub.commands.huggingface_cli login =====
call :TryPythonCliLogin
if %ERRORLEVEL% EQU 0 goto :SUCCESS

echo.
echo ===== Strategy 3: huggingface-cli login =====
call :TryLegacyCli
if %ERRORLEVEL% EQU 0 goto :SUCCESS

echo.
echo ===== Strategy 4: Manual token/ENV setup =====
call :TryManualSetup
if %ERRORLEVEL% EQU 0 goto :SUCCESS

echo.
echo [FATAL] All 4 strategies failed.
echo - Check that your token is correct and not expired.
echo - Ensure Python and huggingface_hub are installed and on PATH.
echo - You may also delete "%HF_STORED_TOKENS%" and try again.
goto :END

:SUCCESS
echo.
echo [OK] Hugging Face token appears to be configured.
echo Testing whoami...

call :TestWhoAmI

echo.
echo Done. You can now use tools that rely on Hugging Face auth.
goto :END

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Strategy 1 - hf auth login
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:TryHfAuthLogin
where hf >nul 2>&1
if errorlevel 1 (
  echo [INFO] 'hf' command not found, skipping Strategy 1.
  exit /b 1
)
echo [INFO] Running: hf auth login --token ***** --add-to-git-credential
hf auth login --token "%HF_TOKEN%" --add-to-git-credential
if errorlevel 1 (
  echo [WARN] hf auth login failed with code !ERRORLEVEL!.
  exit /b 1
)
exit /b 0

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Strategy 2 - python -m huggingface_hub.commands.huggingface_cli login
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:TryPythonCliLogin
where python >nul 2>&1
if errorlevel 1 (
  echo [INFO] 'python' not found on PATH, skipping Strategy 2.
  exit /b 1
)
echo [INFO] Running: python -m huggingface_hub.commands.huggingface_cli login
python -m huggingface_hub.commands.huggingface_cli login --token "%HF_TOKEN%" --add-to-git-credential
if errorlevel 1 (
  echo [WARN] python -m huggingface_hub.commands.huggingface_cli login failed with code !ERRORLEVEL!.
  exit /b 1
)
exit /b 0

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Strategy 3 - legacy `huggingface-cli` entrypoint
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:TryLegacyCli
where huggingface-cli >nul 2>&1
if errorlevel 1 (
  echo [INFO] 'huggingface-cli' not found, skipping Strategy 3.
  exit /b 1
)
echo [INFO] Running: huggingface-cli login --token ***** --add-to-git-credential
huggingface-cli login --token "%HF_TOKEN%" --add-to-git-credential
if errorlevel 1 (
  echo [WARN] huggingface-cli login failed with code !ERRORLEVEL!.
  exit /b 1
)
exit /b 0

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Strategy 4 - Manual token file + env vars + stored_tokens
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:TryManualSetup
echo [INFO] Writing token file: "%HF_TOKEN_FILE%"
> "%HF_TOKEN_FILE%" echo %HF_TOKEN%
if errorlevel 1 (
  echo [ERROR] Failed to write "%HF_TOKEN_FILE%".
  exit /b 1
)

echo [INFO] Writing stored_tokens file: "%HF_STORED_TOKENS%"
> "%HF_STORED_TOKENS%" echo {^"%HF_TOKEN_NAME%^":^"%HF_TOKEN%^"}
if errorlevel 1 (
  echo [ERROR] Failed to write "%HF_STORED_TOKENS%".
  exit /b 1
)

echo [INFO] Setting HF_TOKEN and HUGGINGFACE_TOKEN environment variables (persisted).
setx HF_TOKEN "%HF_TOKEN%" >nul
setx HUGGINGFACE_TOKEN "%HF_TOKEN%" >nul

REM Also set for current session
set HF_TOKEN=%HF_TOKEN%
set HUGGINGFACE_TOKEN=%HF_TOKEN%

where python >nul 2>&1
if errorlevel 1 (
  echo [WARN] 'python' not found; cannot fully test, but manual setup is done.
  exit /b 0
)

set "HF_TMP_PY=%TEMP%\hf_whoami_test_%RANDOM%.py"
> "%HF_TMP_PY%" echo from huggingface_hub import HfApi
>>"%HF_TMP_PY%" echo api = HfApi()
>>"%HF_TMP_PY%" echo me = api.whoami()
>>"%HF_TMP_PY%" echo print('Logged in as:', me)

python "%HF_TMP_PY%"
set TEST_RC=%ERRORLEVEL%
del "%HF_TMP_PY%" >nul 2>&1

if not %TEST_RC%==0 (
  echo [WARN] Python whoami() check failed. Manual setup may be incomplete.
  exit /b 1
)
exit /b 0

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Test helper - runs whoami if available
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:TestWhoAmI
where hf >nul 2>&1
if not errorlevel 1 (
  echo [INFO] Calling: hf auth whoami
  hf auth whoami
)

where huggingface-cli >nul 2>&1
if not errorlevel 1 (
  echo [INFO] Calling: huggingface-cli whoami
  huggingface-cli whoami
)
exit /b 0

:END
echo.
echo Press any key to close this window...
pause >nul
endlocal
