@echo off
echo Installing Python packages...

REM Upgrade pip first (optional but recommended)
python -m pip install --upgrade pip

REM Install the required packages
python -m pip install streamlit>=1.28.0
python -m pip install openai>=1.0.0
python -m pip install fpdf>=1.7.2
python -m pip install python-docx>=0.8.11
python -m pip install pypdf>=3.0.0
python -m pip install pandas>=2.0.0

echo All packages installed!
pause
