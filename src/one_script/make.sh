#!/bin/bash
TARGET="./nyxgo"
SCRIPT="./start.run"
mkdir "$TARGET"
cp "../core.py" "../loadNapCat.cjs" "../locate.yaml" "../source.json" "../requirements.txt" "$TARGET"
tar -czf core_data "$TARGET"
cat ./template.sh ./core_data > "$SCRIPT"
chmod +x "$SCRIPT"
rm -rf "$TARGET" ./core_data
echo "自解压脚本制作完毕->$SCRIPT"
