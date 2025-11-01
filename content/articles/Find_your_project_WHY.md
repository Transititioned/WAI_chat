@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Set paths
SET VENV_PATH=C:\py310whisper\whisper310
SET ACTIVATE=%VENV_PATH%\Scripts\activate.bat
SET AUDIO_FOLDER=C:\transcribe
SET OUTPUT_FOLDER=%AUDIO_FOLDER%\output
SET LOG_FILE=%AUDIO_FOLDER%\whisperx_log.txt

:: Clear old log
echo [INFO] Starting transcription run at %DATE% %TIME% > "%LOG_FILE%"

:: Activate the venv
echo [INFO] Activating venv... >> "%LOG_FILE%"
call "%ACTIVATE%"

:: Make sure output folder exists
if not exist "%OUTPUT_FOLDER%" (
    mkdir "%OUTPUT_FOLDER%"
)

:: Loop over WAV files
for %%F in ("%AUDIO_FOLDER%\*.wav") do (
    echo. >> "%LOG_FILE%"
    echo [INFO] Transcribing %%~nxF >> "%LOG_FILE%"
    echo ------------------------------ >> "%LOG_FILE%"

    if exist "%%F" (
       
	   whisperx "%%F" ^
		--output_dir "%OUTPUT_FOLDER%" ^
		--output_format all ^
		--device cuda ^
		--no_align ^
		--vad_method silero ^
		>> "%LOG_FILE%" 2>&1

        if exist "%OUTPUT_FOLDER%\%%~nF.txt" (
            echo [SUCCESS] Output created for %%~nxF >> "%LOG_FILE%"
        ) else (
            echo [ERROR] No output found for %%~nxF >> "%LOG_FILE%"
        )
    ) else (
        echo [ERROR] File not found: %%F >> "%LOG_FILE%"
    )
)

echo Done. >> "%LOG_FILE%"
echo Press any key to exit.
pause >nul
