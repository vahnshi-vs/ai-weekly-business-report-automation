@echo off
cd /d "C:\Users\svans\weekly_beauty_report_project"

echo Running weekly dashboard pipeline...
python main_pipeline.py

if errorlevel 1 (
    echo main_pipeline.py failed.
    pause
    exit /b 1
)

echo Pipeline completed successfully.
pause