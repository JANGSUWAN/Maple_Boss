# Maple_Boss
메이플 보스 수익계산기
import json
import os
import requests
import streamlit as st

# 페이지 설정 (모바일 최적화 레이아웃)
st.set_page_config(
    page_title="메이플스토리 보스 정산 앱", page_icon="💰", layout="centered"
)

PRICE_FILE = "boss_prices.json"
RECORD_FILE = "boss_records.json"
ACCOUNT_FILE = "saved_accounts.json"  # 간편 로그인 계정 저장 파일


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


# 데이터 로드
prices = load_json(PRICE_FILE, {})
records = load_json(RECORD_FILE, {})
saved_accounts = load_json(ACCOUNT_FILE, {})  # 형식: {"계정별칭(또는 API키 일부)": "API키"}

# 세션 상태 초기화
if "api_key" not in st.session_state:
  st.session_state["api_key"] = ""
if "is_logged_in" not in st.session_state:
  st.session_state["is_logged_in"] = False

st.title("🛡️ 메이플스토리 보스 정산 & 기록 앱")

# ----------------- [ 로그인 상태가 아닐 때 : 네이버 스타일 간편 로그인 화면 ] -----------------
if not st.session_state["is_logged_in"]:
  st.markdown("### 🔐 넥슨 오픈 API 간편 로그인")

  # 저장된 간편 로그인 계정이 있는 경우 목록 표시
  if saved_accounts:
    st.markdown("#### 👤 최근 로그인한 계정 선택")
    for acc_name, acc_key in list(saved_accounts.items()):
      # 네이버 스타일 디자인: 계정 버튼과 삭제 버튼을 나란히 배치
      c_btn, c_del = st.columns([5, 1])
      with c_btn:
        if st.button(
            f"🟢 {acc_name}", key=f"login_{acc_name}", use_container_width=True
        ):
          st.session_state["api_key"] = acc_key
          st.session_state["is_logged_in"] = True
          st.rerun()
      with c_del:
        if st.button("✕", key=f"del_{acc_name}", help="계정 목록에서 삭제"):
          del saved_accounts[acc_name]
          save_json(ACCOUNT_FILE, saved_accounts)
          st.rerun()

    st.markdown("---")

  # 새로운 API 키 직접 입력 및 저장 영역
  st.markdown("#### ➕ 새 API 키 등록 및 로그인")
  with st.form("login_form"):
    input_name = st.text_input(
        "계정 별칭 (예: 본캐, 부캐1)", placeholder="목록에 표시될 이름"
    ).strip()
    input_key = st.text_input(
        "API 키 입력", type="password", placeholder="live_..."
    ).strip()
    save_checked = st.checkbox("간편 로그인 목록에 이 계정 저장", value=True)
    submitted = st.form_submit_button("🚀 로그인하기")

    if submitted:
      if input_key.startswith("live_") or len(input_key) > 10:
        st.session_state["api_key"] = input_key
        st.session_state["is_logged_in"] = True

        if save_checked:
          # 별칭이 없으면 API 키 앞부분으로 대체
          key_alias = (
              input_name
              if input_name
              else f"계정 ({input_key[:8]}...)"
          )
          saved_accounts[key_alias] = input_key
          save_json(ACCOUNT_FILE, saved_accounts)

        st.rerun()
      else:
        st.error("올바른 형식의 API 키를 입력해주세요.")

# ----------------- [ 로그인 완료 상태 : 메인 앱 화면 ] -----------------
else:
  # 상단에 로그아웃 버튼 배치
  col_top1, col_top2 = st.columns([4, 1])
  with col_top1:
    st.success("🟢 API 키 연동 완료 (간편 로그인 상태)")
  with col_top2:
    if st.button("로그아웃"):
      st.session_state["api_key"] = ""
      st.session_state["is_logged_in"] = False
      st.rerun()

  tab1, tab2 = st.tabs(["📊 보스 클리어 및 정산", "💎 결정석 가격표 조회"])

  with tab2:
    st.subheader("보스별 결정석 최신 가격표")
    for boss, info in prices.items():
      st.write(f"- **[{info['type']}]** {boss} : `{info['price']:,} 메소`")

  with tab1:
    char_name = st.text_input(
        "조회할 캐릭터명을 입력하세요", placeholder="예: 닉네임"
    ).strip()

    if char_name:
      ocid = get_ocid(char_name, st.session_state["api_key"])
      if not ocid:
        st.error(
            "캐릭터를 찾을 수 없습니다. 닉네임이나 API 키를 다시 확인해주세요."
        )
      else:
        st.success(f"✔️ '{char_name}' 캐릭터 연동 성공!")

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
            f"💡 **이달의 예상 총 수익 (월 환산):** `{monthly_total:,} 메소`\n\n"
            f"- **일일 보스:** {counts['일일']}개 종류 (월 30회 반영)\n"
            f"- **주간 보스:** {counts['주간']}개 종류 (월 4주 반영)\n"
            f"- **월간 보스:** {counts['월간']}개 종류 (월 1회 반영)"
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

{
    "일일_자쿰 (노멀)": {"type": "일일", "price": 349000},
    "일일_매그너스 (이지)": {"type": "일일", "price": 114000},
    "일일_매그너스 (노멀)": {"type": "일일", "price": 1160000},
    "일일_힐라 (노멀)": {"type": "일일", "price": 455000},
    "일일_힐라 (하드)": {"type": "일일", "price": 1280000},
    "일일_파풀라투스 (이지/노멀)": {"type": "일일", "price": 1200000},
    "일일_반레온 (이지/노멀/하드)": {"type": "일일", "price": 1070000},
    "일일_아카이럼 (이지/노멀)": {"type": "일일", "price": 1110000},
    "일일_핑크빈 (이지/노멀)": {"type": "일일", "price": 1360000},
    "일일_시그너스 (이지/노멀)": {"type": "일일", "price": 1360000},
    "주간_자쿰 (카오스)": {"type": "주간", "price": 4040000},
    "주간_매그너스 (하드)": {"type": "주간", "price": 4280000},
    "주간_파풀라투스 (카오스)": {"type": "주간", "price": 6550000},
    "주간_피에르 (카오스)": {"type": "주간", "price": 4080000},
    "주간_반반 (카오스)": {"type": "주간", "price": 4070000},
    "주간_블러디 퀸 (카오스)": {"type": "주간", "price": 4070000},
    "주간_벨룸 (카오스)": {"type": "주간", "price": 4640000},
    "주간_스우 (노멀)": {"type": "주간", "price": 8350000},
    "주간_스우 (하드)": {"type": "주간", "price": 48900000},
    "주간_스우 (익스트림)": {"type": "주간", "price": 545000000},
    "주간_데미안 (노멀)": {"type": "주간", "price": 8750000},
    "주간_데미안 (하드)": {"type": "주간", "price": 46400000},
    "주간_가디언 엔젤 슬라임 (노멀)": {"type": "주간", "price": 12700000},
    "주간_가디언 엔젤 슬라임 (카오스)": {"type": "주간", "price": 71300000},
    "주간_루시드 (이지)": {"type": "주간", "price": 14900000},
    "주간_루시드 (노멀)": {"type": "주간", "price": 17800000},
    "주간_루시드 (하드)": {"type": "주간", "price": 59700000},
    "주간_윌 (이지)": {"type": "주간", "price": 16100000},
    "주간_윌 (노멀)": {"type": "주간", "price": 20500000},
    "주간_윌 (하드)": {"type": "주간", "price": 73200000},
    "주간_더스크 (노멀)": {"type": "주간", "price": 22000000},
    "주간_더스크 (카오스)": {"type": "주간", "price": 66300000},
    "주간_듄켈 (노멀)": {"type": "주간", "price": 23700000},
    "주간_듄켈 (하드)": {"type": "주간", "price": 89600000},
    "주간_진 힐라 (노멀)": {"type": "주간", "price": 67600000},
    "주간_진 힐라 (하드)": {"type": "주간", "price": 100000000},
    "주간_선택받은 세렌 (노멀)": {"type": "주간", "price": 167000000},
    "주간_선택받은 세렌 (하드)": {"type": "주간", "price": 302000000},
    "주간_선택받은 세렌 (익스트림)": {"type": "주간", "price": 1840000000},
    "주간_감시자 칼로스 (이지)": {"type": "주간", "price": 238000000},
    "주간_감시자 칼로스 (노멀)": {"type": "주간", "price": 479000000},
    "주간_감시자 칼로스 (카오스)": {"type": "주간", "price": 1230000000},
    "주간_감시자 칼로스 (익스트림)": {"type": "주간", "price": 4104000000},
    "주간_카링 (이지)": {"type": "주간", "price": 320000000},
    "주간_카링 (노멀)": {"type": "주간", "price": 593000000},
    "주간_카링 (하드)": {"type": "주간", "price": 1739000000},
    "주간_카링 (익스트림)": {"type": "주간", "price": 5387000000},
    "주간_림보 (노멀)": {"type": "주간", "price": 995000000},
    "주간_림보 (하드)": {"type": "주간", "price": 2385000000},
    "주간_발드릭스 (노멀)": {"type": "주간", "price": 1368000000},
    "주간_발드릭스 (하드)": {"type": "주간", "price": 3078000000},
    "월간_검은 마법사 (하드)": {"type": "월간", "price": 465000000},
    "월간_검은 마법사 (익스트림)": {"type": "월간", "price": 5680000000}
}
