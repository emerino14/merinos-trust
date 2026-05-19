@echo off
title Multi-Market Dashboard
echo ============================================
echo   Multi-Market Dashboard
echo   MNQ · MES · MGC (Oro) · BTC
echo ============================================
echo.
echo Paso 1: Instalando dependencias...
pip install -r requirements.txt --quiet
echo.
echo Paso 2: Iniciando dashboard en el navegador...
echo (Para cerrar, presiona Ctrl+C en esta ventana)
echo.
python -m streamlit run app.py --server.headless false
pause
