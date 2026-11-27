#!/bin/bash
# 전체 실행: make.sh <프로젝트 폴더> [h] [v] [f] [--say]
#   h=가로 1920x1080, v=세로 기본형, f=세로 쇼츠형 (생략하면 셋 다)
#   --say : 일레븐랩스 대신 맥 기본 음성(무료 초안)
# 필요: ffmpeg, uv (https://docs.astral.sh/uv/), 인터넷(글꼴·픽사베이)
set -e
D=$(cd "$1" && pwd); shift
HERE=$(cd "$(dirname "$0")" && pwd)
for c in ffmpeg ffprobe uv curl; do command -v $c >/dev/null || { echo "$c 가 필요합니다 (README 참고)"; exit 1; }; done
SAY=""; ORIENTS=()
for a in "$@"; do [ "$a" = "--say" ] && SAY="--say" || ORIENTS+=("$a"); done
[ ${#ORIENTS[@]} -eq 0 ] && ORIENTS=(h v f)
PW="uv run -q --with playwright python"
$PW -c "from playwright.sync_api import sync_playwright as s; p=s().start(); b=p.chromium.launch(); b.close(); p.stop()" 2>/dev/null \
  || command -v google-chrome >/dev/null || [ -d "/Applications/Google Chrome.app" ] \
  || uv run -q --with playwright playwright install chromium
python3 "$HERE/fetch_stock.py" sync "$D"
uv run -q --with elevenlabs python "$HERE/prep.py" "$D" $SAY
for o in "${ORIENTS[@]}"; do
  ( $PW "$HERE/overlays.py" "$D" "$o" && $PW "$HERE/graphics.py" "$D" "$o" ) &
done
wait
for o in "${ORIENTS[@]}"; do python3 "$HERE/assemble.py" "$D" "$o"; done
