"""숫자+단위(건·개·명·번·곳·살·마리·권·시간·가지)를 고유어 수사로 바꿔 TTS가 '칠 건' 대신 '일곱 건'으로 읽게 한다. 1~99."""
import re
ONES = ["", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉"]
TENS = ["", "열", "스물", "서른", "마흔", "쉰", "예순", "일흔", "여든", "아흔"]
UNITS = "건|개|명|번|곳|살|마리|권|시간|가지|군데|차례"
def native(n):
    t, o = divmod(n, 10)
    if n == 20: return "스무"
    return (TENS[t] + ONES[o]) if n < 100 else str(n)
def normalize(text):
    return re.sub(rf"(?<![\d,.])(\d{{1,2}})\s*({UNITS})", lambda m: f"{native(int(m.group(1)))} {m.group(2)}", text)
if __name__ == "__main__":
    print(normalize("2020년 7건에서, 작년 39건, 올해는 38건, 20명, 3곳"))
