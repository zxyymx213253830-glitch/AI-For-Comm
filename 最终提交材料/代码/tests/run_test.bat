@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo.
echo ============================================================
echo   AI for Comm —— 双 Agent 协作测试
echo   运行中，请稍候（约 3-4 分钟）...
echo ============================================================
echo.
python tests/test_simple.py
echo.
echo ────────────────────────────────────────────────────────────
echo   运行结束！可查看 outputs/ 下的：
echo     - HTML 报告（report_*.html）
echo     - 终端日志（run_*.log）
echo ────────────────────────────────────────────────────────────
pause
