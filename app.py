# -*- coding: utf-8 -*-
# 길라잡이 발음 교정 앱 - ① 시작 화면 · 홈 · 북두칠성 구조
# 실행: 터미널에서  streamlit run app.py

import base64
import unicodedata
import io
import json
import math
import random
import struct
import time
import wave
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="길라잡이", page_icon="⭐", layout="wide",
                   initial_sidebar_state="collapsed")

# ------------------------------------------------------------------
# 1. 기본 설정값
# ------------------------------------------------------------------
BURGUNDY = "#7B1E2E"
NAVY = "#0B1535"
GOLD = "#FFD54A"

LANG_NAMES = {"en": "영어", "ko": "한국어"}
LANG_TITLES = {"en": "한국인을 위한 영어 발음 교실", "ko": "일본인을 위한 한국어 발음 교실"}

STEPS = {
    "en": ["자음 개념", "자음 연습", "모음 개념", "모음 연습",
           "음절 개념", "음절 연습", "최종 테스트"],
    "ko": ["자음 개념", "자음 연습", "모음 개념", "모음 연습",
           "음절 개념", "음절 연습", "최종 테스트"],
}

STAR_POS = [(50, 120), (150, 80), (250, 95), (350, 125), (450, 185), (550, 165), (650, 100)]
LINES = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 3)]


# ------------------------------------------------------------------
# 2. 사용자/기기별 세션 데이터 관리
# ------------------------------------------------------------------
def default_data():
    return {
        "done": {"en": [False] * 7, "ko": [False] * 7},
        "count": {"en": 0, "ko": 0},
        "last_lang": None,
        "last_step": None,
        "last_time": 0,
    }


ss = st.session_state
if "data" not in ss:
    ss.data = default_data()
    ss.screen = "start"
    ss.lang = "en"
    ss.step = None
    ss.resume = None
    d = ss.data
    if d.get("last_step") is not None and time.time() - d.get("last_time", 0) < 3600:
        ss.resume = (d["last_lang"], d["last_step"])


# ------------------------------------------------------------------
# 3. 화면 이동 네비게이션
# ------------------------------------------------------------------
ss.lc = 0


def touch():
    ss.data["last_time"] = time.time()


def go_start():
    ss.screen = "start"


def go_home():
    if ss.get("fp"):
        ss.fp = False
        ss.screen = "finale"
        return
    if ss.resume and ss.screen == "start":
        ss.lang = ss.resume[0]
    ss.screen = "home"
    touch()


def set_lang(lang):
    ss.lang = lang
    ss.resume = None


def open_step(i):
    ss.step = i
    ss.page, ss.pact, ss.pi, ss.ps, ss.rnd = 0, None, 0, {}, 0
    ss.t, ss.rv = None, False
    ss.resume = None
    ss.data["last_lang"] = ss.lang
    ss.data["last_step"] = i
    ss.screen = "step"
    touch()


def finish_step():
    lang, i = ss.lang, ss.step
    ss.data["done"][lang][i] = True
    if all(ss.data["done"][lang]):
        ss.data["count"][lang] += 1
        ss.data["done"][lang] = [False] * 7
        ss.data["last_step"] = None
        ss.screen = "finale"
    else:
        ss.screen = "stepend"
    if ss.get("rv") and ss.screen == "stepend":
        ss.step, ss.screen = 6, "step"
    touch()


def next_step():
    if ss.step < 6:
        open_step(ss.step + 1)
    else:
        go_home()


def other_language():
    ss.lang = "ko" if ss.lang == "en" else "en"
    ss.resume = None
    go_home()


# ------------------------------------------------------------------
# 4. 배경 및 UI 요소
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def sky_html():
    rnd = random.Random(7)
    parts = []
    for _ in range(45):
        x, y = rnd.uniform(0, 100), rnd.uniform(0, 100)
        size = rnd.choice([2, 2, 3, 4])
        delay = rnd.uniform(0, 4)
        color = rnd.choice(["#fff6c8", "#ffffff", "#ffe58a"])
        parts.append(
            f'<div class="tw" style="left:{x:.1f}%;top:{y:.1f}%;width:{size}px;'
            f'height:{size}px;background:{color};box-shadow:0 0 {size * 3}px {color};'
            f'animation-delay:{delay:.1f}s"></div>'
        )
    return "".join(parts)


def bear_svg(size=90):
    svg = (
        f'<svg width="{size}" height="{size}" viewBox="0 0 100 100">'
        '<ellipse cx="14" cy="55" rx="17" ry="9" fill="#fff" stroke="#7B1E2E" '
        'stroke-width="2" transform="rotate(-30 14 55)"/>'
        '<ellipse cx="86" cy="55" rx="17" ry="9" fill="#fff" stroke="#7B1E2E" '
        'stroke-width="2" transform="rotate(30 86 55)"/>'
        '<circle cx="30" cy="28" r="10" fill="#8d5a3b"/>'
        '<circle cx="70" cy="28" r="10" fill="#8d5a3b"/>'
        '<circle cx="50" cy="55" r="30" fill="#a8704a"/>'
        '<ellipse cx="50" cy="66" rx="12" ry="9" fill="#f1d3b3"/>'
        '<circle cx="40" cy="50" r="3.5" fill="#222"/>'
        '<circle cx="60" cy="50" r="3.5" fill="#222"/>'
        '<ellipse cx="50" cy="62" rx="4" ry="3" fill="#222"/></svg>'
    )
    return f'<div class="float" style="text-align:center">{svg}</div>'


def dipper_html(done, blink=None, all_lit=False, dark=False):
    line_off = "#3a4470" if dark else "#e6d6d9"
    line_on = GOLD if dark else "#e0b84a"
    star_off = "#8b93b8" if dark else "#c9b8bc"
    parts = ['<svg viewBox="0 0 700 260" width="100%" style="max-height:34vh">']
    for a, b in LINES:
        lit = all_lit or (done[a] and done[b])
        (x1, y1), (x2, y2) = STAR_POS[a], STAR_POS[b]
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                     f'stroke="{line_on if lit else line_off}" stroke-width="3"/>')
    for i, (x, y) in enumerate(STAR_POS):
        lit = all_lit or done[i]
        cls = "glow" if lit else ""
        if blink == i:
            cls += " blink"
        parts.append(
            f'<text x="{x}" y="{y + 18}" text-anchor="middle" font-size="56" '
            f'class="{cls}" fill="{GOLD if lit else star_off}">★</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def inject_css(dark):
    bg = NAVY if dark else "#FFFFFF"
    text = "#FFFFFF" if dark else "#2b2b2b"
    css = f"""
    <style>
    header, footer, #MainMenu {{visibility:hidden; height:0;}}
    .stApp {{background:{bg};}}
    .block-container {{padding-top:1rem; padding-bottom:0.5rem; max-width:1100px;
                       position:relative; z-index:2;}}
    h1,h2,h3,p,span,div,label {{color:{text};}}
    .stButton>button {{background:{BURGUNDY}; color:#fff !important; border:none;
                       border-radius:12px; padding:0.6rem 1rem; font-weight:600; width:100%;
                       white-space: normal !important; height: auto !important; min-height: 52px;
                       word-break: break-word !important; line-height: 1.35;}}
    .stButton>button:hover {{background:#9a2a3d; color:#fff;}}
    .stButton>button p {{color:#fff !important; white-space: normal !important; margin: 0;}}
    .tw {{position:fixed; border-radius:50%; z-index:1; pointer-events:none;
          animation:tw 3s ease-in-out infinite;}}
    @keyframes tw {{0%,100%{{opacity:.25}} 50%{{opacity:1}}}}
    .float {{animation:fl 3s ease-in-out infinite;}}
    @keyframes fl {{0%,100%{{transform:translateY(0)}} 50%{{transform:translateY(-8px)}}}}
    .glow {{filter:drop-shadow(0 0 8px #ffd54a) drop-shadow(0 0 16px #ffd54a);}}
    .blink {{animation:bl 0.8s ease-in-out infinite;}}
    @keyframes bl {{0%,100%{{opacity:.3}} 50%{{opacity:1}}}}
    .bubble {{background:#fdf0f2; border:2px solid {BURGUNDY}; border-radius:16px;
              padding:0.6rem 1rem; color:{BURGUNDY} !important; font-weight:700;}}
    .center {{text-align:center;}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    if dark:
        st.markdown(sky_html(), unsafe_allow_html=True)


def debug_box():
    """주소 끝에 ?debug=1 을 붙여 열면, 서버가 녹음 파일을 찾았는지 보여 줘요."""
    if "debug" not in st.query_params:
        return
    idx = audio_index()
    st.info("녹음 파일 인식: **%d개** · 이.mp3 %s · 폴더 확인: %s" % (
        len(idx), "있음" if "이" in idx else "없음",
        " / ".join(f"{d.parent.name}/{d.name}={'있음' if d.exists() else '없음'}" for d in AUDIO_DIRS)))
    st.caption("앱 위치: " + str(Path(__file__).parent))


def nav_row(left=None, mid=None, right=None):
    """버튼 한 줄: 왼쪽/가운데/오른쪽 칸에 하나씩 놓아요. 각 값은 (글자, 함수, args, key)"""
    cols = st.columns([2, 3, 2])
    for col, spec in zip(cols, (left, mid, right)):
        if spec:
            label, fn, args, key = spec
            col.button(label, on_click=fn, args=args, key=key, width="stretch")


def top_bar(title=""):
    c1, c2 = st.columns([1, 5])
    c1.button("🏠 홈으로", on_click=go_home, key="home_btn")
    if title:
        c2.markdown(f"<h3 style='margin:0.3rem 0'>{title}</h3>", unsafe_allow_html=True)


# ------------------------------------------------------------------
# 5. 주요 화면 렌더링
# ------------------------------------------------------------------
def screen_start():
    debug_box()
    inject_css(dark=True)
    st.markdown("<div style='height:9vh'></div>", unsafe_allow_html=True)
    st.markdown(bear_svg(120), unsafe_allow_html=True)
    st.markdown(
        "<h1 class='center' style='font-size:2.6rem;margin:0.3rem 0'>✦ 한민고등학교 길라잡이 ✦</h1>"
        "<p class='center' style='font-size:1.2rem;color:#ffe58a'>"
        "북두칠성을 따라가는 발음 교정 여행</p>",
        unsafe_allow_html=True,
    )
    st.markdown(dipper_html([False] * 7, dark=True), unsafe_allow_html=True)
    
    st.markdown("<div style='height:2vh'></div>", unsafe_allow_html=True)
    nav_row(mid=("별 따라 시작하기", go_home, (), "start_btn"))


def screen_home():
    debug_box()
    inject_css(dark=False)
    d = ss.data
    lang = ss.lang

    c1, c2, c3 = st.columns([3, 3, 3])
    c1.markdown(f"<h2 style='margin:0;color:{BURGUNDY}'>한민고 길라잡이</h2>"
                f"<span>{LANG_TITLES[lang]}</span>", unsafe_allow_html=True)
    if d["count"]["en"] + d["count"]["ko"] > 0:
        c2.markdown(
            f"<div class='bubble center'>이수 횟수 · 영어 {d['count']['en']}회 · "
            f"한국어 {d['count']['ko']}회</div>", unsafe_allow_html=True)
    other = "ko" if lang == "en" else "en"
    c3.button(f"{LANG_NAMES[other]} 학습으로 이동", on_click=set_lang, args=(other,),
              key="lang_btn")

    blink = None
    if ss.resume and ss.resume[0] == lang:
        blink = ss.resume[1]
        b1, b2 = st.columns([1, 6])
        b1.markdown(bear_svg(70), unsafe_allow_html=True)
        b2.markdown("<div class='bubble' style='margin-top:1rem'>"
                    "종료한 시점의 단계입니다!</div>", unsafe_allow_html=True)
    else:
        st.markdown(bear_svg(70), unsafe_allow_html=True)

    st.markdown(dipper_html(d["done"][lang], blink=blink), unsafe_allow_html=True)
    cols = st.columns(7)
    for i, col in enumerate(cols):
        col.button(f"{i + 1}. {STEPS[lang][i]}", on_click=open_step, args=(i,),
                   key=f"star_{i}")
    st.markdown("<p class='center' style='margin-top:0.6rem'>"
                "별 아래 단계를 눌러 원하는 순서로 학습해요.</p>", unsafe_allow_html=True)


def screen_step():
    inject_css(dark=False)
    lang, i = ss.lang, ss.step
    ended = (i in (1, 3, 5) and ss.pact is not None and ss.pi >= len(ss.pact)) or \
            (i == 6 and ss.get("t") is not None and ss.t["ph"] in ("res", "rev"))
    if not ended:
        top_bar(f"단계 {i + 1} · {STEPS[lang][i]}")
    if i <= 5:
        (render_en if lang == "en" else render_ko)(i)
        return
    render_test()
    return


def screen_stepend():
    inject_css(dark=False)
    lang = ss.lang
    st.markdown(bear_svg(100), unsafe_allow_html=True)
    st.markdown("<h2 class='center' style='color:%s'>별이 하나 빛났어요! ✨</h2>" % BURGUNDY,
                unsafe_allow_html=True)
    st.markdown(dipper_html(ss.data["done"][lang]), unsafe_allow_html=True)
    
    nav_row(left=("🏠 홈으로 돌아가기", go_home, (), "se_home"),
            right=("학습 계속하기 ➔", next_step, (), "se_next"))


def screen_finale():
    inject_css(dark=True)
    st.markdown("<h1 class='center' style='margin-top:2vh'>모든 별이 빛났어요! 🎉</h1>"
                "<p class='center' style='color:#ffe58a'>북두칠성이 완성됐어요. 정말 수고했어요!</p>",
                unsafe_allow_html=True)
    st.markdown(bear_svg(90), unsafe_allow_html=True)
    st.markdown(dipper_html([True] * 7, all_lit=True, dark=True), unsafe_allow_html=True)
    st.markdown("<div style='height:4vh'></div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.button("시작 화면으로", on_click=go_start, key="fin_start")
    with c2:
        st.button("다른 언어 학습", on_click=other_language, key="fin_other")


# ------------------------------------------------------------------
# 6. 오디오 및 텍스트 툴 (MP3 우선 재생 및 TTS 폴백 적용)
# ------------------------------------------------------------------
AUDIO_DIRS = [
    Path(__file__).parent,
    Path(__file__).parent / "static" / "audio",
    Path(__file__).parent / "audio"
]
MIMES = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4", ".ogg": "audio/ogg"}


@st.cache_resource(show_spinner=False, ttl=30)
def audio_index():
    idx = {}
    for d in AUDIO_DIRS:
        if d.exists():
            for f in d.iterdir():
                if f.suffix.lower() in MIMES:
                    idx.setdefault(unicodedata.normalize("NFC", f.stem), f)
    return idx


@st.cache_data(show_spinner=False, ttl=60)
def audio_bytes(w):
    f = audio_index().get(unicodedata.normalize("NFC", w))
    return (f.read_bytes(), MIMES[f.suffix.lower()]) if f else (None, None)


SAY_AS = {"lice": "head lice"}


@st.cache_data(show_spinner=False, ttl=60)
def audio_uri(w):
    data, mime = audio_bytes(w)
    return f"data:{mime};base64," + base64.b64encode(data).decode() if data else ""


def listen(words, lang="en-US", hide=False):
    """단어마다 같은 모양의 소리 버튼을 옆으로 이어서 보여 줘요.
    static/audio 폴더에 MP3 파일이 있는 경우 MP3를 우선 재생하고, 없으면 브라우저 TTS를 사용합니다."""
    btns = "".join(
        f'<button data-t="{SAY_AS.get(w, w)}" data-a="{audio_uri(w)}" onclick="s(this)">🔊 {"소리 듣기" if hide else w}</button>'
        for w in words)
    
    # 수정된 JavaScript: data-a(MP3 base64)가 존재하면 MP3를 우선 재생, 없거나 실패 시 TTS 작동
    script = (
        "function s(b){"
        "  speechSynthesis.cancel();"
        "  var a = b.dataset.a;"
        "  if(a && a.length > 20){"
        "    var audio = new Audio(a);"
        "    audio.play().catch(function(e){"
        "      console.log('MP3 재생 실패, TTS로 전환:', e);"
        "      fallbackTTS(b);"
        "    });"
        "    return;"
        "  }"
        "  fallbackTTS(b);"
        "}"
        "function fallbackTTS(b){"
        "  var u = new SpeechSynthesisUtterance(b.dataset.t);"
        "  u.lang = '" + lang + "';"
        "  u.rate = 0.7;"
        "  var v = speechSynthesis.getVoices().filter(function(x){"
        "    return x.lang.replace('_','-').indexOf('" + lang[:2] + "') == 0;"
        "  });"
        "  if(v.length) u.voice = v[0];"
        "  speechSynthesis.speak(u);"
        "}"
    )
    
    doc = ("<style>body{margin:0}button{background:#7B1E2E;color:#fff;border:0;border-radius:12px;padding:10px 16px;"
           "margin:4px 6px 4px 0;font-size:16px;font-weight:600;white-space:nowrap;cursor:pointer}"
           "button:hover{background:#9a2a3d}</style>" + btns + "<script>" + script + "</script>")
    h = 56 * max(1, -(-len(words) // 4)) + 4
    tries = []
    if hasattr(st, "iframe"):
        tries.append(lambda: st.iframe(doc, height=h))
    tries.append(lambda: __import__("streamlit.components.v1", fromlist=["html"]).html(doc, height=h))
    tries.append(lambda: st.html(doc, unsafe_allow_javascript=True))
    for t in tries:
        try:
            t()
            return
        except Exception as e:
            print("listen 실패:", repr(e))
    st.caption("🔇 이 환경에서는 소리 버튼을 쓸 수 없어요.")


@st.cache_data(show_spinner=False)
def _env(raw, n=40):
    try:
        w = wave.open(io.BytesIO(raw))
        ch, raw = w.getnchannels(), w.readframes(w.getnframes())
        x = [abs(v) for v in struct.unpack("<%dh" % (len(raw) // 2), raw)][::ch]
        size = max(1, len(x) // n)
        e = [sum(x[k * size:(k + 1) * size]) / size for k in range(n)]
        m = max(e) or 1
        return [v / m for v in e], len(x) / w.getframerate()
    except Exception:
        return None, 0


def envelope(audio, n=40):
    return _env(audio.getvalue(), n)


def bump(amp, length, n=40):
    L, s = int(n * length), (n - int(n * length)) // 2
    return [amp * math.sin(math.pi * (k - s) / L) if s <= k < s + L else 0 for k in range(n)]


def corr(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) or 1
    return num / den


def score_audio(audio, ref):
    e, sec = envelope(audio)
    if not e or sec < 0.5 or max(e) < 0.04:
        return 0, e
    raw_corr = corr(e, ref)
    score = int(max(0, raw_corr) * 100)
    if score < 40:
        score = int(score * 0.5)
    return score, e


def graph_svg(ref, usr):
    W = 560
    p = ['<svg viewBox="0 0 700 280" width="100%" style="max-height:40vh">']
    for k, (name, vals) in enumerate([("올바른 발음", ref), ("내 발음", usr)]):
        y0 = 72 + k * 135
        up = [(j * W / 39, y0 - v * 58) for j, v in enumerate(vals)]
        dn = [(x, 2 * y0 - y) for x, y in up]
        pts = lambda L: " ".join(f"{x:.0f},{y:.0f}" for x, y in L)
        ry = ";".join(f"{max(2, v * 58):.1f}" for v in vals)
        p.append(f'<clipPath id="c{k}"><rect x="0" y="0" width="0" height="280"><animate attributeName="width" '
                 f'from="0" to="{W + 4}" dur="2.4s" fill="freeze"/></rect></clipPath>')
        p.append(f'<text x="5" y="{y0 - 62}" font-size="14" fill="{BURGUNDY}">{name}</text>')
        p.append(f'<line x1="0" y1="{y0}" x2="{W}" y2="{y0}" stroke="#e5d5d8" stroke-dasharray="4 4"/>')
        p.append(f'<g clip-path="url(#c{k})"><polygon points="{pts(up + dn[::-1])}" fill="rgba(123,30,46,0.18)"/>'
                 f'<polyline points="{pts(up)}" fill="none" stroke="{BURGUNDY}" stroke-width="3"/>'
                 f'<polyline points="{pts(dn)}" fill="none" stroke="{BURGUNDY}" stroke-width="3"/></g>')
        p.append(f'<ellipse cx="635" cy="{y0}" rx="28" ry="2" fill="#f1d3b3" stroke="{BURGUNDY}" stroke-width="2">'
                 f'<animate attributeName="ry" values="{ry}" dur="2.4s" repeatCount="indefinite"/></ellipse>')
        p.append(f'<text x="635" y="{y0 + 78}" text-anchor="middle" font-size="12" fill="#666">입 모양</text>')
    p.append("</svg>")
    return "".join(p)


def sentence_intonation_svg():
    return '''
    <svg viewBox="0 0 700 160" width="100%" style="max-height:28vh; background:#fffafb; border:1px solid #ecd0d5; border-radius:12px; padding:10px;">
        <text x="20" y="25" font-size="14" font-weight="700" fill="#7B1E2E">📈 문장 억양 및 전체 발음 흐름 (Intonation Flow)</text>
        <line x1="20" y1="80" x2="680" y2="80" stroke="#e5d5d8" stroke-dasharray="4 4"/>
        <path d="M 30 110 Q 120 40 220 90 T 420 70 T 620 95" fill="none" stroke="#7B1E2E" stroke-width="3.5"/>
        <circle cx="120" cy="55" r="6" fill="#FFD54A" stroke="#7B1E2E" stroke-width="2"/>
        <circle cx="420" cy="70" r="6" fill="#FFD54A" stroke="#7B1E2E" stroke-width="2"/>
        <text x="100" y="35" font-size="11" fill="#5a1522" font-weight="600">상승 억양 (강세)</text>
        <text x="400" y="50" font-size="11" fill="#5a1522" font-weight="600">하강 억양 (안정)</text>
        <text x="350" y="145" text-anchor="middle" font-size="12" fill="#666">문장을 읽을 때 소리의 높낮이와 강세 흐름을 곡선으로 비교해요.</text>
    </svg>
    '''


def render_r_l_gif():
    gif_file = Path(__file__).parent / "KakaoTalk_20261105_101402840_02.gif"
    if gif_file.exists():
        st.image(str(gif_file), caption="⚡ /r/ 발음 조음 위치: 혀가 뒤쪽으로 말립니다.", use_container_width=True)
    else:
        st.markdown(tongue_svg("r") + tongue_svg("l"), unsafe_allow_html=True)
        st.caption("📁 'KakaoTalk_20261105_101402840_02.gif' 파일을 앱 파일과 같은 폴더에 넣어주세요.")


def tongue_svg(kind):
    tip = "M30 118 Q90 112 150 72 Q95 125 30 118" if kind == "l" else "M30 118 Q85 105 120 98 Q90 128 30 118"
    note = "혀끝이 윗잇몸에 닿아요" if kind == "l" else "혀끝이 닿지 않고 뒤로 말려요"
    return (f'<div style="display:inline-block;width:48%;text-align:center"><svg viewBox="0 0 200 140" width="100%">'
            '<path d="M20 40 Q100 5 180 40" fill="none" stroke="#999" stroke-width="3"/>'
            '<path d="M20 125 Q100 138 180 125" fill="none" stroke="#999" stroke-width="3"/>'
            f'<path d="{tip}" fill="#e88a8a" stroke="#7B1E2E" stroke-width="2"/></svg>'
            f'<b>{kind}</b><br>{note}</div>')


def stretch(word, v, sc):
    m = 0.28 * (sc - 1)
    return word.replace(v, f"<span style='display:inline-block;transform:scaleX({sc});margin:0 {m:.2f}em'>{v}</span>", 1)


def big(html, size=2.4):
    return f"<div class='center' style='font-size:{size}rem;font-weight:800;color:{BURGUNDY};word-break:break-word;'>{html}</div>"


def eat_it_svg():
    c = BURGUNDY
    return ('<svg viewBox="0 0 420 210" width="100%" style="max-height:32vh">'
            f'<text x="20" y="95" font-size="84" font-weight="800" fill="{c}" textLength="250" lengthAdjust="spacingAndGlyphs">eat</text>'
            f'<text x="305" y="95" font-size="84" font-weight="800" fill="{c}" textLength="85" lengthAdjust="spacingAndGlyphs">it</text>'
            f'<line x1="20" y1="125" x2="270" y2="125" stroke="{c}" stroke-width="6" stroke-linecap="round"/>'
            f'<line x1="305" y1="125" x2="390" y2="125" stroke="{c}" stroke-width="6" stroke-linecap="round"/>'
            '<text x="145" y="155" text-anchor="middle" font-size="16" fill="#444">길게 · /iː/ · 입을 작게</text>'
            '<text x="347" y="155" text-anchor="middle" font-size="16" fill="#444">짧게 · /ɪ/</text></svg>')


# ------------------------------------------------------------------
# 7. 영어 트랙 내용
# ------------------------------------------------------------------
RL_PAGES = [
    dict(t="R / L 발음 학습",
         lines=["**오늘의 학습 내용**: /r/과 /l/의 발음 차이와 정확한 발음 방법을 배워요.",
                "**학습 목표**:",
                "• /r/과 /l/의 조음 방식 차이를 이해하고, 두 소리를 구별할 수 있다.",
                "• 다양한 예시(단어, 구, 문장)에서 정확히 발음할 수 있다."],
         words=["right", "light"],
         vis=lambda: big("Right (/r/) vs Light (/l/)", 2.2) + "<p class='center'>두 단어의 발음 차이를 비교해서 들어 보세요!</p>"),
    dict(t="발음 원리 이해하기 (GIF 조음 가이드)",
         lines=["**/r/과 /l/의 혀 위치를 비교해 보세요!**",
                "• **/r/ 발음**: 혀가 입 안쪽(뒤쪽)으로 말리며 잇몸에 닿지 않아요.",
                "• **/l/ 발음**: 혀끝이 윗잇몸에 딱 닿아요."],
         words=["right", "light"], vis=render_r_l_gif),
]
EI_PAGES = [
    dict(t="eat과 it의 길이가 달라요",
         lines=["**eat** /iː/: 길고 혀가 높아요. 입은 작게 벌려요.", "**it** /ɪ/: 짧고 혀가 조금 낮아요.",
                "긴 소리는 글자를 늘여서 보여 줘요."],
         words=["eat", "it"],
         vis=eat_it_svg),
    dict(t="잠깐! 단어 첫 e는 소리가 달라요",
         lines=["**egg, end** → /ɛ/", "**even, equal** → /iː/", "**English** → /ɪ/"],
         words=["egg", "end", "even", "equal", "English"],
         vis=lambda: big("e ?", 3.5) + "<p class='center'>같은 e라도 단어마다 달라져요.</p>"),
]
SYL_PAGES = [
    dict(t="단어를 어디서 끊어 읽을까요?",
         lines=["철자 개수가 아니라 **모음 소리**를 들어야 해요.", "❌ speak → spe-ak (모음 글자 2개를 2음절로 셈)",
                "✅ speak → 1음절 (ea가 /iː/ 한 소리)", "❌ cake → ca-ke (끝의 e는 소리가 나지 않아요)"],
         words=["speak", "black", "cake"],
         vis=lambda: big("speak<br>1음절", 2.6) + "<p class='center'>모음 소리 하나 = 음절 하나</p>"),
    dict(t="음절이 나뉘는 규칙",
         lines=["**합성어** sea | shell", "**접두사** re | play", "**접미사** teach | er",
                "**모음 사이 자음 1개** pi | lot", "**모음 사이 자음 2개** dol | lar",
                "bl, br, st 같은 첫소리 묶음과 sh, ch, th는 나누지 않아요."],
         words=["seashell", "replay", "teacher", "pilot", "dollar"],
         vis=lambda: big("sea | shell<br>re | play", 2.2)),
]

for _pages, _tabs, _tips in (
    (RL_PAGES, ["학습 시작", "발음 원리"], ["r과 l은 소리가 달라요. 두 소리를 번갈아 들어 봐요.", "혀끝이 닿는지, 말리는지를 GIF로 확인해요."]),
    (EI_PAGES, ["길이 비교", "첫 e 소리"], ["긴 소리 /iː/는 입을 작게, 짧은 소리 /ɪ/는 조금 더 열어요.", "같은 e라도 단어에 따라 /ɛ/, /iː/, /ɪ/로 달라요."]),
    (SYL_PAGES, ["오류 발견", "규칙 배우기"], ["모음 글자 수와 음절 수는 같지 않을 수 있어요.", "먼저 모음 소리를 찾고, 그다음 경계를 정해요."]),
):
    for _p, _t, _tip in zip(_pages, _tabs, _tips):
        _p["tab"], _p["tip"] = _t, _tip


def slide_css():
    st.markdown("""<style>
    .hd{display:flex;justify-content:space-between;align-items:center;background:#7B1E2E;
        border-radius:14px;padding:8px 16px;margin:4px 0 8px}
    .hd b{color:#fff !important}
    .pill{display:inline-block;padding:3px 12px;border-radius:999px;font-size:.85rem;
          margin-left:6px;background:#a0495a;color:#fff !important}
    .pill.on{background:#fff;color:#7B1E2E !important;font-weight:800}
    .tip{background:#fdf0f2;border-left:6px solid #7B1E2E;border-radius:10px;
         padding:8px 14px;margin:8px 0;color:#5a1522 !important}
    [data-testid="stVerticalBlockBorderWrapper"]{border:2px solid #ecd0d5 !important;
         border-radius:18px !important;background:#fffafb}
    </style>""", unsafe_allow_html=True)


def header(sub, tabs, on):
    pills = "".join(f"<span class='pill{' on' if k == on else ''}'>{t}</span>" for k, t in enumerate(tabs))
    st.markdown(f"<div class='hd'><b>길라잡이 · {sub}</b><div>{pills}</div></div>", unsafe_allow_html=True)


def pg_move(d):
    ss.page += d


def render_concept(pages, lang="en-US"):
    slide_css()
    n = len(pages)
    pg = min(ss.page, n - 1)
    P = pages[pg]
    header(("영어" if ss.lang == "en" else "한국어") + " 발음 교실", [f"{k + 1:02d} {q['tab']}" for k, q in enumerate(pages)], pg)
    with st.container(border=True):
        st.markdown(f"<h2 style='color:{BURGUNDY};margin:0 0 6px'>{P['t']}</h2>", unsafe_allow_html=True)
        if callable(P.get("vis")):
            L, R = st.columns([5, 6])
            with L:
                for line in P["lines"]:
                    st.markdown(line)
                listen(P["words"], lang)
            with R:
                st.markdown(P["vis"](), unsafe_allow_html=True)
        else:
            for line in P["lines"]:
                st.markdown(line)
            listen(P["words"], lang)
    st.markdown(f"<div class='tip'>🔭 {P['tip']}</div>", unsafe_allow_html=True)
    
    nav_row(left=("← 이전", pg_move, (-1,), f"pv{pg}") if pg > 0 else None,
            right=("다음 →", pg_move, (1,), f"nx{pg}") if pg < n - 1 else ("개념 완료 ✓", finish_step, (), "cdone"))


def rl_item(w, mean, pos, ipa, kind):
    if kind == "r":
        tip, wrong = "r은 혀끝이 입천장에 닿지 않고 뒤로 말려요.", "l처럼 혀끝이 윗잇몸에 닿았어요."
        ask, model = "혀끝이 어디에 닿았나요? 닿지 않게 다시 해 볼까요?", "입술을 살짝 모으고 혀를 뒤로 당기며 시작해요."
    elif kind == "l":
        tip, wrong = "l은 혀끝이 윗잇몸에 닿아요.", "r처럼 혀끝이 닿지 않았어요."
        ask, model = "혀끝이 윗잇몸에 닿았나요? 다시 해 볼까요?", "혀끝을 윗잇몸에 딱 붙인 채 소리를 내요."
    else:
        tip, wrong = "r과 l을 구분해서 말해요.", "r과 l 중 일부가 같은 소리로 들렸어요."
        ask, model = "어느 소리가 r이고 어느 소리가 l인지 다시 확인해 볼까요?", "r은 혀를 말고, l은 혀끝을 윗잇몸에 붙여요."
    return dict(w=w, mean=mean, pos=pos, ipa=ipa, tip=tip, wrong=wrong, ask=ask, model=model)


RL_ITEMS = [
    rl_item("Right / Light", "단어 첫머리의 /r/과 /l/", "1단계 (단어)", "/raɪt/ vs /laɪt/", "b"),
    rl_item("Rice / Lice", "단어 첫머리의 /r/과 /l/", "2단계 (단어)", "/raɪs/ vs /laɪs/", "b"),
    rl_item("Curriculum", "단어 내부의 /r/와 /l/ 연속 발음", "3단계 (단어 내부)", "/kəˈrɪkjələm/", "b"),
    rl_item("Charging bus card", "R과 L이 모두 포함된 구", "4단계 (구 단위)", "/ˈtʃɑːrdʒɪŋ bʌs kɑːrd/", "b"),
    rl_item("There are a lot of people.", "R과 L이 모두 포함된 문장", "5단계 (문장 단위)", "/ðɛr ɑːr ə lɒt əv ˈpiːpəl/", "b")
]

EI_PAIRS = [("bed", "침대", "/bɛd/", "bit", "조금", "/bɪt/"), ("pen", "펜", "/pɛn/", "pin", "핀", "/pɪn/"),
            ("set", "놓다", "/sɛt/", "sit", "앉다", "/sɪt/"),
            ("pet", "애완동물", "/pɛt/", "pit", "구덩이", "/pɪt/"), ("bet", "내기", "/bɛt/", "bit", "조금", "/bɪt/")]
EI_ITEMS = [dict(p=[(a, b, c, "e"), (d, e, f, "i")]) for a, b, c, d, e, f in EI_PAIRS]
SYL_ITEMS = [
    dict(w="SPEAK", q="음절 수는?", opts=["1개", "2개"], ans=0, why="ea가 /iː/ 한 소리라서 1음절이에요. (모음 소리 1개)"),
    dict(w="SEASHELL", q="알맞은 경계는?", opts=["SEA | SHELL", "SE | ASHELL"], ans=0, why="합성어는 의미 단위로 나눠요."),
    dict(w="REPLAY", q="알맞은 경계는?", opts=["RE | PLAY", "REP | LAY"], ans=0, why="접두사 re와 어근 play를 나눠요."),
    dict(w="PILOT", q="알맞은 경계는?", opts=["PI | LOT", "PIL | OT"], ans=0, why="모음 사이 자음 1개는 보통 뒤 음절로 가요."),
    dict(w="CAKE", q="음절 수는?", opts=["1개", "2개"], ans=0, why="끝의 e는 소리가 나지 않아서 1음절이에요."),
]


def feedback(s, it=None):
    st.progress(s / 100, text=f"일치율 {s}%")
    if s >= 60:
        st.success("좋아요! 잘 발음했어요.")
    elif it:
        st.warning(f"① 오류 안내: {it['wrong']}\n\n② 다시 해 볼까요? {it['ask']}\n\n③ 이렇게 해 봐요: {it['model']}")


def practice_rec(it, idx):
    st.markdown(big(it["w"], 2.2) + f"<p class='center'>{it['ipa']} · {it['pos']} · {it['mean']}</p>"
                + (f"<p class='center'><b>{it['q']}</b></p>" if it.get("q") else ""), unsafe_allow_html=True)
    listen([it["w"]], it.get("lang", "en-US"))
    
    if "문장" in it['pos'] or "구" in it['pos']:
        intonation_hint = st.toggle("🔭 힌트: 문장 억양 및 발음 흐름 보기", key=f"intonation_{idx}_{ss.rnd}")
        if intonation_hint:
            st.markdown(sentence_intonation_svg(), unsafe_allow_html=True)
            st.caption("💡 문장이나 구를 말할 때는 단어 사이의 연음과 억양 곡선(높낮이)을 살려 말해야 자연스러워요.")

    a = st.audio_input("녹음하기", key=f"a{ss.step}_{idx}_{ss.rnd}")
    if not a:
        return False
    s, _ = score_audio(a, bump(1, 0.7))
    ss.ps[idx] = s
    feedback(s, it)
    if it.get("checks"):
        st.markdown("**확인할 항목:** " + " · ".join("☐ " + c_ for c_ in it["checks"]))
    return True


def practice_pair(it, idx):
    k = f"{ss.step}_{idx}_{ss.rnd}"
    hint = st.toggle("🔭 힌트: 소리 길이 보기", key=f"h{k}")
    words = [(p[0], p[3]) for p in it["p"]]
    html = ""
    for w, v in words:
        shown = stretch(w, v, 0.6 if v == "i" else 1.5) if hint else w
        html += big(shown, 2.4)
    st.markdown(html, unsafe_allow_html=True)
    tgt = st.radio("녹음할 단어", [0, 1], format_func=lambda j: f"{it['p'][j][0]}  {it['p'][j][2]} ({it['p'][j][1]})",
                   horizontal=True, key=f"r{k}")
    w, mean, ipa, v = it["p"][tgt]
    hi = v == "i"
    rt, rm = bump(0.9 if hi else 0.55, 0.5 if hi else 0.7), bump(0.35 if hi else 0.8, 0.5 if hi else 0.7)
    a = st.audio_input("녹음하기", key=f"a{k}_{tgt}")
    if not a:
        return False
    s, e = score_audio(a, rt)
    ss.ps[idx] = s
    if e:
        ut, um = [x * 0.9 for x in e], [x * (0.35 if hi else 0.8) for x in e]
        st.markdown(graph_svg(rm, um) + "<p>곡선과 그 대칭 곡선 사이 = 입이 벌어진 모양이에요. 오른쪽 타원은 입 모양의 움직임이에요.</p>",
                    unsafe_allow_html=True)
    it2 = dict(wrong="모음 길이와 입 모양이 목표와 달랐어요.", ask="이 단어의 모음이 길어야 할까요, 짧아야 할까요?",
               model="/iː/는 길게·입을 작게, /ɪ/는 짧게·혀를 조금 낮게 해요.")
    feedback(s, it2)
    return True


def practice_quiz(it, idx):
    st.markdown(big(it["w"], 2.6), unsafe_allow_html=True)
    c = st.radio(it["q"], it["opts"], index=None, key=f"q{ss.step}_{idx}_{ss.rnd}", horizontal=True)
    if c is None:
        return False
    ok = c == it["opts"][it["ans"]]
    ss.ps[idx] = 100 if ok else 0
    (st.success if ok else st.error)(("정답이에요! " if ok else "아쉬워요. ") + it["why"])
    return True


def adv():
    ss.pi += 1


def back():
    ss.pi -= 1


def redo(weak):
    ss.pact, ss.pi, ss.rnd = weak, 0, ss.rnd + 1


def render_practice(items, fn):
    slide_css()
    if ss.pact is None:
        ss.pact, ss.pi, ss.ps = list(range(len(items))), 0, {}
    act = ss.pact
    if ss.pi >= len(act):
        weak = [i for i in act if ss.ps.get(i, 0) < 60]
        st.markdown(f"<h2 class='center' style='color:{BURGUNDY}'>연습 끝!</h2>", unsafe_allow_html=True)
        if weak:
            names = [items[i].get("w") or items[i]["p"][0][0] + "/" + items[i]["p"][1][0] for i in weak]
            st.warning("부족한 발음: " + ", ".join(names))
            st.markdown("**부족한 발음을 다시 학습할까요?**")
            
            nav_row(left=("🏠 홈으로 돌아가기", go_home, (), "pe_home1"),
                    mid=("네, 다시 학습", redo, (weak,), "redo"),
                    right=("아니요, 단계 완료", finish_step, (), "skip"))
        else:
            st.success("모두 통과했어요!")
            
            nav_row(left=("🏠 홈으로 돌아가기", go_home, (), "pe_home2"),
                    right=("단계 완료 ✓", finish_step, (), "pdone"))
        return
    idx = act[ss.pi]
    header(("영어" if ss.lang == "en" else "한국어") + " 발음 교실 · 연습", [str(k + 1) for k in range(len(act))], ss.pi)
    with st.container(border=True):
        done = fn(items[idx], idx)
    it = items[idx]
    tip = it.get("tip") or ("두 단어의 모음 길이와 혀 높이를 비교해 봐요." if "p" in it else "모음 소리 하나가 음절 하나예요.")
    st.markdown(f"<div class='tip'>🔭 유의할 점: {tip}</div>", unsafe_allow_html=True)
    
    nav_row(left=("← 이전", back, (), f"pb{ss.step}_{idx}_{ss.rnd}") if ss.pi > 0 else None,
            right=("다음 →" if done else "건너뛰기 →", adv, (), f"n{ss.step}_{idx}_{ss.rnd}"))


# ------------------------------------------------------------------
# 8. 한국어 트랙 내용
# ------------------------------------------------------------------
def tissue_svg(label, ang, note):
    return ('<div style="display:inline-block;width:48%;text-align:center"><svg viewBox="0 0 200 140" width="100%">'
            '<circle cx="35" cy="75" r="28" fill="#f1d3b3" stroke="#7B1E2E" stroke-width="2"/>'
            '<ellipse cx="58" cy="78" rx="6" ry="4" fill="#7B1E2E"/>'
            f'<rect x="82" y="30" width="14" height="95" rx="4" fill="#ffd9dd" stroke="#7B1E2E" '
            f'transform="rotate({-ang} 89 30)"/></svg><b>{label}</b><br>{note}</div>')


def wave_svg(ref, usr):
    p = ['<svg viewBox="0 0 700 140" width="100%" style="max-height:24vh">']
    for vals, col in ((ref, "#bbb"), (usr, BURGUNDY)):
        pts = " ".join(f"{j * 700 / 39:.0f},{120 - v * 100:.0f}" for j, v in enumerate(vals))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3"/>')
    return "".join(p) + "</svg>"


def vowel_svg():
    def chart(title, pts):
        s = (f'<div style="display:inline-block;width:48%;text-align:center"><b>{title}</b>'
             '<svg viewBox="0 0 200 150" width="100%"><rect x="10" y="10" width="180" height="120" fill="#fffafb" stroke="#ecd0d5"/>')
        for t, x, y in pts:
            s += f'<text x="{x}" y="{y}" text-anchor="middle" font-size="22" fill="#7B1E2E">{t}</text>'
        return s + '<text x="14" y="146" font-size="10">앞</text><text x="178" y="146" font-size="10">뒤</text></svg></div>'
    ja = [("い", 40, 40), ("う", 160, 40), ("え", 50, 85), ("お", 150, 90), ("あ", 100, 122)]
    ko = [("ㅣ", 35, 40), ("ㅡ", 105, 40), ("ㅜ", 165, 40), ("ㅔ", 45, 85), ("ㅓ", 115, 88), ("ㅗ", 165, 88), ("ㅏ", 100, 122)]
    return chart("일본어 모음", ja) + chart("한국어 단모음", ko) + "<p class='center'>위 = 혀가 높아요 · 아래 = 낮아요</p>"


KO_CONS_PAGES = [
    dict(t="평음과 격음, 바람 세기가 달라요",
         lines=["**평음** ㅂ ㄷ ㄱ ㅈ ㅅ: 바람이 약하고 성대가 부드럽게 울려요.", 
                "**격음** ㅍ ㅌ ㅋ ㅊ: 바람이 강하게 터져 나와요.",
                "입 앞에 손가락이나 휴지를 대고 발음해 차이를 느껴 보세요."],
         words=["바다", "파다"],
         vis=lambda: tissue_svg("평음 (바다)", 10, "휴지가 살짝 움직여요") + tissue_svg("격음 (파다)", 55, "휴지가 크게 날려요")),
    dict(t="소리가 만들어지는 위치 (조음 위치)",
         lines=["한국어 자음은 **어디에서 소리가 만들어지는지**에 따라 나뉘어요.",
                "• **입술소리** ㅂ ㅍ ㅁ: 두 입술을 붙였다가 떼면서 소리를 내요. (바다, 파다)",
                "• **잇몸소리** ㄷ ㅌ ㄴ ㅅ ㄹ: 혀끝을 윗잇몸에 대고 소리를 내요. (달, 탈)",
                "• **센입천장소리** ㅈ ㅊ: 혀의 앞쪽을 잇몸 뒤쪽의 딱딱한 입천장에 대요. (자, 차)",
                "• **여린입천장소리** ㄱ ㅋ ㅇ: 혀뿌리를 입천장 안쪽의 부드러운 부분에 대요. (가, 카)",
                "• **목청소리** ㅎ: 목에서 바람이 나와요.",
                "같은 위치에서도 **바람의 세기**에 따라 평음과 격음으로 나뉘어요: ㅂ↔ㅍ · ㄷ↔ㅌ · ㅈ↔ㅊ · ㄱ↔ㅋ"],
         words=["바다", "파다", "달", "탈", "자", "차", "가", "카"],
         vis=None),
    dict(t="짝으로 비교해서 연습하기",
         lines=["ㄱ↔ㅋ 가/카 · ㄷ↔ㅌ 다/타", "ㅂ↔ㅍ 바/파 · ㅈ↔ㅊ 자/차",
                "단어로도 비교해 보세요: 바다/파다 · 비다/피다 · 달/탈 · 자다/차다"],
         words=["바다", "파다", "비다", "피다", "달", "탈", "자다", "차다"],
         vis=lambda: big("비다 ≠ 피다", 2.6) + "<p class='center'>뜻이 달라져요: 비다(empty) / 피다(bloom)</p>"),
]
KO_VOW_PAGES = [
    dict(t="먼저, 두 언어의 모음은 어떻게 다를까요?",
         lines=["일본어 「う」는 보통 /ɯ/로 표기하며 강한 원순성이 없어요.",
                "한국어 모음은 혀의 앞뒤·높이와 입술 모양을 함께 봐요.",
                "「う」와 ㅜ는 비슷하지만 입술 모양에 차이가 있어요.", "각 모음을 눌러 소리를 들어 보세요."],
         words=["이", "으", "우", "에", "어", "오", "아"], vis=vowel_svg),
    dict(t="입술 모양과 혀의 위치가 발음을 바꿔요",
         lines=["**ㅜ** 입술을 둥글게 오므려요 (부족하면 ㅡ와 혼동)", "**ㅡ** 입술을 둥글게 하지 않아요",
                "**ㅗ** 입술은 둥글게, 입은 비교적 좁게", "**ㅓ** 입을 더 열고 둥글게 하지 않아요 (ㅗ와 혼동 주의)",
                "**ㅘ ㅝ ㅙ ㅞ** 앞의 /w/ 활음 탈락 주의 · **ㅢ** /w/로 바뀌는 활음 대치 주의 · **ㅖ** 예·세계·계절"],
         words=["굴", "글", "곰", "검", "금", "과일", "원", "왜", "웨이터", "의사", "의자", "예", "세계"],
         vis=lambda: big("ㅜ · ㅡ<br>ㅗ · ㅓ", 2.2) + "<p class='center'>이중모음: 과일 · 원 · 왜 · 웨이터 · 의사</p>"),
]
KO_SYL_PAGES = [
    dict(t="받침 ㅁ ㄴ ㅇ을 구분해요",
         lines=["일본어 ん은 하나지만 한국어 받침은 셋이에요.", "**감** 입술이 닫혀요 · **간** 혀끝이 윗잇몸 · **강** 혀뿌리가 올라가요",
                "내 녹음을 다시 들으며 받침 소리가 어디서 끝나는지 확인해요."],
         words=["감", "간", "강"], vis=lambda: big("감 · 간 · 강", 2.6)),
    dict(t="받침도 한 박자예요",
         lines=["노래방 가사처럼 한 글자 = 한 박자예요.", "받침을 따로 늘이거나 새 박자로 세지 않아요.",
                "일본어 パン · かん 처럼 ん으로 끝나는 말과 비교해 봐요."],
         words=["사랑", "친구", "공부"], vis=lambda: big("사 · 랑<br>1박 · 1박", 2.4)),
]
for _pages, _tabs, _tips in (
    (KO_CONS_PAGES, ["바람 세기", "조음 위치", "짝 비교"], ["평음은 약하게, 격음은 강하게 바람을 내요.", "혀와 입술이 닿는 위치를 정확히 지켜요.", "소리 하나 차이로 뜻이 달라져요."]),
    (KO_VOW_PAGES, ["도입", "제시"], ["일본어 う와 한국어 ㅜ는 입술 모양이 달라요.", "활음(/w/)이 약해지거나 바뀌지 않게 주의해요."]),
    (KO_SYL_PAGES, ["받침 구분", "박자"], ["받침 소리가 끝나는 위치를 느껴 봐요.", "한 글자는 한 박자로 읽어요."]),
):
    for _p, _t, _tip in zip(_pages, _tabs, _tips):
        _p["tab"], _p["tip"] = _t, _tip


def ko_item(w, mean, pos, ipa, tip, q="", checks=None):
    return dict(kind="rec", lang="ko-KR", w=w, mean=mean, pos=pos, ipa=ipa, tip=tip, q=q, checks=checks,
                wrong=f"{tip} 부분이 목표와 달랐어요.", ask="어디가 달랐는지 다시 들어 보고 해 볼까요?", model=tip)


def ko_listen(say, opts, tip):
    ans = next(i for i, o in enumerate(opts) if o.split()[-1] == say)
    return dict(kind="listen", w=say, say=say, opts=opts, ans=ans, tip=tip)


def ko_pair(a, b, tip, cons=False, checks=None):
    return dict(kind="pair", p=[a, b], tip=tip, cons=cons, checks=checks)


VCHK = ["입술의 원순성", "혀의 높이", "활음의 연결 여부"]

KO_CONS_ITEMS = [
    ko_listen(s_, o_, "평음은 바람이 약하고, 격음은 바람이 강해요.") for s_, o_ in (
        ("가", ["ㄱ  가", "ㅋ  카"]), ("타", ["ㄷ  다", "ㅌ  타"]), ("바", ["ㅂ  바", "ㅍ  파"]), ("차", ["ㅈ  자", "ㅊ  차"]),
        ("카", ["ㄱ  가", "ㅋ  카"]), ("다", ["ㄷ  다", "ㅌ  타"]), ("파", ["ㅂ  바", "ㅍ  파"]), ("자", ["ㅈ  자", "ㅊ  차"]))
] + [
    ko_pair(("바다", "넓고 짠물이 있는 곳"), ("파다", "땅에 구멍을 내다"), "격음 ㅍ은 입 앞 손가락에 센 바람이 느껴져요.", True),
    ko_pair(("비다", "속이 없다"), ("피다", "꽃이 열리다"), "격음 ㅍ은 입술을 터뜨리며 센 바람을 내요.", True),
    ko_pair(("달", "하늘의 달"), ("탈", "얼굴에 쓰는 탈"), "ㅌ은 더 센 바람이 나와요.", True),
    ko_pair(("자다", "잠을 자다"), ("차다", "발로 차다"), "ㅊ은 더 센 바람이 나와요.", True),
    ko_pair(("불", "타는 불"), ("풀", "자라는 풀"), "ㅍ은 센 바람을 내요.", True),
]
KO_VOW_ITEMS = [
    ko_pair(("굴", "oyster"), ("글", "text"), "ㅜ는 입술을 둥글게 오므려요.", checks=VCHK),
    ko_pair(("곰", "bear"), ("검", "sword"), "ㅗ는 입술을 둥글게, ㅓ는 입을 더 열어요.", checks=VCHK),
    ko_pair(("곰", "bear"), ("금", "gold"), "ㅗ는 입술을 둥글게, ㅡ는 둥글게 하지 않아요.", checks=VCHK),
    ko_pair(("검", "sword"), ("금", "gold"), "ㅓ는 입을 열고 ㅡ는 입술을 펴요.", checks=VCHK),
    ko_item("과일", "fruit", "명사", "/kwa.il/", "ㅘ의 /w/ 활음이 사라지지 않게 해요.", "/w/가 자연스럽게 이어지나요?", VCHK),
    ko_item("원", "circle", "명사", "/wʌn/", "첫 활음 /w/가 들리게 해요.", "첫 활음이 들리나요?", VCHK),
    ko_item("왜", "why", "부사", "/wɛ/", "두 소리가 끊기지 않고 이어요.", "두 소리가 끊기지 않나요?", VCHK),
    ko_item("웨이터", "waiter", "명사", "/wei.tʰʌ/", "입 모양이 자연스럽게 바뀌게 해요.", "입 모양이 자연스럽게 바뀌나요?", VCHK),
    ko_item("의사", "doctor", "명사", "/ɰi.sa/", "ㅢ의 첫 소리가 /w/처럼 바뀌지 않게 해요.", "첫 요소가 /w/로 바뀌지 않나요?", VCHK),
    ko_item("저는 손이 커요", "I have big hands", "문장", "/tɕʌ.nɯn so.ni kʰʌ.jo/", "ㅓ와 ㅗ를 구분해요.",
            "최종 미션: 문장 발음하기 (먼저 목표 단어를 하나씩 연습해요)", VCHK),
]
KO_SYL_ITEMS = [ko_item(w, m, "명사", ipa, t) for w, m, ipa, t in (
    ("감", "persimmon", "/kam/", "ㅁ: 입술을 닫고 끝내요."), ("간", "liver", "/kan/", "ㄴ: 혀끝이 윗잇몸에 대요."),
    ("강", "river", "/kaŋ/", "ㅇ: 혀뿌리를 올리고 입은 열어요."), ("밤", "night", "/pam/", "ㅁ: 입술을 닫고 끝내요."),
    ("방", "room", "/paŋ/", "ㅇ: 입은 열고 코로 소리를 내요."), ("사랑", "love", "/sa.raŋ/", "한 글자 = 한 박자로 읽어요."),
    ("친구", "friend", "/tɕʰin.ku/", "ㄴ 받침이 별도 박자가 되지 않게 해요."))]
KO_SYL_ITEMS.append(ko_item("저는 감이 좋아요", "I like persimmons", "문장", "/tɕʌ.nɯn ka.mi tɕo.a.jo/", "받침 소리를 구분해 이어 읽어요."))


def retry():
    ss.rnd += 1


def practice_ko(it, idx):
    k = f"{ss.step}_{idx}_{ss.rnd}"
    if it["kind"] == "rec":
        return practice_rec(it, idx)
    if it["kind"] == "listen":
        st.markdown(big("🎧 듣고 고르기", 2) + "<p class='center'>들린 첫소리와 같은 자음을 골라요. 실수하면 한 번 더 들어 봐요.</p>",
                    unsafe_allow_html=True)
        listen([it["say"]], "ko-KR", hide=True)
        c = st.radio("들린 소리를 고르세요", it["opts"], index=None, key=f"q{k}", horizontal=True)
        if c is None:
            return False
        ok = c == it["opts"][it["ans"]]
        ss.ps[idx] = 100 if ok else 0
        (st.success if ok else st.error)(("정답이에요! " if ok else "아쉬워요. ") + f"정답은 {it['opts'][it['ans']]}이에요. {it['tip']}")
        return True
    st.markdown("".join(big(p[0], 2.2) + f"<p class='center'>{p[1]}</p>" for p in it["p"]), unsafe_allow_html=True)
    listen([p[0] for p in it["p"]], "ko-KR")
    if it.get("cons"):
        if not st.checkbox("✓ 뜻을 확인했어요 (확인한 뒤 녹음해요)", key=f"m{k}"):
            return False
        st.info("기식 확인: 입 앞에 손가락을 대고 약한 공기(평음), 강한 공기(격음)를 느껴 보세요. "
                "이어 연습할 대조 단어: 바다/파다 · 비다/피다 · 달/탈 · 자다/차다")
    t = st.radio("녹음할 단어", [0, 1], format_func=lambda j: it["p"][j][0], horizontal=True, key=f"r{k}")
    a = st.audio_input("녹음하기", key=f"a{k}_{t}")
    if not a:
        return False
    s, e = score_audio(a, bump(1, 0.6))
    ss.ps[idx] = s
    if e:
        st.markdown(wave_svg(bump(1, 0.6), e) + "<p>회색 = 기준 소리 모양, 붉은 선 = 내 소리</p>", unsafe_allow_html=True)
        if it.get("cons"):
            avg = int(sum(ss.ps.values()) / len(ss.ps))
            c = st.columns(2)
            c[0].metric("파형 일치율", f"{s}%")
            c[1].metric("일관성(이번 단계 평균)", f"{avg}%")
            st.caption("일관성: 여러 단어에서 평음/격음 구별이 안정적으로 유지되는지 확인해요.")
    feedback(s, dict(wrong="목표 소리와 달랐어요.", ask="입 모양과 바람을 다시 확인하고 해 볼까요?", model=it["tip"]))
    if it.get("checks"):
        st.markdown("**확인할 항목:** " + " · ".join("☐ " + c_ for c_ in it["checks"]))
    st.button("다시 발음하기", on_click=retry, key=f"rt{k}")
    return True


def render_ko(i):
    if i == 0: render_concept(KO_CONS_PAGES, "ko-KR")
    elif i == 1: render_practice(KO_CONS_ITEMS, practice_ko)
    elif i == 2: render_concept(KO_VOW_PAGES, "ko-KR")
    elif i == 3: render_practice(KO_VOW_ITEMS, practice_ko)
    elif i == 4: render_concept(KO_SYL_PAGES, "ko-KR")
    elif i == 5: render_practice(KO_SYL_ITEMS, practice_ko)


def render_en(i):
    if i == 0: render_concept(RL_PAGES)
    elif i == 1: render_practice(RL_ITEMS, practice_rec)
    elif i == 2: render_concept(EI_PAGES)
    elif i == 3: render_practice(EI_ITEMS, practice_pair)
    elif i == 4: render_concept(SYL_PAGES)
    elif i == 5: render_practice(SYL_ITEMS, practice_quiz)


# ------------------------------------------------------------------
# 9. 최종 테스트 및 결과
# ------------------------------------------------------------------
def t_submit(ok):
    ss.t["a"][ss.t["q"]] = ok
    ss.t["ph"] = "fb"


def complete_final():
    d, lang = ss.data, ss.lang
    d["done"][lang][6] = True
    if all(d["done"][lang]):
        d["count"][lang] += 1
        d["done"][lang] = [False] * 7
        ss.fp = True
    d["last_step"] = None
    touch()


def t_next():
    t = ss.t
    if t["q"] >= 9:
        t["ph"] = "res"
        complete_final()
    else:
        t["q"] += 1
        t["ph"] = "q"


def t_goto(ph):
    ss.t["ph"] = ph


def retake():
    ss.t = None
    ss.tn = ss.get("tn", 0) + 1


def t_jump(si):
    t = ss.t
    open_step(si)
    ss.t = t
    ss.rv = True


def donut_svg(pct):
    C = 2 * math.pi * 70
    return ('<svg viewBox="0 0 200 200" width="230">'
            '<circle cx="100" cy="100" r="70" fill="none" stroke="#d9534f" stroke-width="26"/>'
            f'<circle cx="100" cy="100" r="70" fill="none" stroke="#2e9e5b" stroke-width="26" '
            f'stroke-dasharray="{C * pct / 100:.1f} {C:.1f}" transform="rotate(-90 100 100)"/>'
            f'<text x="100" y="108" text-anchor="middle" font-size="34" font-weight="800" fill="#333">{pct}%</text></svg>')


EN_Q = [
    dict(k="listen", lv=1, q="들린 단어를 고르세요", say="light", opts=["right", "light"], ans=1,
         c="r과 l은 다른 소리예요. l은 혀끝이 윗잇몸에 닿아요.", s=0),
    dict(k="mc", lv=1, q="SPEAK은 몇 음절일까요?", opts=["1음절", "2음절"], ans=0,
         c="모음 소리 하나가 음절 하나예요. ea는 /iː/ 한 소리예요.", s=4),
    dict(k="mc", lv=1, q="eat과 it 중 더 길게 발음하는 것은?", opts=["eat", "it"], ans=0,
         c="eat /iː/는 길고 입을 작게, it /ɪ/는 짧아요.", s=2),
    dict(k="mc", lv=2, q="혀끝이 윗잇몸에 닿는 소리는?", opts=["r", "l"], ans=1,
         c="l은 혀끝이 윗잇몸에 닿고, r은 닿지 않고 뒤로 말려요.", s=0),
    dict(k="mc", lv=2, q="Even의 첫 e 소리는?", opts=["/ɛ/", "/iː/", "/ɪ/"], ans=1,
         c="even, equal은 /iː/, egg, end는 /ɛ/, English는 /ɪ/예요.", s=2),
    dict(k="mc", lv=2, q="PILOT의 알맞은 음절 경계는?", opts=["PI | LOT", "PIL | OT"], ans=0,
         c="모음 사이 자음 1개는 보통 뒤 음절로 가요.", s=4),
    dict(k="rec", lv=2, q="소리 내어 읽어 보세요", w="bit", c="/ɪ/는 짧게, 혀를 조금 낮게 해요.", s=2),
    dict(k="rec", lv=3, q="소리 내어 읽어 보세요", w="rice", c="r은 혀끝이 닿지 않게 뒤로 말아요.", s=0),
    dict(k="mc", lv=3, q="TEACHER의 알맞은 음절 경계는?", opts=["TEACH | ER", "TEA | CHER"], ans=0,
         c="접미사 -er는 어근과 나눠요.", s=4),
    dict(k="rec", lv=3, q="문장을 읽어 보세요", w="There are a lot of people", c="r과 l을 구분해서 읽어요.", s=0),
]
KO_Q = [
    dict(k="listen", lv=1, q="들린 단어를 고르세요", say="바다", opts=["바다", "파다"], ans=0,
         c="평음 ㅂ은 바람이 약해요.", s=0),
    dict(k="mc", lv=1, q="바람이 더 강하게 나오는 소리는?", opts=["ㅂ", "ㅍ"], ans=1,
         c="격음 ㅍ ㅌ ㅋ ㅊ은 바람이 강하게 터져 나와요.", s=0),
    dict(k="mc", lv=1, q="입술을 둥글게 오므리는 모음은?", opts=["ㅜ", "ㅡ"], ans=0,
         c="한국어 ㅜ는 입술을 둥글게 오므려요. 약하면 ㅡ처럼 들려요.", s=2),
    dict(k="mc", lv=2, q="입술이 닫히며 끝나는 받침이 있는 글자는?", opts=["감", "간", "강"], ans=0,
         c="감은 입술이 닫히고, 간은 혀끝이 윗잇몸에, 강은 혀뿌리가 올라가요.", s=4),
    dict(k="listen", lv=2, q="들린 단어를 고르세요", say="탈", opts=["달", "탈"], ans=1,
         c="격음 ㅌ은 평음 ㄷ보다 바람이 강해요.", s=0),
    dict(k="mc", lv=2, q="‘왜’를 발음할 때 주의할 점은?", opts=["두 소리가 끊기지 않고 이어져요", "첫 활음을 빼고 읽어요"], ans=0,
         c="ㅘ ㅝ ㅙ ㅞ에서 앞의 /w/ 활음이 사라지지 않게 해요.", s=2),
    dict(k="rec", lv=2, q="소리 내어 읽어 보세요", w="파다", c="ㅍ은 센 바람이 나와요.", s=0),
    dict(k="rec", lv=3, q="문장을 읽어 보세요", w="저는 손이 커요", c="ㅓ와 ㅗ를 구분해요.", s=2),
    dict(k="mc", lv=3, q="‘사랑’은 몇 박자로 읽을까요?", opts=["2박자", "3박자"], ans=0,
         c="한 글자는 한 박자예요. 받침을 따로 늘이지 않아요.", s=4),
    dict(k="rec", lv=3, q="문장을 읽어 보세요", w="저는 감이 좋아요", c="받침 소리를 구분해 이어 읽어요.", s=4),
]


def render_test():
    slide_css()
    lang = ss.lang
    Q = EN_Q if lang == "en" else KO_Q
    tts = "en-US" if lang == "en" else "ko-KR"
    sub = ("영어" if lang == "en" else "한국어") + " 발음 교실 · 최종 테스트"
    if ss.get("t") is None:
        ss.t = dict(q=0, a=[None] * 10, ph="q")
    t = ss.t
    ph, q = t["ph"], t["q"]

    if ph in ("q", "fb"):
        header(sub, [f"{q + 1} / 10"], 0)
        st.markdown(f"<div style='height:5px;background:#eee;border-radius:3px'><div style='width:{(q + (ph == 'fb')) * 10}%;"
                    f"height:5px;background:{BURGUNDY};border-radius:3px'></div></div>", unsafe_allow_html=True)
        Qd = Q[q]
        stars = "★" * Qd["lv"] + "☆" * (3 - Qd["lv"])
        if ph == "q":
            with st.container(border=True):
                st.markdown(f"<span style='color:{BURGUNDY};font-size:1.4rem'>{stars}</span> 난이도 · {Qd['q']}",
                            unsafe_allow_html=True)
                key = f"{ss.get('tn', 0)}_{q}"
                if Qd["k"] == "rec":
                    st.markdown(big(Qd["w"], 2.4), unsafe_allow_html=True)
                    a = st.audio_input("녹음하기", key=f"ta{key}")
                    ok = bool(a) and score_audio(a, bump(1, 0.7))[0] >= 60
                    ready = bool(a)
                else:
                    if Qd["k"] == "listen":
                        listen([Qd["say"]], tts, hide=True)
                    c = st.radio("답을 고르세요", Qd["opts"], index=None, key=f"tq{key}", horizontal=True)
                    ready = c is not None
                    ok = ready and c == Qd["opts"][Qd["ans"]]
            
            c1, c2 = st.columns([3, 1])
            with c2:
                st.button("답 체크", on_click=t_submit, args=(ok,), disabled=not ready, key=f"tb{key}")
        else:
            ok = t["a"][q]
            st.markdown(big("✅ 정답이에요!" if ok else "❌ 아쉬워요", 2.4), unsafe_allow_html=True)
            ans = Qd["w"] if Qd["k"] == "rec" else Qd["opts"][Qd["ans"]]
            st.markdown(f"<p class='center'>정답/목표: <b>{ans}</b></p>", unsafe_allow_html=True)
            tag = (f"<span style='font-size:.75rem;background:#fff;border:1px solid {BURGUNDY};"
                   f"border-radius:8px;padding:1px 8px'>{STEPS[lang][Qd['s']]}</span>")
            st.markdown(f"<div class='tip'>🔭 관련 개념: {Qd['c']} {tag}</div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns([3, 1])
            with c2:
                st.button("결과 보기 →" if q >= 9 else "다음 문제 →", on_click=t_next, key=f"tn{q}")
        return

    wrong = [i for i, ok in enumerate(t["a"]) if not ok]
    if ph == "res":
        pct = (10 - len(wrong)) * 10
        header(sub, ["결과"], 0)
        st.markdown(f"<div class='center'>{donut_svg(pct)}<h3>정답 {10 - len(wrong)}개 · "
                    f"<span style='color:#2e9e5b'>정답률 {pct}%</span> · "
                    f"<span style='color:#d9534f'>오답률 {100 - pct}%</span></h3></div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if wrong:
                st.button("틀린 문제 복습", on_click=t_goto, args=("rev",), key="r_rev")
            else:
                st.success("모두 맞혔어요! 🎉")
        with c2:
            st.button("🏠 홈으로 돌아가기", on_click=go_home, key="r_home")
        return

    header(sub, ["틀린 문제 복습"], 0)
    steps = sorted({Q[i]["s"] for i in wrong})
    with st.container(border=True):
        for si in steps:
            qs = ", ".join(str(i + 1) for i in wrong if Q[i]["s"] == si)
            c = st.columns([4, 2, 2])
            c[0].markdown(f"**{STEPS[lang][si]}** · 틀린 문제 {qs}번")
            c[1].button("개념 보기", on_click=t_jump, args=(si,), key=f"j{si}")
            c[2].button("연습하기", on_click=t_jump, args=(si + 1,), key=f"jp{si}")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.button("테스트 재응시", on_click=retake, key="retake")
    with c2:
        st.button("🏠 홈으로 돌아가기", on_click=go_home, key="rv_home")


# ------------------------------------------------------------------
# 10. 앱 메인 분기
# ------------------------------------------------------------------
SCREENS = {"start": screen_start, "home": screen_home, "step": screen_step,
           "stepend": screen_stepend, "finale": screen_finale}
SCREENS[ss.screen]()
