@echo off
cd /d "%~dp0"
echo KB 소상공인 창업 입지 추천 서비스 시작 중...
start http://localhost:8501
python -m streamlit run app.py --server.port 8501
pause
