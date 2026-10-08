import json
import os
import requests
import streamlit as st

페이지 설정
st.set_page_config(
page_title="메이플스토리 보스 정산 앱", page_icon="💰", layout="centered"
)

PRICE_FILE = "boss_prices.json"
RECORD_FILE = "boss_records.json"

def load_json(file_path, default_data):
if not os.path.exists(file_path):
with open(file_path, "w", encoding="utf-8") as f:
json.dump(default_data, f, ensure_ascii=False, indent=4)
return default_data
with open(file_path, "r", encoding="utf-8") as f:
try:
return json.load(f)
except json.JSONDecodeError:
return default_data

def save_json(file_path, data):
with open(file_path, "w", encoding="utf-8") as f:
json.dump(data, f, ensure_ascii=False, indent=4)

def get_ocid(character_name, api_key):
url = (
"https://open.api.nexon.com/maplestory/v1/id?character_name="
f"{character_name}"
)
headers = {"accept": "application/json", "x-nxopen-api-key": api_key}
response = requests.get(url, headers=headers)
if response.status_code == 200:
return response.json().get("ocid")
return None

데이터 로드
prices = load_json(PRICE_FILE, {})
records = load_json(RECORD_FILE, {})

사이드바 설정 (사용자별 API 키 입력)
st.sidebar.header("🔑 API 설정")
user_api_key = st.sidebar.text_input(
"넥슨 오픈 API 키 입력", type="password", placeholder="live_..."
).strip()
st.sidebar.markdown(
"(openapi.nexon.com 에서 발급받은 본인의 키를 입력하세요)"
)

st.title("🛡️ 메이플스토리 보스 정산 & 기록 앱")
st.markdown("캐릭터를 연동하고 이번 주 클리어한 보스를 체크해 보세요!")

if not user_api_key:
st.warning("👈 왼쪽 사이드바에 넥슨 오픈 API 키를 먼저 입력해주세요.")
else:
tab1, tab2 = st.tabs(["📊 보스 클리어 및 정산", "💎 결정석 가격표 조회"])

with tab2:
st.subheader("보스별 결정석 최신 가격표")
for boss, info in prices.items():
st.write(f"- [{info['type']}] {boss} : {info['price']:,} 메소")

with tab1:
char_name = st.text_input(
"조회할 캐릭터명을 입력하세요", placeholder="예: 닉네임"
).strip()

if char_name:
ocid = get_ocid(char_name, user_api_key)
if not ocid:
st.error(
"캐릭터를 찾을 수 없습니다. 닉네임이나 API 키를 다시 확인해주세요."
)
else:
st.success("✔️ 캐릭터 연동 완료!")

char_data = records.get(char_name, {"cleared": []})
saved_cleared = char_data["cleared"]

st.markdown("---")
st.subheader("📋 보스 클리어 체크리스트")

cleared_bosses = []
for boss, info in prices.items():
is_checked = boss in saved_cleared
if st.checkbox(
f"[{info['type']}] {boss} ({info['price']:,} 메소)",
value=is_checked,
key=boss,
):
cleared_bosses.append(boss)

if st.button("💾 클리어 기록 저장 및 정산 계산"):
records[char_name] = {"cleared": cleared_bosses}
save_json(RECORD_FILE, records)
st.toast("기록이 성공적으로 저장되었습니다!", icon="✅")

uncleared_bosses = [b for b in prices.keys() if b not in cleared_bosses]
weekly_total = sum(prices[b]["price"] for b in cleared_bosses)

monthly_total = 0
counts = {"일일": 0, "주간": 0, "월간": 0}
for b in cleared_bosses:
b_type = prices[b]["type"]
b_price = prices[b]["price"]
if b_type == "일일":
monthly_total += b_price * 30
counts["일일"] += 1
elif b_type == "주간":
monthly_total += b_price * 4
counts["주간"] += 1
elif b_type == "월간":
monthly_total += b_price * 1
counts["월간"] += 1

st.markdown("---")
st.subheader("📈 정산 및 월 환산 리포트")

col1, col2 = st.columns(2)
with col1:
st.metric(
label="이번 주 클리어 보스",
value=f"{len(cleared_bosses)}개",
delta=f"미클리어 {len(uncleared_bosses)}개",
)
with col2:
st.metric(
label="이번 주 주간 보스 수익",
value=f"{weekly_total:,} 메소",
)

st.info(
f"💡 이달의 예상 총 수익 (월 환산):{monthly_total:,} 메소\n\n"
f"- 일일 보스: {counts['일일']}개 종류 (월 30회 반영)\n"
f"- 주간 보스: {counts['주간']}개 종류 (월 4주 반영)\n"
f"- 월간 보스: {counts['월간']}개 종류 (월 1회 반영)"
)

st.markdown("### 📝 상세 클리어 상태 표")
status_data = []
for b in prices.keys():
status = "✔️ 클리어" if b in cleared_bosses else "❌ 미클리어"
status_data.append({
"주기": prices[b]["type"],
"보스명": b,
"상태": status,
"결정석 가격": f"{prices[b]['price']:,} 메소",
})
st.dataframe(status_data, use_container_width=True)