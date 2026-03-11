REM  Update Icons
python .\scripts\fix_svg.py
REM  Update Padding
python .\scripts\svg_scale.py .\app\resource\images\fluentIcon --trim-only
REM  Update Main.pro
pylupdate5 -noobsolete .\main.pro
REM  Update qrc
python .\scripts\dev.py all
