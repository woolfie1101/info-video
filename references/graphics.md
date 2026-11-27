# 그래픽 종류 (config 장면의 "graphic")

공통: `title`(위 제목), `source`(우하단 출처). 등장 시점은 자막 번호(0부터)로 지정 → 내레이션과 박자 맞춤.
모두 1000x800 무대 좌표로 그려 방향별 안전 영역에 자동 배치(자막·채널명 자리 침범 안 함).

## bar — 막대그래프 (흰 종이 배경)
막대가 아래에서 자라고 수치 태그가 아래→위로 닦이듯 등장.
```json
{"type":"bar","title":"...","unit":"건","suffix":"건","data":[["2020",7],["2026\n1~8월",38]],
 "highlight":[5,6], "at":1, "at_bar":{"5":2,"6":3}, "max":40, "source":"..."}
```
- `at`: 막대들이 차례로 나오기 시작하는 자막 번호 / `at_bar`: 특정 막대만 따로 나올 자막 번호
- `highlight`: 빨간색 강조 막대 / 라벨 줄바꿈은 `\n`

## cards — 아이콘 카드 2~3장 (흰 종이 배경, 평면 벡터, 굵은 검정 테두리)
```json
{"type":"cards","title":"...","cards":[{"icon":"phone","text":"휴대폰으로<br>문제 촬영","tag":"→ AI에 질문","at":1}]}
```
- 아이콘: phone, glasses, paper, warning, money, clock, person (scripts/graphics.py의 ICONS에 SVG 추가 가능)

## quote — 인용 카드 (검정 배경 + 빛줄기 회전, 명조체 타자 효과)
```json
{"type":"quote","lines":["한 줄","두 줄"],"highlight":["노랑으로 칠할 말"],"source":"한국일보(2026.11.17)","type_seconds":2.4}
```
- 한 줄 18자 이내(세로 화면에서도 안 잘리게). 기사 원문 문장 그대로 인용

## compare — 숫자 비교 카드 2장 (숫자가 0부터 올라감)
```json
{"type":"compare","title":"...","subtitle":"(100점 만점)","left":{"label":"집에서 본 시험","value":96,"suffix":"점"},
 "right":{"label":"교실 시험","value":48,"suffix":"점대"},"at":[1,2,3]}
```
- `at`: [왼쪽 카드, 오른쪽 카드, 오른쪽 숫자 올라가기] 자막 번호. 값은 정수만

## 새 종류 추가
`graphics.py`에 함수(si, g) → (css, body) 추가하고 `GRAPHICS`에 등록. 모션 규칙(references/style.md) 따를 것.
