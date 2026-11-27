# info-video — 설명 영상 자동 제작 스킬

대본만 쓰면 가로 영상, 세로 영상, 쇼츠형 영상 3종을 한 번에 만들어 줍니다.
실사 화면은 픽사베이 무료 스톡, 목소리는 일레븐랩스, 그래프는 움직이는 애니메이션입니다.

## 1. 설치 (처음 한 번)
1. ffmpeg: 맥은 `brew install ffmpeg` / 윈도우는 `winget install ffmpeg`
2. uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` (파이썬 패키지는 실행할 때 자동 설치)
3. 크롬이 없으면: `uv run --with playwright playwright install chromium`

## 2. 키 넣기 (각자 본인 것)
`~/.config/info-video/.env` 파일(또는 영상 프로젝트 폴더의 `.env`)에 아래처럼 적습니다. 키는 다른 곳에 올리거나 공유하지 마세요.
```
PIXABAY_API_KEY=여기에_픽사베이_키
ELEVENLABS_API_KEY=여기에_일레븐랩스_키
```
- 픽사베이(필수, 무료): https://pixabay.com/api/docs/ → 로그인하면 페이지에 내 키가 보입니다
- 일레븐랩스(선택): https://elevenlabs.io → 프로필 → API Keys. 또는 `npx -y @elevenlabs/cli@latest onboard init` 실행으로 로그인
  - 없으면 맥 기본 음성으로 초안이 만들어집니다

## 3. 만들기
```
python3 scripts/init.py ~/videos/내주제        # 예시 설정 복사
# ~/videos/내주제/config.json 을 주제에 맞게 수정 (SKILL.md 참고)
scripts/make.sh ~/videos/내주제                # out_h.mp4, out_v.mp4, out_f.mp4
```
예시 설정 그대로 `make.sh`를 돌리면 샘플 영상('AI로 인한 대학 시험 부정행위')이 나옵니다.

## 저작권
- 픽사베이 콘텐츠는 픽사베이 라이선스를 따릅니다(상업 이용 가능, 원본 그대로 재배포·판매 금지). 스킬에는 스톡 파일이 들어 있지 않고 실행할 때 각자 받습니다
- 글꼴: Noto Sans KR, 나눔명조(구글 폰트, OFL)
