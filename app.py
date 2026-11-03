# ============================================================
# language app v2 - 북두칠성 발음 교정 앱 (Streamlit)
# ------------------------------------------------------------
# 영어 트랙 : 한국어 모국어 화자가 영어를 배울 때의 발음 오류
# 일본어 트랙: 일본어 모국어 화자가 한국어 발음을 배울 때의 오류
# 별 7개 = (오류 3개 x [개념·연습, 퀴즈]) + 최종 테스트
# ============================================================

import difflib
import math
import os
import random
import re
import tempfile

import streamlit as st
import streamlit.components.v1 as components


# ------------------------------------------------------------
# 1. 페이지 설정
# ------------------------------------------------------------
st.set_page_config(page_title="language app", page_icon="🌌", layout="centered")


# ------------------------------------------------------------
# 2. 도우미: HTML을 안전하게 화면에 그리는 함수
#    (빈 줄이 있으면 Streamlit이 HTML을 끊어 읽어서, 빈 줄과 들여쓰기를 제거)
# ------------------------------------------------------------
def html(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    body = "\n".join(lines)
    st.markdown("<div>\n" + body + "\n</div>", unsafe_allow_html=True)


# ------------------------------------------------------------
# 3. 전체 디자인(CSS) - 붉은색 컨셉
# ------------------------------------------------------------
html("""
<style>
.stApp {
    background: radial-gradient(circle at 20% 0%, #3b0a14 0%, #14060a 55%, #0b0306 100%);
}
.hero {
    background: linear-gradient(135deg, #b91c1c 0%, #e11d48 60%, #7f1d1d 100%);
    border-radius: 22px; padding: 22px 26px; color: #fff; margin-bottom: 12px;
    box-shadow: 0 10px 30px rgba(225, 29, 72, 0.25);
}
.hero h1 { margin: 0; font-size: 2rem; color: #fff; }
.hero p { margin: 6px 0 0 0; opacity: 0.92; }
.bigword { font-size: 2.6rem; font-weight: 800; color: #ff6b6b; line-height: 1.1; }
.cap { text-align: center; color: #ffd0d0; font-weight: 700; margin-top: 4px; font-size: 0.95rem; }
.note { text-align: center; color: #f5b5b5; font-size: 0.85rem; margin-bottom: 8px; }
.dipper { max-width: 560px; margin: 0 auto 6px auto; }

/* 북두칠성 별 */
.star.lit { fill: #ff3b3b; filter: drop-shadow(0 0 8px #ff4d4d); animation: glow 2.4s ease-in-out infinite alternate; }
.star.next { fill: #6b1a26; stroke: #ff8a8a; stroke-width: 1.5; stroke-dasharray: 3 2; animation: blink 1.3s ease-in-out infinite; }
.star.off { fill: #3a1218; }
@keyframes glow { from { opacity: 0.75; } to { opacity: 1; } }
@keyframes blink { from { opacity: 0.4; } to { opacity: 1; } }

/* 접촉 지점 표시 */
.touch { fill: none; stroke: #ffd166; stroke-width: 3; stroke-dasharray: 4 3; animation: blink 1s infinite alternate; }

/* 휴지 흔들림 (평음/격음/경음) */
.tissue { transform-box: fill-box; transform-origin: 50% 0%; }
.sway-weak { animation: swayweak 1.1s ease-in-out infinite alternate; }
.sway-mid { animation: swaymid 0.9s ease-in-out infinite alternate; }
.sway-strong { animation: swaystrong 0.6s ease-in-out infinite alternate; }
@keyframes swayweak { from { transform: rotate(-1deg); } to { transform: rotate(1deg); } }
@keyframes swaymid { from { transform: rotate(-7deg); } to { transform: rotate(7deg); } }
@keyframes swaystrong { from { transform: rotate(-3deg); } to { transform: rotate(34deg); } }

/* 숨 길이 막대 */
.barrow { display: flex; align-items: center; gap: 10px; margin: 6px 0; color: #ffd0d0; }
.barlabel { width: 120px; font-size: 0.9rem; }
.bar { height: 16px; border-radius: 8px; background: linear-gradient(90deg, #e11d48, #ff6b6b); }

/* 음절 글자 크기 시각화 */
.syl-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,120,120,0.25);
            border-radius: 16px; padding: 10px 16px; margin-bottom: 10px; }
.syl-row { display: flex; align-items: baseline; gap: 4px; margin: 4px 0; flex-wrap: wrap; }
.syl-tag { width: 110px; font-size: 0.8rem; color: #f5b5b5; }
.syl-k { font-size: 28px; border: 1px dashed #7a3a44; border-radius: 8px; padding: 0 8px; color: #f5b5b5; }
.syl-c { font-size: 18px; color: #e6a0a0; opacity: 0.8; }
.syl-v { font-size: 54px; font-weight: 800; color: #ff4d4d; }

/* 박자 + 노래방 가사 */
.beat { display: inline-block; min-width: 70px; text-align: center; padding: 8px 10px; margin-right: 4px;
        border-radius: 10px; background: #3a1218; color: #ffd0d0; font-size: 1.3rem; }
.beat.k { background: #b91c1c; color: #fff; }
.karaoke { display: inline-block; position: relative; font-size: 2rem; font-weight: 800; color: #6b3a44;
           margin-right: 18px; }
.karaoke span { position: absolute; left: 0; top: 0; overflow: hidden; white-space: nowrap; width: 0;
                color: #ff4d4d; animation: fillup 1s linear forwards; }
@keyframes fillup { from { width: 0; } to { width: 100%; } }

table { color: #fde8e8; }
</style>
""")


# ------------------------------------------------------------
# 4. 음성 인식 부품 (브라우저의 Web Speech API 사용)
#    - 🔊 듣기: 브라우저가 단어를 읽어 줌
#    - 🎤 말하기: 마이크로 말하면 글자로 바꿔서 Python으로 전달
#    - 말하는 동안 소리 파형이 심전도처럼 표시됨
# ------------------------------------------------------------
VOICE_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { margin: 0; font-family: sans-serif; color: #fde8e8; background: transparent; }
  .row { display: flex; gap: 8px; flex-wrap: wrap; }
  button { background: #e11d48; border: none; color: #fff; padding: 10px 16px; border-radius: 12px;
           font-size: 15px; font-weight: 700; cursor: pointer; }
  button.alt { background: #7f1d2e; }
  button.rec { background: #ff4d4d; animation: pulse 1s infinite; }
  @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255,77,77,.7); } 100% { box-shadow: 0 0 0 14px rgba(255,77,77,0); } }
  #status { margin-top: 8px; font-size: 14px; min-height: 20px; color: #ffd0d0; }
  canvas { width: 100%; height: 50px; margin-top: 6px; background: #1c070c; border-radius: 10px; }
</style>
</head>
<body>
<div class="row">
  <button id="speak" class="alt">🔊 듣기</button>
  <button id="mic">🎤 말하기</button>
</div>
<div id="status"></div>
<canvas id="wave" width="400" height="50"></canvas>

<script>
  // ---- Streamlit과 통신하는 기본 함수 ----
  function send(type, data) {
    window.parent.postMessage(Object.assign({ isStreamlitMessage: true, type: type }, data), "*");
  }
  function setHeight() {
    send("streamlit:setFrameHeight", { height: args.mode === "listen" ? 90 : 160 });
  }

  var args = { mode: "both", lang: "en-US", target: "", speak: "" };
  var statusEl = document.getElementById("status");
  var micBtn = document.getElementById("mic");
  var speakBtn = document.getElementById("speak");
  var canvas = document.getElementById("wave");
  var ctx = canvas.getContext("2d");

  window.addEventListener("message", function (event) {
    var data = event.data;
    if (data && data.type === "streamlit:render") {
      args = Object.assign(args, data.args || {});
      var listenOnly = (args.mode === "listen");
      micBtn.style.display = listenOnly ? "none" : "inline-block";
      canvas.style.display = listenOnly ? "none" : "block";
      setHeight();
    }
  });
  send("streamlit:componentReady", { apiVersion: 1 });

  // ---- 듣기 ----
  speakBtn.onclick = function () {
    if (!("speechSynthesis" in window)) {
      statusEl.textContent = "이 브라우저는 음성 재생을 지원하지 않아요.";
      return;
    }
    var u = new SpeechSynthesisUtterance(args.speak || args.target);
    u.lang = args.lang;
    u.rate = 0.8;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  };

  // ---- 소리 파형 그리기 ----
  var stream = null, audioCtx = null, rafId = null;

  function drawWave(analyser) {
    var buf = new Uint8Array(analyser.fftSize);
    function loop() {
      analyser.getByteTimeDomainData(buf);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.beginPath();
      ctx.lineWidth = 2;
      ctx.strokeStyle = "#ff4d4d";
      for (var i = 0; i < buf.length; i++) {
        var x = i / buf.length * canvas.width;
        var y = buf[i] / 255 * canvas.height;
        if (i === 0) { ctx.moveTo(x, y); } else { ctx.lineTo(x, y); }
      }
      ctx.stroke();
      rafId = requestAnimationFrame(loop);
    }
    loop();
  }

  function stopWave() {
    if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    if (stream) { stream.getTracks().forEach(function (t) { t.stop(); }); stream = null; }
    if (audioCtx) { audioCtx.close(); audioCtx = null; }
  }

  function startWave() {
    // 파형은 보너스 기능이라, 실패해도 음성 인식은 계속됨
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (s) {
      stream = s;
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      var src = audioCtx.createMediaStreamSource(s);
      var analyser = audioCtx.createAnalyser();
      analyser.fftSize = 1024;
      src.connect(analyser);
      drawWave(analyser);
    }).catch(function () {});
  }

  // ---- 말하기(음성 인식) ----
  var recognizing = false;

  micBtn.onclick = function () {
    if (recognizing) { return; }
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      statusEl.textContent = "이 브라우저는 음성 인식을 지원하지 않아요. Chrome이나 Edge를 사용해 주세요.";
      return;
    }
    var rec = new SR();
    rec.lang = args.lang;
    rec.interimResults = false;
    rec.maxAlternatives = 5;
    rec.continuous = false;

    rec.onstart = function () {
      recognizing = true;
      micBtn.classList.add("rec");
      statusEl.textContent = "듣고 있어요… 말해 보세요!";
      startWave();
    };
    rec.onresult = function (e) {
      var res = e.results[0];
      var alts = [];
      for (var i = 0; i < res.length; i++) {
        alts.push({ text: res[i].transcript, conf: res[i].confidence });
      }
      statusEl.textContent = "인식 완료!";
      send("streamlit:setComponentValue", { value: { alts: alts, t: Date.now() }, dataType: "json" });
    };
    rec.onerror = function (e) {
      if (e.error === "no-speech") {
        statusEl.textContent = "소리가 들리지 않았어요. 다시 눌러 주세요.";
      } else if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        statusEl.textContent = "마이크 권한을 허용해 주세요. (주소창 왼쪽 자물쇠)";
      } else {
        statusEl.textContent = "오류: " + e.error;
      }
    };
    rec.onend = function () {
      recognizing = false;
      micBtn.classList.remove("rec");
      stopWave();
    };
    rec.start();
  };
</script>
</body>
</html>
"""


@st.cache_resource
def get_voice_component():
    """VOICE_HTML을 임시 폴더에 저장하고 Streamlit 부품으로 등록한다."""
    folder = os.path.join(tempfile.gettempdir(), "language_app_voice_component")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(VOICE_HTML)
    return components.declare_component("language_app_voice", path=folder)


voice_box = get_voice_component()


# ------------------------------------------------------------
# 5. 시각자료 만들기 (SVG / HTML)
# ------------------------------------------------------------

# ----- 5-1. 북두칠성 -----
# 별 1번 = 손잡이 끝(알카이드) ... 별 7번 = 국자 앞쪽(두베)
STAR_POS = [(40, 70), (110, 95), (180, 118), (250, 138), (275, 205), (385, 215), (400, 148)]
STAR_LINES = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 3)]


def star_points(cx, cy, r_out, r_in):
    """5각 별의 꼭짓점 좌표 문자열을 만든다."""
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        r = r_out if i % 2 == 0 else r_in
        pts.append(f"{cx + r * math.cos(ang):.1f},{cy - r * math.sin(ang):.1f}")
    return " ".join(pts)


def dipper_svg(done, labels):
    nxt = next((i for i, d in enumerate(done) if not d), None)
    rng = random.Random(7)
    parts = ['<rect width="460" height="270" rx="18" fill="#12050a"/>']
    # 배경의 작은 별들
    for _ in range(45):
        parts.append(
            f'<circle cx="{rng.randint(5, 455)}" cy="{rng.randint(5, 265)}" '
            f'r="{rng.choice([0.6, 0.9, 1.2])}" fill="#ffd0d0" opacity="0.35"/>'
        )
    # 별 사이의 선 (두 별이 모두 밝으면 밝은 선)
    for a, b in STAR_LINES:
        lit = done[a] and done[b]
        color = "#ff5a5a" if lit else "#4a1a22"
        width = 3 if lit else 1.5
        (x1, y1), (x2, y2) = STAR_POS[a], STAR_POS[b]
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>'
        )
    # 별과 이름표
    for i, (x, y) in enumerate(STAR_POS):
        if done[i]:
            cls = "star lit"
        elif i == nxt:
            cls = "star next"
        else:
            cls = "star off"
        parts.append(f'<polygon class="{cls}" points="{star_points(x, y, 17, 7)}"/>')
        parts.append(
            f'<text x="{x}" y="{y + 36}" text-anchor="middle" font-size="11" fill="#f5b5b5">'
            f'{i + 1}. {labels[i]}</text>'
        )
    return '<div class="dipper"><svg viewBox="0 0 460 270" style="width:100%;height:auto">' + "".join(parts) + "</svg></div>"


# ----- 5-2. 혀 단면도 -----
PALATE = "M 30 38 Q 58 28 68 54 Q 150 12 218 44 Q 265 66 278 125"
TONGUE = {
    "tap": "M 280 175 Q 195 168 135 136 Q 95 114 74 72",
    "lateral": "M 280 175 Q 195 165 135 132 Q 96 108 74 70",
    "r": "M 280 175 Q 205 170 160 135 Q 122 105 150 78",
    "velar": "M 280 175 Q 235 152 220 112 Q 214 82 220 52",
    "flat": "M 280 175 Q 200 180 120 172",
}


def tongue_svg(tongue_key, caption, note="", touch=None, lips_closed=False):
    lower_lip_y = 46 if lips_closed else 82
    contact = ""
    if touch:
        contact = f'<circle class="touch" cx="{touch[0]}" cy="{touch[1]}" r="11"/>'
    return f"""
    <svg viewBox="0 0 300 200" style="width:100%;height:auto">
    <rect width="300" height="200" rx="14" fill="#1c070c"/>
    <path d="{PALATE}" fill="none" stroke="#f5b5b5" stroke-width="4" stroke-linecap="round"/>
    <path d="{TONGUE[tongue_key]}" fill="none" stroke="#ff4d4d" stroke-width="14" stroke-linecap="round"/>
    <rect x="8" y="30" width="26" height="14" rx="7" fill="#e11d48"/>
    <rect x="8" y="{lower_lip_y}" width="26" height="14" rx="7" fill="#e11d48"/>
    {contact}
    </svg>
    <div class="cap">{caption}</div>
    <div class="note">{note}</div>
    """


def viz_rl():
    cols = st.columns(3)
    items = [
        ("tap", "오리의 ㄹ = 탄설음", "혀끝이 톡 한 번 치고 바로 내려와요", (76, 62)),
        ("lateral", "달의 ㄹ = 영어 l", "혀끝을 붙인 채 공기는 양옆으로", (76, 62)),
        ("r", "영어 r", "혀끝이 어디에도 닿지 않아요!", None),
    ]
    for col, (key, cap, note, touch) in zip(cols, items):
        with col:
            html(tongue_svg(key, cap, note, touch))


# ----- 5-3. 심전도 스타일 모음 그래프 (eat vs it) -----
def viz_ecg():
    html("""
    <svg viewBox="0 0 640 300" style="width:100%;height:auto">
    <defs>
      <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
        <path d="M20 0H0V20" fill="none" stroke="#5a1f2a" stroke-width="0.6"/>
      </pattern>
    </defs>
    <rect width="640" height="300" rx="14" fill="#1c070c"/>
    <rect width="640" height="300" rx="14" fill="url(#grid)"/>
    <text x="16" y="24" font-size="13" fill="#ff6b6b">빨강 = 혀 높이 (위로 갈수록 높음)</text>
    <text x="16" y="44" font-size="13" fill="#ffe3c2">살구색 = 입 벌림 (아래로 갈수록 크게 벌림)</text>
    <polyline points="20,180 55,80 295,80 330,180" fill="none" stroke="#ff4d4d" stroke-width="4" stroke-linejoin="round"/>
    <polyline points="20,225 55,208 295,208 330,225" fill="none" stroke="#ffe3c2" stroke-width="3" stroke-linejoin="round"/>
    <text x="175" y="68" text-anchor="middle" font-size="13" fill="#ffd0d0">eat /iː/  길고 긴장, 혀 가장 높음</text>
    <text x="40" y="272" font-size="40" font-weight="800" fill="#ff6b6b" textLength="270" lengthAdjust="spacingAndGlyphs">e a t</text>
    <polyline points="360,180 385,110 520,110 545,180" fill="none" stroke="#ff4d4d" stroke-width="4" stroke-linejoin="round"/>
    <polyline points="360,225 385,192 520,192 545,225" fill="none" stroke="#ffe3c2" stroke-width="3" stroke-linejoin="round"/>
    <text x="452" y="98" text-anchor="middle" font-size="13" fill="#ffd0d0">it /ɪ/  짧고 이완, 입 조금 더 열림</text>
    <text x="380" y="272" font-size="40" font-weight="800" fill="#ff6b6b" textLength="120" lengthAdjust="spacingAndGlyphs">it</text>
    </svg>
    """)
    st.caption("그래프가 옆으로 길수록 소리도 길어요. eat는 it보다 약 2배 길게!")


def viz_e_table():
    st.markdown(
        """
| 철자 | 예시 | 소리 | 한국어로 느끼면 |
|---|---|---|---|
| e | bed | /ɛ/ | ㅔ보다 입을 조금 더 벌려서 |
| ee, ea | eat, feet | /iː/ | 길게 늘인 ㅣ |
| 단어 끝 e | make | 소리 없음 (앞 모음이 길어짐) | 메이크 |
| 약한 음절의 e | taken | /ə/ | 힘 빠진 "어" |
"""
    )


# ----- 5-4. 음절: 글자 크기 시각화 -----
SYLLABLE_WORDS = [
    ("speak", [("sp", 0), ("ea", 1), ("k", 0)], ["스", "피", "크"], 1),
    ("street", [("str", 0), ("ee", 1), ("t", 0)], ["스", "트", "리", "트"], 1),
    ("strike", [("str", 0), ("i", 1), ("ke", 0)], ["스", "트", "라", "이", "크"], 1),
    ("desk", [("d", 0), ("e", 1), ("sk", 0)], ["데", "스", "크"], 1),
]


def viz_syllables():
    for word, parts, korean, count in SYLLABLE_WORDS:
        k_html = "".join(f'<span class="syl-k">{k}</span>' for k in korean)
        e_html = "".join(
            f'<span class="syl-v">{t}</span>' if big else f'<span class="syl-c">{t}</span>'
            for t, big in parts
        )
        html(f"""
        <div class="syl-card">
        <b style="color:#ffd0d0">{word}</b>
        <div class="syl-row"><span class="syl-tag">한국어식 ({len(korean)}박)</span>{k_html}</div>
        <div class="syl-row"><span class="syl-tag">영어 ({count}음절)</span>{e_html}</div>
        </div>
        """)
    st.caption("영어는 모음이 박자를 만들어요. 자음은 작고 빠르게, 모음에 붙여서!")


# ----- 5-5. 일본어 트랙: 휴지 흔들림 -----
def viz_tissue():
    html("""
    <svg viewBox="0 0 480 210" style="width:100%;height:auto">
    <rect width="480" height="210" rx="14" fill="#1c070c"/>
    <g>
      <rect x="55" y="25" width="50" height="6" rx="3" fill="#f5b5b5"/>
      <g class="tissue sway-mid"><rect x="78" y="31" width="5" height="85" rx="2" fill="#ffe3c2"/></g>
      <circle cx="30" cy="115" r="3" fill="#ff8a8a"><animate attributeName="cx" from="20" to="70" dur="1.2s" repeatCount="indefinite"/></circle>
      <circle cx="30" cy="125" r="3" fill="#ff8a8a"><animate attributeName="cx" from="10" to="60" dur="1.4s" repeatCount="indefinite"/></circle>
      <text x="80" y="155" text-anchor="middle" font-size="26" font-weight="800" fill="#ff6b6b">가</text>
      <text x="80" y="178" text-anchor="middle" font-size="13" fill="#ffd0d0">평음 (예사소리)</text>
      <text x="80" y="196" text-anchor="middle" font-size="12" fill="#f5b5b5">숨 보통</text>
    </g>
    <g>
      <rect x="215" y="25" width="50" height="6" rx="3" fill="#f5b5b5"/>
      <g class="tissue sway-strong"><rect x="238" y="31" width="5" height="85" rx="2" fill="#ffe3c2"/></g>
      <circle cx="190" cy="105" r="3" fill="#ff8a8a"><animate attributeName="cx" from="180" to="235" dur="0.7s" repeatCount="indefinite"/></circle>
      <circle cx="190" cy="115" r="3" fill="#ff8a8a"><animate attributeName="cx" from="175" to="230" dur="0.8s" repeatCount="indefinite"/></circle>
      <circle cx="190" cy="125" r="3" fill="#ff8a8a"><animate attributeName="cx" from="170" to="225" dur="0.6s" repeatCount="indefinite"/></circle>
      <circle cx="190" cy="135" r="3" fill="#ff8a8a"><animate attributeName="cx" from="185" to="240" dur="0.9s" repeatCount="indefinite"/></circle>
      <text x="240" y="155" text-anchor="middle" font-size="26" font-weight="800" fill="#ff6b6b">카</text>
      <text x="240" y="178" text-anchor="middle" font-size="13" fill="#ffd0d0">격음 (거센소리)</text>
      <text x="240" y="196" text-anchor="middle" font-size="12" fill="#f5b5b5">숨 강하게 터뜨림</text>
    </g>
    <g>
      <rect x="375" y="25" width="50" height="6" rx="3" fill="#f5b5b5"/>
      <g class="tissue sway-weak"><rect x="398" y="31" width="5" height="85" rx="2" fill="#ffe3c2"/></g>
      <text x="400" y="155" text-anchor="middle" font-size="26" font-weight="800" fill="#ff6b6b">까</text>
      <text x="400" y="178" text-anchor="middle" font-size="13" fill="#ffd0d0">경음 (된소리)</text>
      <text x="400" y="196" text-anchor="middle" font-size="12" fill="#f5b5b5">목에 힘, 숨 거의 없음</text>
    </g>
    </svg>
    """)
    st.caption("입 앞에 휴지(또는 손바닥)를 대고 가 → 카 → 까 를 말해 보세요. 흔들림이 달라야 해요!")
    html("""
    <div>
    <div class="barrow"><span class="barlabel">까 (경음)</span><div class="bar" style="width:40px"></div></div>
    <div class="barrow"><span class="barlabel">가 (평음)</span><div class="bar" style="width:120px"></div></div>
    <div class="barrow"><span class="barlabel">카 (격음)</span><div class="bar" style="width:260px"></div></div>
    <div class="note" style="text-align:left">▲ 자음 뒤에 숨이 새어 나오는 시간(대략적인 비교)</div>
    </div>
    """)


# ----- 5-6. 일본어 트랙: 모음 지도 + 입술 모양 -----
def viz_vowel_map():
    html("""
    <svg viewBox="0 0 400 290" style="width:100%;height:auto">
    <rect width="400" height="290" rx="14" fill="#1c070c"/>
    <text x="16" y="22" font-size="12" fill="#f5b5b5">↑ 혀가 높음</text>
    <text x="16" y="276" font-size="12" fill="#f5b5b5">↓ 혀가 낮음</text>
    <text x="90" y="276" font-size="12" fill="#f5b5b5">← 혀가 앞</text>
    <text x="300" y="276" font-size="12" fill="#f5b5b5">혀가 뒤 →</text>
    <circle cx="70" cy="55" r="17" fill="none" stroke="#f5b5b5" stroke-width="2"/>
    <text x="70" y="61" text-anchor="middle" font-size="16" fill="#f5b5b5">い</text>
    <circle cx="105" cy="130" r="17" fill="none" stroke="#f5b5b5" stroke-width="2"/>
    <text x="105" y="136" text-anchor="middle" font-size="16" fill="#f5b5b5">え</text>
    <circle cx="170" cy="220" r="17" fill="none" stroke="#f5b5b5" stroke-width="2"/>
    <text x="170" y="226" text-anchor="middle" font-size="16" fill="#f5b5b5">あ</text>
    <circle cx="270" cy="70" r="17" fill="none" stroke="#f5b5b5" stroke-width="2"/>
    <text x="270" y="76" text-anchor="middle" font-size="16" fill="#f5b5b5">う</text>
    <circle cx="280" cy="140" r="17" fill="none" stroke="#f5b5b5" stroke-width="2"/>
    <text x="280" y="146" text-anchor="middle" font-size="16" fill="#f5b5b5">お</text>
    <circle cx="70" cy="95" r="15" fill="#e11d48" opacity="0.0"/>
    <circle cx="48" cy="40" r="13" fill="#e11d48"/>
    <text x="48" y="46" text-anchor="middle" font-size="15" font-weight="800" fill="#fff">ㅣ</text>
    <circle cx="85" cy="150" r="13" fill="#e11d48"/>
    <text x="85" y="156" text-anchor="middle" font-size="15" font-weight="800" fill="#fff">ㅔ</text>
    <circle cx="150" cy="240" r="13" fill="#e11d48"/>
    <text x="150" y="246" text-anchor="middle" font-size="15" font-weight="800" fill="#fff">ㅏ</text>
    <circle cx="350" cy="45" r="15" fill="#e11d48" stroke="#ffd166" stroke-width="3"/>
    <text x="350" y="51" text-anchor="middle" font-size="15" font-weight="800" fill="#fff">ㅜ</text>
    <circle cx="335" cy="120" r="15" fill="#e11d48" stroke="#ffd166" stroke-width="3"/>
    <text x="335" y="126" text-anchor="middle" font-size="15" font-weight="800" fill="#fff">ㅗ</text>
    <circle cx="300" cy="195" r="13" fill="#b91c1c"/>
    <text x="300" y="201" text-anchor="middle" font-size="15" font-weight="800" fill="#fff">ㅓ</text>
    <circle cx="238" cy="42" r="13" fill="#b91c1c"/>
    <text x="238" y="48" text-anchor="middle" font-size="15" font-weight="800" fill="#fff">ㅡ</text>
    </svg>
    """)
    st.caption("● 빨간 원 = 한국어 모음 / ○ 테두리 = 일본어 모음 / 노란 테두리 = 입술을 둥글게(원순). 우(う)는 한국어 ㅡ 쪽에 더 가까워요!")


def viz_lips():
    html("""
    <svg viewBox="0 0 500 120" style="width:100%;height:auto">
    <rect width="500" height="120" rx="14" fill="#1c070c"/>
    <ellipse cx="50" cy="55" rx="14" ry="14" fill="#7f1d1d" stroke="#ff6b6b" stroke-width="3"/>
    <text x="50" y="105" text-anchor="middle" font-size="14" fill="#ffd0d0">ㅜ 작고 둥글게</text>
    <ellipse cx="150" cy="55" rx="26" ry="6" fill="#7f1d1d" stroke="#f5b5b5" stroke-width="3"/>
    <text x="150" y="105" text-anchor="middle" font-size="14" fill="#ffd0d0">う 납작·둥글지 않음</text>
    <ellipse cx="250" cy="55" rx="19" ry="17" fill="#7f1d1d" stroke="#ff6b6b" stroke-width="3"/>
    <text x="250" y="105" text-anchor="middle" font-size="14" fill="#ffd0d0">ㅗ 둥글고 큼</text>
    <ellipse cx="350" cy="55" rx="26" ry="18" fill="#7f1d1d" stroke="#ff6b6b" stroke-width="3"/>
    <text x="350" y="105" text-anchor="middle" font-size="14" fill="#ffd0d0">ㅓ 둥글지 않고 크게</text>
    <ellipse cx="450" cy="55" rx="30" ry="5" fill="#7f1d1d" stroke="#ff6b6b" stroke-width="3"/>
    <text x="450" y="105" text-anchor="middle" font-size="14" fill="#ffd0d0">ㅡ 옆으로 납작</text>
    </svg>
    """)


# ----- 5-7. 일본어 트랙: 받침 (박자 + 노래방 + 혀 단면도) -----
def viz_final_consonants():
    cols = st.columns(3)
    items = [
        ("flat", "ㅁ 받침 (밤)", "입술을 닫아요", None, True),
        ("lateral", "ㄴ 받침 (반)", "혀끝이 윗잇몸에 붙어요", (76, 62), False),
        ("velar", "ㅇ 받침 (방)", "혀뿌리가 올라가요", (220, 46), False),
    ]
    for col, (key, cap, note, touch, lips) in zip(cols, items):
        with col:
            html(tongue_svg(key, cap, note, touch, lips))

    st.markdown("**한 박자 비교**")
    html("""
    <div>
    <div style="margin:6px 0"><span class="note">일본어 ばん (2박)</span><br>
    <span class="beat">ば</span><span class="beat">ん</span></div>
    <div style="margin:6px 0"><span class="note">한국어 반 (1박, 받침은 짧게 닫기만)</span><br>
    <span class="beat k">반</span></div>
    </div>
    """)
    st.markdown("**노래방 가사처럼 따라 읽기** (한 글자 = 한 박자, 1초씩)")
    html("""
    <div>
    <div class="karaoke">밤<span style="animation-delay:0s">밤</span></div>
    <div class="karaoke">반<span style="animation-delay:1s">반</span></div>
    <div class="karaoke">방<span style="animation-delay:2s">방</span></div>
    </div>
    """)
    st.caption("글자 색이 차오르는 속도에 맞춰 읽어 보세요. 받침 때문에 길어지면 안 돼요!")


VISUALS = {
    "rl": viz_rl,
    "ecg": lambda: (viz_ecg(), viz_e_table()),
    "syllable": viz_syllables,
    "tissue": viz_tissue,
    "vowel": lambda: (viz_vowel_map(), viz_lips()),
    "final": viz_final_consonants,
}


# ------------------------------------------------------------
# 6. 학습 내용 데이터
#    items : 연습 단어 (target=정답, conf=헷갈리는 단어, hint=힌트)
#    quiz  : 퀴즈 (q, options, answer, why, speak=듣고 고르기용)
# ------------------------------------------------------------
TRACKS = {
    "영어": {
        "label": "영어 (한국어 모국어 화자용)",
        "lang": "en-US",
        "lessons": [
            {
                "short": "r / l",
                "title": "자음 r / l",
                "visual": "rl",
                "concept": """
### 🎯 핵심 문제
한국어의 ㄹ은 하나의 소리 같지만, 실제로는 **두 가지로 소리 나요.**

- **초성·모음 사이 ㄹ** (오리, 나라): 혀끝이 윗잇몸을 **톡 한 번 치고** 내려오는 **탄설음**
- **종성(받침) ㄹ** (달, 물): 혀끝을 윗잇몸에 **붙인 채** 공기가 혀 양옆으로 흐르는 **설측음**

영어 **l은 한국어 받침 ㄹ과 같은 자세**예요. 이미 가진 소리를 단어 맨 앞에서도 만들면 돼요!
영어 **r은 한국어에 없는 소리**예요. 혀끝이 **어디에도 닿지 않고** 뒤로 말리며 입술이 살짝 둥글어져요.

### 🛠️ 연습 요령
- **l** : "달"의 받침 ㄹ 자세를 먼저 만들고 시작 → "을~라이트" (light)
- **r** : 입술을 "우" 모양으로 모으고 혀를 뒤로 → "우~라이트" (right)
- **혀끝이 닿으면 l, 닿지 않으면 r**
""",
                "items": [
                    {"target": "light", "conf": "right", "hint": "혀끝을 윗잇몸에 붙이고 '을~' 하며 시작"},
                    {"target": "right", "conf": "light", "hint": "입술을 둥글게, 혀끝은 아무 데도 닿지 않게"},
                    {"target": "lock", "conf": "rock", "hint": "l: 혀끝을 붙였다가 떼면서"},
                    {"target": "rock", "conf": "lock", "hint": "r: 혀를 뒤로 당기기"},
                ],
                "quiz": [
                    {"q": "한국어 '오리'의 ㄹ처럼 혀끝으로 톡 치는 소리를 무엇이라 할까요?",
                     "options": ["탄설음", "설측음", "비음", "마찰음"], "answer": "탄설음",
                     "why": "혀끝이 윗잇몸을 한 번 톡 치는 소리예요."},
                    {"q": "영어 /l/을 낼 때 혀끝의 위치는?",
                     "options": ["윗잇몸에 붙인 채 공기는 옆으로", "어디에도 닿지 않고 뒤로 말기",
                                 "윗니와 아랫니 사이에 끼우기", "아랫니 뒤에 붙이기"],
                     "answer": "윗잇몸에 붙인 채 공기는 옆으로",
                     "why": "한국어 받침 ㄹ(달)과 같은 자세예요."},
                    {"q": "소리를 듣고 알맞은 단어를 고르세요. (🔊 버튼을 누르세요)",
                     "options": ["right", "light"], "answer": "light", "speak": "light",
                     "why": "light는 혀끝이 윗잇몸에 붙어요."},
                    {"q": "영어 /r/의 특징으로 알맞은 것은?",
                     "options": ["혀끝이 어디에도 닿지 않는다", "혀끝으로 윗잇몸을 톡 친다",
                                 "혀끝을 윗니에 붙인다", "혀뿌리로 입천장을 막는다"],
                     "answer": "혀끝이 어디에도 닿지 않는다",
                     "why": "r은 혀끝이 떠 있는 소리예요."},
                ],
            },
            {
                "short": "i / e",
                "title": "모음 i / e",
                "visual": "ecg",
                "concept": """
### 🎯 핵심 문제
한국어는 ㅣ 하나로 두 소리를 모두 처리하기 쉬워요. 영어에는 **길이와 긴장도**가 다른 두 소리가 있어요.

- **eat /iː/** : 혀가 **가장 높고 앞**, 입꼬리를 옆으로, **길고 긴장**된 소리
- **it /ɪ/** : 혀가 **조금 낮고 이완**, 입이 조금 더 열림, **짧은** 소리 (한국어 ㅣ와 ㅔ의 중간 느낌)

### 🛠️ 연습 요령
1. 그래프에서 **빨간 선(혀)** 이 eat에서 더 높은지 확인
2. eat는 **길게 늘이고**, it는 **짧게 툭**
3. 철자 e는 단어마다 소리가 달라요 (표 참고)
""",
                "items": [
                    {"target": "seat", "conf": "sit", "hint": "길게 늘인 ㅣ, 입꼬리 옆으로"},
                    {"target": "sit", "conf": "seat", "hint": "짧고 힘을 뺀 소리"},
                    {"target": "sheep", "conf": "ship", "hint": "쉬~입 (길게)"},
                    {"target": "ship", "conf": "sheep", "hint": "쉽 (짧게)"},
                ],
                "quiz": [
                    {"q": "eat의 모음 /iː/는 it의 모음 /ɪ/보다 어떤가요?",
                     "options": ["길고 혀가 더 높다", "짧고 혀가 더 높다", "길고 혀가 더 낮다", "차이가 없다"],
                     "answer": "길고 혀가 더 높다", "why": "그래프에서 eat가 더 길고 더 높았죠!"},
                    {"q": "it의 모음 /ɪ/의 특징은?",
                     "options": ["짧고 이완된 소리", "길고 긴장된 소리", "입술을 둥글게 하는 소리", "소리가 나지 않는다"],
                     "answer": "짧고 이완된 소리", "why": "힘을 빼고 짧게 내요."},
                    {"q": "소리를 듣고 알맞은 단어를 고르세요. (🔊 버튼을 누르세요)",
                     "options": ["sheep", "ship"], "answer": "ship", "speak": "ship",
                     "why": "ship은 짧은 /ɪ/ 소리예요."},
                    {"q": "make의 마지막 e는 어떻게 소리 날까요?",
                     "options": ["소리 나지 않고 앞 모음을 길게 만든다", "강한 /iː/로 소리 난다",
                                 "/ɛ/로 소리 난다", "약한 '어'로 소리 난다"],
                     "answer": "소리 나지 않고 앞 모음을 길게 만든다", "why": "magic e라고도 불러요."},
                ],
            },
            {
                "short": "음절",
                "title": "음절 (모음 개수 = 음절 수)",
                "visual": "syllable",
                "concept": """
### 🎯 핵심 문제
한국어는 자음마다 모음(ㅡ)을 붙여서 발음하기 쉬워요. 그래서 **speak → "스피크"(3음절)** 가 돼요.
영어는 **발음되는 모음의 개수 = 음절 수**예요. speak는 모음이 ea 하나라서 **1음절**이고, 자음은 작고 빠르게 붙어요. (ㅅ피ㅋ)

### 🛠️ 연습 요령
1. **모음을 고정**하고 그 모음만 크게 발음 (그림의 빨간 큰 글자)
2. 자음 s, p, k는 **어디에 붙는지** 확인 (모음 앞? 뒤?)
3. 자음 뒤에 **"ㅡ"를 붙이지 않기**: 입 모양만 만들고 소리는 거의 내지 않기
""",
                "items": [
                    {"target": "speak", "conf": None, "hint": "sp + EE + k, 1음절!"},
                    {"target": "street", "conf": None, "hint": "str + EE + t, 1음절!"},
                    {"target": "strike", "conf": None, "hint": "str + I + k, 1음절! 끝의 e는 소리 없음"},
                    {"target": "desk", "conf": None, "hint": "d + E + sk, 1음절!"},
                ],
                "quiz": [
                    {"q": "street는 몇 음절일까요?",
                     "options": ["1", "2", "3", "4"], "answer": "1", "why": "모음 소리가 ee 하나뿐이에요."},
                    {"q": "desk의 올바른 발음 방식은?",
                     "options": ["모음 하나에 자음을 짧게 붙여 한 박자", "데-스-크 세 박자",
                                 "모든 글자에 ㅡ를 붙인다", "e를 발음하지 않는다"],
                     "answer": "모음 하나에 자음을 짧게 붙여 한 박자", "why": "영어는 모음이 박자를 만들어요."},
                    {"q": "영어에서 음절 수를 결정하는 것은?",
                     "options": ["발음되는 모음의 개수", "자음의 개수", "글자 수", "단어의 길이"],
                     "answer": "발음되는 모음의 개수", "why": "모음 개수 = 음절 수!"},
                    {"q": "ice cream은 영어에서 몇 음절일까요? (한국어 '아이스크림'은 5음절)",
                     "options": ["2", "3", "4", "5"], "answer": "2", "why": "ice(1) + cream(1)이에요."},
                ],
            },
        ],
        "final": {
            "mcq": [
                {"q": "소리를 듣고 알맞은 단어를 고르세요. (🔊 버튼을 누르세요)",
                 "options": ["right", "light"], "answer": "light", "speak": "light",
                 "why": "light는 혀끝이 윗잇몸에 붙어요."},
                {"q": "eat와 it의 차이로 맞는 것은?",
                 "options": ["eat는 길고 긴장, it는 짧고 이완", "eat는 짧고 이완, it는 길고 긴장",
                             "둘은 길이만 같고 혀 높이가 다르다", "둘은 완전히 같다"],
                 "answer": "eat는 길고 긴장, it는 짧고 이완", "why": "ECG 그래프를 떠올려 보세요."},
                {"q": "strike는 몇 음절일까요?",
                 "options": ["1", "2", "3", "5"], "answer": "1", "why": "모음 i 하나뿐이에요."},
            ],
            "speak": [
                {"target": "grass", "conf": "glass", "hint": "r: 혀끝을 띄우기"},
                {"target": "leave", "conf": "live", "hint": "l + 길고 높은 ㅣ"},
                {"target": "strike", "conf": None, "hint": "한 음절! 자음 뒤에 ㅡ 금지"},
            ],
        },
    },
    "일본어": {
        "label": "일본어 (일본어 모국어 화자용 · 한국어 발음)",
        "lang": "ko-KR",
        "lessons": [
            {
                "short": "평·격·경음",
                "title": "자음 평음 / 격음 / 경음 (平音・激音・濃音)",
                "visual": "tissue",
                "concept": """
### 🎯 핵심 문제
일본어는 か/が처럼 **성대가 떨리는지(유성·무성)** 로 자음을 구별해요.
한국어 가/카/까는 **성대 진동이 아니라 숨의 세기와 목의 긴장도**로 구별해요.

- **평음(예사소리)** ㄱ ㄷ ㅂ ㅈ : 숨과 힘이 **보통** → 가
- **격음(거센소리)** ㅋ ㅌ ㅍ ㅊ : 숨을 **강하게 터뜨림** → 카 (휴지가 크게 흔들려요)
- **경음(된소리)** ㄲ ㄸ ㅃ ㅉ : **목에 힘**을 주고 숨은 **거의 내지 않음** → 까 (휴지가 거의 안 흔들려요)

### 🛠️ 연습 요령
1. 휴지를 입 앞에 대고 **카 → 가 → 까** 순서로 흔들림 확인
2. 격음은 "하~" 하는 숨을 섞는 느낌, 경음은 소리를 **꾹 눌렀다 터뜨리는** 느낌
3. 짝으로 연습: 불 / 풀 / 뿔, 달 / 탈 / 딸
""",
                "items": [
                    {"target": "불", "conf": "풀", "hint": "평음: 숨 보통, 힘 보통"},
                    {"target": "풀", "conf": "뿔", "hint": "격음: 숨을 강하게 터뜨리기"},
                    {"target": "뿔", "conf": "불", "hint": "경음: 목에 힘, 숨은 거의 없이"},
                    {"target": "딸", "conf": "달", "hint": "경음: 꾹 눌렀다가 터뜨리기"},
                ],
                "quiz": [
                    {"q": "입 앞의 휴지가 가장 크게 흔들리는 소리는?",
                     "options": ["격음 (카)", "평음 (가)", "경음 (까)", "모두 같다"], "answer": "격음 (카)",
                     "why": "격음은 숨을 강하게 터뜨려요."},
                    {"q": "경음(ㄲ ㄸ ㅃ)을 낼 때의 느낌은?",
                     "options": ["목에 힘을 주고 숨은 거의 내지 않는다", "숨을 강하게 내뿜는다",
                                 "성대를 크게 떨게 한다", "입술을 둥글게 한다"],
                     "answer": "목에 힘을 주고 숨은 거의 내지 않는다", "why": "휴지가 거의 안 흔들려요."},
                    {"q": "소리를 듣고 알맞은 단어를 고르세요. (🔊 버튼을 누르세요)",
                     "options": ["불", "풀", "뿔"], "answer": "풀", "speak": "풀",
                     "why": "풀은 격음이라 숨이 강해요."},
                    {"q": "한국어 가/카/까를 구별하는 기준은?",
                     "options": ["숨의 세기와 목의 긴장도", "성대 진동의 유무", "입술 모양", "소리의 높낮이"],
                     "answer": "숨의 세기와 목의 긴장도", "why": "일본어의 유성·무성 구별과 달라요."},
                ],
            },
            {
                "short": "모음",
                "title": "모음 (원순 모음 ㅜ ㅗ / ㅓ ㅡ)",
                "visual": "vowel",
                "concept": """
### 🎯 핵심 문제
먼저 일본어와 **비슷해서 쉬운 모음**부터 시작해요: **ㅣ ㅔ ㅏ ㅜ ㅗ**.
하지만 비슷해 보여도 다른 점이 있어요.

- **ㅜ / ㅗ** : 입술을 **둥글게 앞으로 내밀어요(원순)**. 일본어 う(u)는 입술을 거의 둥글게 하지 않아요.
- **ㅡ** : 입술을 둥글게 하지 않고 **옆으로 납작하게**. 오히려 일본어 う에 가까워요.
- **ㅓ** : 일본어에 없는 소리. 입을 **크게 벌리고 둥글게 하지 않아요**.

### 🛠️ 연습 요령
1. 모음 지도에서 **빨간 원(한국어)과 테두리(일본어)의 위치 차이** 확인
2. 거울을 보며 **입술 모양** 비교: 우(ㅜ)는 **작은 동그라미**
3. ㅗ → ㅓ 로 바꿀 때 **입술 둥글기를 풀면서** 턱을 내리기
""",
                "items": [
                    {"target": "어머니", "conf": "오머니", "hint": "어: 입술 둥글지 않게, 크게"},
                    {"target": "오리", "conf": "어리", "hint": "오: 입술을 둥글게"},
                    {"target": "그림", "conf": "구림", "hint": "으: 입술 납작하게"},
                    {"target": "구름", "conf": "그름", "hint": "우: 입술을 작게 모아 앞으로"},
                ],
                "quiz": [
                    {"q": "한국어 ㅜ를 낼 때 입술 모양은?",
                     "options": ["둥글게 앞으로 내민다", "옆으로 납작하게 한다", "크게 벌린다", "움직이지 않는다"],
                     "answer": "둥글게 앞으로 내민다", "why": "일본어 う는 입술을 거의 내밀지 않아요."},
                    {"q": "한국어 ㅡ는 입술이 어떤가요?",
                     "options": ["둥글지 않고 옆으로 납작", "작고 둥글게", "크게 둥글게", "앞으로 내밈"],
                     "answer": "둥글지 않고 옆으로 납작", "why": "일본어 う와 가까워요."},
                    {"q": "소리를 듣고 알맞은 단어를 고르세요. (🔊 버튼을 누르세요)",
                     "options": ["구름", "거름", "고름"], "answer": "구름", "speak": "구름",
                     "why": "구름의 첫 모음은 둥근 ㅜ예요."},
                    {"q": "일본어 화자가 먼저 익히기 쉬운 공통 모음은?",
                     "options": ["ㅣ ㅔ ㅏ ㅜ ㅗ", "ㅓ ㅡ ㅐ ㅟ ㅢ", "ㅑ ㅕ ㅛ ㅠ ㅖ", "ㅘ ㅝ ㅙ ㅞ ㅚ"],
                     "answer": "ㅣ ㅔ ㅏ ㅜ ㅗ", "why": "쉬운 것부터, 그다음에 ㅓ·ㅡ!"},
                ],
            },
            {
                "short": "받침 ㄴㅁㅇ",
                "title": "음절 (받침 비음 ㄴ ㅁ ㅇ)",
                "visual": "final",
                "concept": """
### 🎯 핵심 문제
일본어 ん(ん)은 **독립된 한 박자**라서, 한국어 받침을 **길게 늘이기 쉬워요.** (반 → "바안")
한국어 받침은 **한 글자 안에서 짧게 닫는 것**이에요. **한 글자 = 한 박자!**

받침 비음 3가지는 **닫는 위치**가 달라요.
- **ㅁ** (밤) : **입술**을 닫아요
- **ㄴ** (반) : **혀끝**이 윗잇몸에 붙어요
- **ㅇ** (방) : **혀뿌리**가 올라가 입천장 뒤쪽에 닿아요

### 🛠️ 연습 요령
1. **받침만 먼저** 연습: 음(ㅁ) → 은(ㄴ) → 응(ㅇ), 닫는 위치 느끼기
2. 받침이 있는 글자로 확장: 밤 / 반 / 방
3. **노래방 가사**처럼 한 박자에 맞춰 읽기 (길게 늘이지 않기)
""",
                "items": [
                    {"target": "밤", "conf": "반", "hint": "끝에서 입술을 닫고 멈추기"},
                    {"target": "반", "conf": "방", "hint": "끝에서 혀끝을 윗잇몸에"},
                    {"target": "방", "conf": "밤", "hint": "끝에서 혀뿌리를 올리기"},
                    {"target": "한국", "conf": None, "hint": "한(ㄴ)과 국(ㄱ)을 각각 한 박자로"},
                ],
                "quiz": [
                    {"q": "한국어 반(班)은 몇 박자로 읽을까요?",
                     "options": ["1박자", "2박자", "3박자", "받침만 따로 1박자"], "answer": "1박자",
                     "why": "받침은 한 글자 안에서 짧게 닫아요."},
                    {"q": "ㅁ 받침(밤)에서 닫는 곳은?",
                     "options": ["입술", "혀끝과 윗잇몸", "혀뿌리와 입천장", "목구멍"], "answer": "입술",
                     "why": "ㅁ은 입술을 닫는 소리예요."},
                    {"q": "소리를 듣고 알맞은 단어를 고르세요. (🔊 버튼을 누르세요)",
                     "options": ["밤", "반", "방"], "answer": "방", "speak": "방",
                     "why": "방은 혀뿌리가 올라가는 ㅇ 받침이에요."},
                    {"q": "ㅇ 받침을 낼 때 닫는 곳은?",
                     "options": ["혀뿌리와 입천장 뒤쪽", "입술", "혀끝과 윗잇몸", "윗니와 아랫입술"],
                     "answer": "혀뿌리와 입천장 뒤쪽", "why": "ㅇ은 입 안쪽 깊은 곳에서 막아요."},
                ],
            },
        ],
        "final": {
            "mcq": [
                {"q": "소리를 듣고 알맞은 단어를 고르세요. (🔊 버튼을 누르세요)",
                 "options": ["불", "풀", "뿔"], "answer": "풀", "speak": "풀",
                 "why": "풀은 숨이 강한 격음이에요."},
                {"q": "한국어 ㅡ와 ㅜ의 차이로 맞는 것은?",
                 "options": ["ㅜ는 입술을 둥글게, ㅡ는 납작하게", "ㅜ는 납작하게, ㅡ는 둥글게",
                             "둘 다 입술을 둥글게", "둘 다 같은 소리"],
                 "answer": "ㅜ는 입술을 둥글게, ㅡ는 납작하게", "why": "모음 지도와 입술 그림을 떠올려 보세요."},
                {"q": "받침이 있는 글자(예: 반)는 몇 박자일까요?",
                 "options": ["1박자", "2박자", "3박자", "4박자"], "answer": "1박자",
                 "why": "한 글자 = 한 박자예요."},
            ],
            "speak": [
                {"target": "딸", "conf": "탈", "hint": "경음: 꾹 눌렀다 터뜨리기"},
                {"target": "그림", "conf": "구림", "hint": "으: 입술 납작하게"},
                {"target": "방", "conf": "밤", "hint": "받침 ㅇ: 혀뿌리 올리기"},
            ],
        },
    },
}

PASS_PRACTICE = 60   # 연습 평균 합격 점수
PASS_QUIZ = 75       # 퀴즈 합격 점수(%)
PASS_FINAL = 70      # 최종 테스트 합격 점수
SELF_LEVELS = {"어려웠어요": 30, "괜찮아요": 60, "좋아요": 80, "아주 좋아요": 100}


# ------------------------------------------------------------
# 7. session_state 초기화 (앱이 기억해야 하는 값들)
# ------------------------------------------------------------
def init_state():
    if "progress" not in st.session_state:
        st.session_state.progress = {name: [False] * 7 for name in TRACKS}
    if "stage_scores" not in st.session_state:
        st.session_state.stage_scores = {name: [None] * 7 for name in TRACKS}
    for key in ["best", "attempts", "seen", "quiz_result", "quiz_attempt"]:
        if key not in st.session_state:
            st.session_state[key] = {}
    if "page" not in st.session_state:
        st.session_state.page = 0


init_state()

# 다른 곳에서 "이 페이지로 이동" 요청이 있으면 사이드바가 만들어지기 전에 처리
if "goto" in st.session_state:
    st.session_state.page = st.session_state.pop("goto")


# ------------------------------------------------------------
# 8. 계산 도우미 함수들
# ------------------------------------------------------------
def stage_label(track, page):
    """page 번호(1~7)에 해당하는 단계 이름"""
    lessons = TRACKS[track]["lessons"]
    if page == 7:
        return "최종 확인 테스트"
    lesson = lessons[(page - 1) // 2]
    return f"{lesson['short']} " + ("개념·연습" if page % 2 == 1 else "퀴즈")


def star_labels(track):
    names = []
    for page in range(1, 8):
        if page == 7:
            names.append("최종")
        else:
            lesson = TRACKS[track]["lessons"][(page - 1) // 2]
            names.append(lesson["short"] + (" 연습" if page % 2 == 1 else " 퀴즈"))
    return names


def is_unlocked(track, star_index):
    return all(st.session_state.progress[track][:star_index])


def light_star(track, star_index, score, message):
    """별을 밝히고 점수를 기록한 뒤 화면을 새로고침한다."""
    st.session_state.progress[track][star_index] = True
    old = st.session_state.stage_scores[track][star_index]
    st.session_state.stage_scores[track][star_index] = max(old or 0, round(score))
    st.session_state.flash = {"msg": message, "balloons": star_index == 6}
    st.rerun()


def go_to(page):
    st.session_state.goto = page
    st.rerun()


def clean(text):
    """비교를 위해 공백·기호를 지우고 소문자로 바꾼다."""
    return re.sub(r"[^0-9a-z가-힣ぁ-んァ-ン一-龥]", "", text.lower())


def evaluate(alts, item):
    """음성 인식 결과(alts)를 정답과 비교해 (점수, 메시지)를 돌려준다."""
    if not alts:
        return 0, "소리를 인식하지 못했어요. 다시 말해 보세요."
    target = clean(item["target"])
    conf = clean(item.get("conf") or "")
    heard = alts[0].get("text", "")
    top = clean(heard)
    confidence = alts[0].get("conf") or 0.8
    others = [clean(a.get("text", "")) for a in alts[1:]]

    if top == target:
        return round(75 + 25 * confidence), f"✅ 정확해요! 「{heard}」"
    if target in others:
        return 60, f"🙂 거의 맞았어요. 1순위는 「{heard}」였고 정답도 후보에 있었어요."
    if conf and (top == conf or conf in others):
        return 25, f"⚠️ 「{heard}」(으)로 들렸어요. {item['conf']} 소리와 섞였어요! 힌트를 다시 읽어 보세요."
    similarity = difflib.SequenceMatcher(None, top, target).ratio()
    return round(similarity * 50), f"🔁 「{heard}」(으)로 들렸어요. 다시 도전해 보세요!"


# ------------------------------------------------------------
# 9. 연습 문항 하나를 그리는 함수 (듣기 + 말하기 + 점수)
# ------------------------------------------------------------
def practice_item(track, scope, idx, item):
    lang = TRACKS[track]["lang"]
    key = f"{track}|{scope}|{idx}"
    with st.container(border=True):
        left, right = st.columns([1, 2])
        with left:
            st.markdown(f'<div class="bigword">{item["target"]}</div>', unsafe_allow_html=True)
            st.caption("💡 " + item["hint"])
        with right:
            if st.session_state.get("self_mode"):
                # 마이크를 쓰지 않는 자가 평가 모드
                voice_box(target=item["target"], speak=item["target"], lang=lang,
                          mode="listen", key="voice_" + key, default=None)
                choice = st.radio("내 발음은?", list(SELF_LEVELS), horizontal=True, index=None,
                                  key="self_" + key)
                if st.button("점수 기록", key="selfbtn_" + key):
                    if choice is None:
                        st.warning("먼저 평가를 골라 주세요.")
                    else:
                        score = SELF_LEVELS[choice]
                        st.session_state.attempts[key] = {"score": score, "msg": f"📝 자가 평가: {choice}"}
                        st.session_state.best[key] = max(st.session_state.best.get(key, 0), score)
            else:
                res = voice_box(target=item["target"], speak=item["target"], lang=lang,
                                mode="both", key="voice_" + key, default=None)
                # 새로운 인식 결과가 왔을 때만 채점 (t = 시각 도장)
                if res and res.get("t") != st.session_state.seen.get(key):
                    st.session_state.seen[key] = res.get("t")
                    score, msg = evaluate(res.get("alts", []), item)
                    st.session_state.attempts[key] = {"score": score, "msg": msg}
                    st.session_state.best[key] = max(st.session_state.best.get(key, 0), score)

        attempt = st.session_state.attempts.get(key)
        if attempt:
            st.write(attempt["msg"] + f"  (이번 {attempt['score']}점)")
        if key in st.session_state.best:
            st.progress(st.session_state.best[key] / 100, text=f"최고 점수 {st.session_state.best[key]}점")


def practice_average(track, scope, count):
    """모든 문항을 시도했으면 평균 점수, 아니면 None"""
    scores = [st.session_state.best.get(f"{track}|{scope}|{i}") for i in range(count)]
    if any(s is None for s in scores):
        return None
    return sum(scores) / count


# ------------------------------------------------------------
# 10. 퀴즈를 그리는 함수들
# ------------------------------------------------------------
def render_questions(track, prefix, questions):
    """문제를 화면에 그리고, 선택한 답 목록과 채점 결과를 돌려준다."""
    lang = TRACKS[track]["lang"]
    attempt = st.session_state.quiz_attempt.get(prefix, 0)
    result = st.session_state.quiz_result.get(prefix)
    answers = []
    for i, q in enumerate(questions):
        with st.container(border=True):
            st.markdown(f"**Q{i + 1}. {q['q']}**")
            if q.get("speak"):
                voice_box(target=q["speak"], speak=q["speak"], lang=lang, mode="listen",
                          key=f"qv_{prefix}_{i}_{attempt}", default=None)
            answer = st.radio("보기", q["options"], index=None, key=f"q_{prefix}_{i}_{attempt}",
                              label_visibility="collapsed", disabled=result is not None)
            answers.append(answer)
            if result is not None:
                if result[i]:
                    st.success("정답! " + q["why"])
                else:
                    st.error(f"오답이에요. 정답: {q['answer']} — {q['why']}")
    return answers, result


def grade_button(prefix, questions, answers):
    if st.button("채점하기", type="primary", key=f"grade_{prefix}"):
        if any(a is None for a in answers):
            st.warning("모든 문제에 답해 주세요.")
        else:
            st.session_state.quiz_result[prefix] = [a == q["answer"] for a, q in zip(answers, questions)]
            st.rerun()


def retry_button(prefix):
    if st.button("🔄 다시 풀기", key=f"retry_{prefix}"):
        st.session_state.quiz_result.pop(prefix, None)
        st.session_state.quiz_attempt[prefix] = st.session_state.quiz_attempt.get(prefix, 0) + 1
        st.rerun()


# ------------------------------------------------------------
# 11. 단계별 화면
# ------------------------------------------------------------
def page_practice_stage(track, lesson_index, star_index):
    lesson = TRACKS[track]["lessons"][lesson_index]
    st.subheader(f"⭐ {star_index + 1}단계 · {lesson['title']}")

    view = st.radio("보기", ["📘 개념", "🎙️ 연습"], horizontal=True, label_visibility="collapsed",
                    key=f"view_{track}_{star_index}")
    if view == "📘 개념":
        st.markdown(lesson["concept"])
        VISUALS[lesson["visual"]]()
        st.info("개념을 읽었다면 위쪽의 **🎙️ 연습**을 눌러 보세요!")
        return

    st.caption("🔊 먼저 듣고, 🎤 말하기를 눌러 따라 말해 보세요. (Chrome/Edge 권장)")
    items = lesson["items"]
    scope = f"L{lesson_index}"
    for idx, item in enumerate(items):
        practice_item(track, scope, idx, item)

    avg = practice_average(track, scope, len(items))
    st.divider()
    if st.session_state.progress[track][star_index]:
        st.success("이미 밝힌 별이에요! 다음 단계로 가 볼까요?")
        if st.button("다음 단계로 ▶", key=f"next_{track}_{star_index}"):
            go_to(star_index + 2)
    elif avg is None:
        st.info("모든 단어를 한 번씩 말해 보면 별을 밝힐 수 있어요.")
    elif avg >= PASS_PRACTICE:
        st.success(f"평균 {avg:.0f}점! 합격이에요 🎉")
        if st.button("⭐ 별 밝히기", type="primary", key=f"light_{track}_{star_index}"):
            light_star(track, star_index, avg, f"⭐ {star_index + 1}번째 별이 밝아졌어요!")
    else:
        st.warning(f"평균 {avg:.0f}점이에요. {PASS_PRACTICE}점이 넘으면 별이 밝아져요. 점수가 낮은 단어를 다시 도전해 보세요!")


def page_quiz_stage(track, lesson_index, star_index):
    lesson = TRACKS[track]["lessons"][lesson_index]
    st.subheader(f"⭐ {star_index + 1}단계 · {lesson['short']} 학습 확인 퀴즈")
    prefix = f"{track}_quiz{lesson_index}"
    questions = lesson["quiz"]
    answers, result = render_questions(track, prefix, questions)

    if result is None:
        grade_button(prefix, questions, answers)
        return

    pct = sum(result) / len(result) * 100
    st.metric("퀴즈 점수", f"{pct:.0f}점")
    if st.session_state.progress[track][star_index]:
        st.success("이미 밝힌 별이에요!")
        if st.button("다음 단계로 ▶", key=f"next_{track}_{star_index}"):
            go_to(star_index + 2)
        retry_button(prefix)
    elif pct >= PASS_QUIZ:
        st.success("합격! 별을 밝혀요 🎉")
        if st.button("⭐ 별 밝히기", type="primary", key=f"light_{track}_{star_index}"):
            light_star(track, star_index, pct, f"⭐ {star_index + 1}번째 별이 밝아졌어요!")
    else:
        st.warning(f"{PASS_QUIZ}점 이상이면 합격이에요. 개념을 다시 보고 도전해 보세요!")
        retry_button(prefix)


def page_final(track):
    st.subheader("🌟 7단계 · 최종 확인 테스트")
    final = TRACKS[track]["final"]
    st.caption("객관식 3문제 + 말하기 3문제의 평균이 70점 이상이면 마지막 별이 밝아져요.")

    st.markdown("#### 파트 A · 객관식")
    prefix = f"{track}_final_mcq"
    answers, result = render_questions(track, prefix, final["mcq"])
    if result is None:
        grade_button(prefix, final["mcq"], answers)

    st.markdown("#### 파트 B · 말하기")
    for idx, item in enumerate(final["speak"]):
        practice_item(track, "final", idx, item)

    st.divider()
    speak_scores = [st.session_state.best.get(f"{track}|final|{i}") for i in range(len(final["speak"]))]
    if result is None or any(s is None for s in speak_scores):
        st.info("객관식을 채점하고, 말하기 3개를 모두 시도하면 최종 점수가 계산돼요.")
        return

    all_scores = [100 if r else 0 for r in result] + speak_scores
    total = sum(all_scores) / len(all_scores)
    st.metric("최종 점수", f"{total:.0f}점")
    if st.session_state.progress[track][6]:
        st.success("🌟 북두칠성을 모두 밝혔어요! 대단해요!")
    elif total >= PASS_FINAL:
        st.success("합격! 마지막 별을 밝혀요 🌟")
        if st.button("🌟 마지막 별 밝히기", type="primary", key="light_final"):
            light_star(track, 6, total, "🌟 북두칠성이 완성되었어요!")
    else:
        st.warning("아쉬워요. 약한 부분을 다시 연습하고 도전해 보세요!")
    if st.button("🔄 객관식 다시 풀기", key="retry_final"):
        st.session_state.quiz_result.pop(prefix, None)
        st.session_state.quiz_attempt[prefix] = st.session_state.quiz_attempt.get(prefix, 0) + 1
        st.rerun()


def page_home(track):
    st.subheader("🌌 북두칠성을 밝혀 보세요")
    done = st.session_state.progress[track]
    st.write(
        "별 7개는 **오류 3개 × (개념·연습 → 퀴즈)** 6단계와 **최종 테스트** 1단계예요. "
        "한 단계를 통과할 때마다 별이 하나씩 밝아져요."
    )
    nxt = next((i for i, d in enumerate(done) if not d), None)
    if nxt is None:
        st.success("모든 별이 밝았어요! 🌟")
    else:
        st.info(f"다음 도전: **{stage_label(track, nxt + 1)}**")
        if st.button("지금 도전하기 ▶", type="primary"):
            go_to(nxt + 1)
    st.markdown(
        """
**사용 팁**
- Chrome 또는 Edge에서 열고, 마이크 권한을 허용해 주세요.
- 마이크가 안 되면 왼쪽 사이드바에서 **자가 평가 모드**를 켜세요.
"""
    )


# ------------------------------------------------------------
# 12. 사이드바 (언어 선택, 메뉴, 점수)
# ------------------------------------------------------------
with st.sidebar:
    st.title("🌌 language app")
    track = st.selectbox("학습 트랙", list(TRACKS), format_func=lambda t: TRACKS[t]["label"], key="track")

    def page_name(p):
        if p == 0:
            return "🌌 북두칠성 (홈)"
        star = p - 1
        if st.session_state.progress[track][star]:
            mark = "✅"
        elif is_unlocked(track, star):
            mark = "⭐"
        else:
            mark = "🔒"
        return f"{mark} {p}. {stage_label(track, p)}"

    st.radio("메뉴", list(range(8)), format_func=page_name, key="page")
    st.toggle("🎙️ 마이크 없이 연습 (자가 평가)", key="self_mode")
    st.divider()

    all_scores = [s for name in TRACKS for s in st.session_state.stage_scores[name] if s is not None]
    st.metric("⭐ 학습 점수", f"{sum(all_scores)}점")
    st.metric("밝힌 별 (현재 트랙)", f"{sum(st.session_state.progress[track])} / 7")

    if st.button("현재 트랙 진행 초기화"):
        st.session_state.progress[track] = [False] * 7
        st.session_state.stage_scores[track] = [None] * 7
        for k in list(st.session_state.best):
            if k.startswith(track + "|"):
                del st.session_state.best[k]
        for k in list(st.session_state.attempts):
            if k.startswith(track + "|"):
                del st.session_state.attempts[k]
        for k in list(st.session_state.quiz_result):
            if k.startswith(track + "_"):
                del st.session_state.quiz_result[k]
        st.session_state.goto = 0
        st.rerun()


# ------------------------------------------------------------
# 13. 메인 화면
# ------------------------------------------------------------
flash = st.session_state.pop("flash", None)
if flash:
    st.toast(flash["msg"])
    if flash["balloons"]:
        st.balloons()

html(f"""
<div class="hero">
<h1>language app</h1>
<p>북두칠성을 모두 밝혀라 · 현재 트랙: <b>{TRACKS[track]['label']}</b></p>
</div>
""")

html(dipper_svg(st.session_state.progress[track], star_labels(track)))

page = st.session_state.page
if page == 0:
    page_home(track)
else:
    star_index = page - 1
    if not is_unlocked(track, star_index):
        st.warning("🔒 앞 단계의 별을 먼저 밝혀야 해요!")
        first_open = next(i for i, d in enumerate(st.session_state.progress[track]) if not d)
        if st.button("현재 단계로 이동 ▶"):
            go_to(first_open + 1)
    elif star_index == 6:
        page_final(track)
    elif star_index % 2 == 0:
        page_practice_stage(track, star_index // 2, star_index)
    else:
        page_quiz_stage(track, star_index // 2, star_index)
        