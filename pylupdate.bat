REM  Update Icons
python .\scripts\fix_svg.py .\app\resource\images\icons\
REM  Update Padding
python .\scripts\svg_scale.py .\app\resource\images\icons --trim-only
REM  Update Main.pro
pylupdate5 -noobsolete .\main.pro
REM  Update qrc
python .\scripts\dev.py all
