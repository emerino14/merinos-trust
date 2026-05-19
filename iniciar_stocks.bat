@echo off
title Stock Options Dashboard
echo ============================================
echo   Stock Options Dashboard
echo   BAC · WFC · SOFI · OXY · DVN
echo   GM  · MARA · RIVN · DKNG
echo ============================================
echo.
echo Paso 1: Instalando dependencias...
pip install -r requirements.txt --quiet
echo.
echo Paso 2: Iniciando dashboard en el navegador...
echo (Para cerrar, presiona Ctrl+C en esta ventana)
echo.
python -m streamlit run stocks_app.py --server.port 8502 --server.headless false
pause
