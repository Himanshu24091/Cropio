@echo off
echo Starting Converter Application...

REM Setup LaTeX environment
python setup_latex_env.py

REM Start Flask application
"C:\Users\himan\Desktop\converter\venv\Scripts\python.exe" app.py

pause
