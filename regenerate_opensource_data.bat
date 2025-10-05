@echo off
echo ========================================
echo 重新生成所有开源字体数据
echo ========================================
echo.

echo [1/2] 提取字母数字（Roboto）...
python scripts\download_and_extract_opensource_fonts.py
echo.

echo [2/2] 提取标点符号（Noto Sans CJK）...
python scripts\extract_punctuation_from_opensource_fonts.py
echo.

echo ========================================
echo 完成！验证数据来源...
echo ========================================
python verify_opensource.py
echo.

pause

