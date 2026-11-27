#!/usr/bin/env python3
"""새 영상 프로젝트 만들기: init.py <새 폴더> → 예시 설정(config.json)을 복사. 그다음 config를 주제에 맞게 고친다."""
import shutil, sys
from pathlib import Path
d = Path(sys.argv[1]); d.mkdir(parents=True, exist_ok=True)
src = Path(__file__).resolve().parent.parent / "references/example-config.json"
if (d / "config.json").exists(): sys.exit(f"{d}/config.json 이 이미 있습니다")
shutil.copy(src, d / "config.json"); print(d / "config.json")
