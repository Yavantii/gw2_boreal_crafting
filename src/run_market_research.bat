@echo off
cd /d %~dp0
call ..\.venv\Scripts\activate.bat
python market_research.py >> ..\market_research.log 2>&1 