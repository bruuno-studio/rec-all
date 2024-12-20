@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

:: Color output preparation
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set "DEL=%%a"
)

:: Title and welcome message
title rec-all Setup
echo.
echo =======================================
echo rec-all A Time Machine for the Everyday        
echo =======================================
echo.

:: Admin check
net session >nul 2>&1
if %errorLevel% neq 0 (
    call :colorEcho 0c "Error: Administrator privileges required."
    echo.
    echo Please run setup.bat as administrator.
    pause
    exit /b 1
)

:: Create cache directory for downloads
if not exist ".cache" mkdir .cache

:: Python check
python --version >nul 2>&1
if %errorLevel% neq 0 (
    call :colorEcho 0c "Python not found! Starting Python installation..."
    echo.
    
    :: Download Python if not in cache
    if not exist ".cache\python_installer.exe" (
        call :colorEcho 0e "Downloading Python installer..."
        echo.
        curl -L -o .cache\python_installer.exe https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
        if %errorLevel% neq 0 (
            call :colorEcho 0c "Failed to download Python! Check your internet connection."
            echo.
            pause
            exit /b 1
        )
    )
    
    .cache\python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    if %errorLevel% neq 0 (
        call :colorEcho 0c "Python installation failed!"
        echo.
        pause
        exit /b 1
    )
    
    :: Refresh PATH
    call :refreshEnv
)

:: CUDA check
nvidia-smi >nul 2>&1
if %errorLevel% equ 0 (
    set "CUDA_AVAILABLE=1"
    call :colorEcho 0a "NVIDIA GPU detected. CUDA support will be enabled."
    echo.
) else (
    set "CUDA_AVAILABLE=0"
    call :colorEcho 0e "No NVIDIA GPU found. Using CPU mode."
    echo.
)

:: Create required directories
if not exist "models" mkdir models

:: Install packages
call :colorEcho 0b "Installing required packages..."
echo.

:: Update pip
python -m pip install --upgrade pip

:: Force reinstall packages to ensure correct versions
pip uninstall opencv-python opencv-python-headless -y 2>nul
pip uninstall numpy -y 2>nul
pip uninstall Pillow -y 2>nul
pip uninstall easyocr -y 2>nul
pip uninstall torchvision -y 2>nul
pip uninstall imageio -y 2>nul
pip uninstall matplotlib -y 2>nul
pip uninstall scikit-image -y 2>nul
pip uninstall mediapipe -y 2>nul

:: Install base dependencies first
pip install Pillow>=9.1.0
pip install numpy==1.24.3
pip install matplotlib>=3.9.1

:: Install other dependencies
pip install opencv-python-headless>=4.8.0
pip install imageio>=2.35.1
pip install scikit-image>=0.24.0
pip install mediapipe>=0.10.14

:: Install PyTorch and related packages
pip install torch torchvision torchaudio

:: Install CUDA version if available
if "%CUDA_AVAILABLE%"=="1" (
    pip uninstall torch torchvision torchaudio -y
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
)

:: Install EasyOCR after its dependencies are in place
pip install easyocr

:: Install AI module requirements
pip install transformers sentencepiece

:: Download models if not already cached
if not exist "models\easyocr" (
    call :colorEcho 0b "Downloading EasyOCR models..."
    echo.
    python -c "import easyocr; reader = easyocr.Reader(['en', 'tr'])"
)

if not exist "models\git-base" (
    call :colorEcho 0b "Downloading AI models..."
    echo.
    python -c "from transformers import AutoProcessor, AutoModelForVision2Seq; processor = AutoProcessor.from_pretrained('microsoft/git-base', cache_dir='models/git-base'); model = AutoModelForVision2Seq.from_pretrained('microsoft/git-base', cache_dir='models/git-base')"
)

:: Create launcher with proper icon
call :colorEcho 0b "Creating launcher..."
echo.

:: Create shortcut directly using mklink
set "SHORTCUT_PATH=%~dp0rec-all.lnk"
set "TARGET_PATH=pythonw.exe"
set "ARGS=%~dp0rec-all.py"
set "ICON_PATH=%~dp0icon.ico"

:: Create VBS script for shortcut creation
(
echo Set ws = CreateObject^("WScript.Shell"^)
echo Set link = ws.CreateShortcut^("%SHORTCUT_PATH%"^)
echo link.TargetPath = "%TARGET_PATH%"
echo link.Arguments = "%ARGS%"
echo link.WorkingDirectory = "%~dp0"
echo link.IconLocation = "%ICON_PATH%"
echo link.Save
) > "%TEMP%\shortcut.vbs"

:: Run VBS script and cleanup
cscript //nologo "%TEMP%\shortcut.vbs"
if exist "%TEMP%\shortcut.vbs" del "%TEMP%\shortcut.vbs"

:: Verify shortcut creation
if exist "%SHORTCUT_PATH%" (
    call :colorEcho 0a "Setup completed successfully!"
    echo.
    echo.
    call :colorEcho 0b "Please use the rec-all shortcut in the installation folder to start the application."
) else (
    call :colorEcho 0c "Warning: Could not create shortcut. You can still run the application using rec-all.py"
)
echo.
pause
exit /b 0

:colorEcho
<nul set /p ".=%DEL%" > "%~2"
findstr /v /a:%1 /R "^$" "%~2" nul
del "%~2" > nul 2>&1
goto :eof

:refreshEnv
:: Refresh PATH
for /f "tokens=2*" %%a in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path') do set "PATH=!PATH!;%%b"
goto :eof 