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

ASSET_DIR = Path(__file__).parent / "language_app_assets"

START_BEAR_IMG = ASSET_DIR / "KakaoTalk_20261106_111319916.png"
HINT_BEAR_IMG = ASSET_DIR / "KakaoTalk_20261106_171655325.png"
FINAL_BEARS_IMG = ASSET_DIR / "KakaoTalk_20261106_171655325_02.png"

import streamlit as st
import streamlit.components.v1 as components
import re

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

    if ss.get("resume") and ss.screen == "start":
        ss.lang = ss.resume[0]

    ss.syl_type = None
    ss.syl_page = "concept"
    ss.syl_index = 0
    ss.syl_quiz_index = 0
    ss.syl_answers = {}
    ss.syl_submitted = False
    ss.syl_practice_index = 0

    ss.screen = "home"
    touch()


def set_lang(lang):
    ss.lang = lang
    ss.resume = None


def open_step(i):
    ss.step = i
    ss.page, ss.pact, ss.pi, ss.ps, ss.rnd = 0, None, 0, {}, 0
    ss.rl_sound = "r"
    ss.rl_scores = {"r": {}, "l": {}}
    ss.t, ss.rv = None, False
    ss.resume = None
    ss.data["last_lang"] = ss.lang
    ss.data["last_step"] = i

    # 5단계: 음절 개념 학습 초기화
    if i == 4:
        ss.syl_concept_type_index = 0
        ss.syl_concept_page_index = 0

    # 6단계: 통합 음절 연습 초기화
    elif i == 5:
        ss.syl_quiz_index = 0
        ss.syl_answers = {}
        ss.syl_submitted = False
        ss.syl_practice_index = 0
        ss.syl_scores = {}
        ss.syl_page = "quiz"

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

def top_bar(title=""):
    c1, c2 = st.columns([1, 5])

    with c1:
        st.button("🏠 홈으로", on_click=go_home, key="home_btn")

    with c2:
        if title:
            st.markdown(
                f"<h3 style='margin:0.3rem 0'>{title}</h3>",
                unsafe_allow_html=True
            )

def nav_row(left=None, mid=None, right=None):
    """버튼 한 줄: 왼쪽/가운데/오른쪽 칸에 하나씩 놓아요."""
    cols = st.columns([2, 3, 2])

    for col, spec in zip(cols, (left, mid, right)):
        if spec:
            label, fn, args, key = spec
            col.button(
                label,
                on_click=fn,
                args=args,
                key=key,
                width="stretch"
            )


# ------------------------------------------------------------------
# 5. 주요 화면 렌더링
# ------------------------------------------------------------------
def screen_start():
    debug_box()
    inject_css(dark=True)
    st.markdown("<div style='height:9vh'></div>", unsafe_allow_html=True)
    c_bear_l, c_bear, c_bear_r = st.columns([1, 2, 1])
    with c_bear:
        from PIL import Image

    image_data = base64.b64encode(START_BEAR_IMG.read_bytes()).decode("utf-8")

    st.markdown(
        f"""
        <div style="text-align: center;">
            <img
                src="data:image/png;base64,{image_data}"
                width="340"
                style="display: block; margin: auto;"
            >
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div style="text-align: center;">
            <img
                src="data:image/png;base64,{image_data}"
                width="340"
                style="display: block; margin: auto;"
            >
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <h1 class='center' style='font-size:2.3rem;margin:0.3rem 0'>
            발음 오류 수정 프로그램
        </h1>
        <p class='center' style='font-size:1.1rem;color:#ffe58a;line-height:1.7'>
            아기곰이 오류를 해결하고 별을 밝혀<br>
            엄마곰을 만날 수 있게 도와주세요
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(dipper_html([False] * 7, dark=True), unsafe_allow_html=True)

    st.markdown("<div style='height:2vh'></div>", unsafe_allow_html=True)

    _, start_col, _ = st.columns([1, 2, 1])

    with start_col:
        st.button(
            "별 따라 시작하기",
            on_click=go_home,
            key="start_btn",
            width="stretch",
            type="primary"
        )


def screen_home():
    debug_box()
    inject_css(dark=False)
    d = ss.data
    lang = ss.lang

    # 제목과 소제목
    st.markdown(
        f"""
        <div style="text-align:center; margin: 20px 0 8px 0;">
            <div style="
                color:{BURGUNDY};
                font-size:2rem;
                font-weight:800;
                line-height:1.35;
            ">
                발음 오류 수정 프로그램
            </div>

        """,
        unsafe_allow_html=True
    )

    # 아기곰 이미지
    image_data = base64.b64encode(START_BEAR_IMG.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div style="text-align:center; margin:12px auto 18px auto;">
            <img src="data:image/png;base64,{image_data}"
                 alt="아기곰"
                 width="220"
                 style="display:block; margin:0 auto; max-width:80%;">
        </div>
        """,
        unsafe_allow_html=True
    )

    # 학습 횟수와 언어 이동
    c1, c2, c3 = st.columns([2, 3, 2])

    if d["count"]["en"] + d["count"]["ko"] > 0:
        c2.markdown(
            f"<div class='bubble center'>이수 횟수 · 영어 {d['count']['en']}회 · "
            f"한국어 {d['count']['ko']}회</div>",
            unsafe_allow_html=True
        )

    other = "ko" if lang == "en" else "en"
    c3.button(
        f"{LANG_NAMES[other]} 학습으로 이동",
        on_click=set_lang,
        args=(other,),
        key="lang_btn"
    )

    # 북두칠성과 학습 단계
    image_data = base64.b64encode(START_BEAR_IMG.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div style="text-align: center; margin: 15px 0;">
            <img src="data:image/png;base64,{image_data}"
                 width="250"
                 style="display: block; margin: auto;">
        </div>
        """,
        unsafe_allow_html=True
    )

    blink = None
    if ss.resume and ss.resume[0] == lang:
        blink = ss.resume[1]
        b2 = st.columns([1, 6])[1]
        b2.markdown(
            "<div class='bubble' style='margin-top:1rem'>"
            "종료한 시점의 단계입니다!</div>",
            unsafe_allow_html=True
        )

    st.markdown(
        dipper_html(d["done"][lang], blink=blink),
        unsafe_allow_html=True
    )

    cols = st.columns(7)
    for i, col in enumerate(cols):
        col.button(
            f"{i + 1}. {STEPS[lang][i]}",
            on_click=open_step,
            args=(i,),
            key=f"star_{i}"
        )

    st.markdown(
        "<p class='center' style='margin-top:0.6rem'>"
        "별 아래 단계를 눌러 원하는 순서로 학습해요.</p>",
        unsafe_allow_html=True
    )

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

    image_data = base64.b64encode(START_BEAR_IMG.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin:15px 0;">
            <img src="data:image/png;base64,{image_data}"
                 width="250" style="display:block;">
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "<h2 class='center' style='color:%s'>별이 하나 빛났어요!</h2>" % BURGUNDY,
        unsafe_allow_html=True
    )
    st.markdown(dipper_html(ss.data["done"][lang]), unsafe_allow_html=True)

    nav_row(left=("🏠 홈으로 돌아가기", go_home, (), "se_home"),
            right=("학습 계속하기 ➔", next_step, (), "se_next"))


def screen_finale():
    inject_css(dark=True)

    st.markdown(
        "<h1 class='center' style='margin-top:2vh'>모든 별이 빛났어요!</h1>"
        "<p class='center' style='color:#ffe58a'>북두칠성이 완성됐어요. 정말 수고했어요!</p>",
        unsafe_allow_html=True
    )

    image_data = base64.b64encode(FINAL_BEARS_IMG.read_bytes()).decode("utf-8")

    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; align-items:center;">
            <img src="data:image/png;base64,{image_data}"
                 width="300"
                 style="display:block;">
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        dipper_html([True] * 7, all_lit=True, dark=True),
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:2vh'></div>", unsafe_allow_html=True)

    _, _, c1, c2 = st.columns([3, 3, 1.5, 1.5])
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


SAY_AS = {}
SAY_AS = {"street": "streeeet"}

@st.cache_data(show_spinner=False, ttl=60)
def audio_uri(w):
    data, mime = audio_bytes(w)
    return f"data:{mime};base64," + base64.b64encode(data).decode() if data else ""


def listen(words, lang="en-US", hide=False, max_per_row=4):
    """MP3를 우선 재생하고, 없으면 동일한 브라우저 TTS 음성을 사용합니다."""

    btns = "".join(
        f'<button data-t="{SAY_AS.get(w, w)}" data-a="{audio_uri(w)}" onclick="s(this)">🔊{" " + w if not hide else ""}</button>'
        for w in words
    )

    script = (
        "var selectedVoice = null;"

        "function loadVoice(){"
        "  var voices = speechSynthesis.getVoices();"
        "  var v = voices.filter(function(x){"
        "    return x.lang.replace('_','-').toLowerCase().indexOf('"
        + lang[:2].lower() +
        "') == 0;"
        "  });"
        "  if(v.length && !selectedVoice){"
        "    selectedVoice = v[0];"
        "  }"
        "}"

        "speechSynthesis.onvoiceschanged = loadVoice;"
        "loadVoice();"

        "function s(b){"
        "  speechSynthesis.cancel();"
        "  var a = b.dataset.a;"
        "  if(a && a.length > 20){"
        "    var audio = new Audio(a);"
        "    audio.play().catch(function(e){"
        "      fallbackTTS(b);"
        "    });"
        "    return;"
        "  }"
        "  fallbackTTS(b);"
        "}"

        "function fallbackTTS(b){"
        "  var u = new SpeechSynthesisUtterance(b.dataset.t);"
        "  console.log('읽는 문자열:', JSON.stringify(b.dataset.t));"
        "  u.lang = '" + lang + "';"
        "  u.rate = 0.7;"
        "  if(selectedVoice){"
        "    u.voice = selectedVoice;"
        "  }"
        "  speechSynthesis.speak(u);"
        "}"
    )

    doc = (
        "<style>body{margin:0}button{background:#7B1E2E;color:#fff;border:0;border-radius:12px;padding:10px 16px;"
        "margin:4px 6px 4px 0;font-size:16px;font-weight:600;white-space:nowrap;cursor:pointer}"
        "button:hover{background:#9a2a3d}</style>"
        + btns + "<script>" + script + "</script>"
    )

    h = 56 * max(1, -(-len(words) // max_per_row)) + 4
    tries = []

    if hasattr(st, "iframe"):
        tries.append(lambda: st.iframe(doc, height=h))

    tries.append(
        lambda: __import__("streamlit.components.v1", fromlist=["html"]).html(doc, height=h)
    )
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

    try:
        if gif_file.exists():
            st.image(
                str(gif_file),
                caption="⚡ /r/과 /l/ 발음 시 혀의 위치와 움직임",
                use_container_width=True
            )
        else:
            raise FileNotFoundError

    except Exception:
        st.markdown(
            tongue_svg("r") + tongue_svg("l"),
            unsafe_allow_html=True
        )
        st.caption("발음 도식: /r/은 혀끝이 윗잇몸에 닿지 않고, /l/은 혀끝이 윗잇몸에 닿아요.")

def tongue_svg(kind):
    kind = kind.lower()

    if kind == "l":
        title = "/l/ 발음"
        tongue = "M25 112 Q75 105 115 85 Q145 65 158 49 Q170 43 176 53 Q165 78 140 91 Q90 125 25 112"
        contact = '<circle cx="160" cy="51" r="5" fill="#7B1E2E"/>'
    else:
        title = "/r/ 발음"
        tongue = "M25 112 Q70 105 105 82 Q130 67 150 75 Q165 82 175 95 Q130 110 90 119 Q50 123 25 112"
        contact = '<path d="M150 55 L150 68" stroke="#D97706" stroke-width="2" stroke-dasharray="4 3"/>'

    return f"""
    <div style="display:inline-block; width:42%; max-width:220px;
                text-align:center; vertical-align:top; padding:4px;">
        <b style="color:#7B1E2E; font-size:16px;">{title}</b>
        <svg xmlns="http://www.w3.org/2000/svg"
             viewBox="0 0 210 150" width="100%">
            <path d="M20 55 Q95 12 190 48"
                  fill="none" stroke="#999" stroke-width="4"
                  stroke-linecap="round"/>
            <path d="M20 125 Q100 140 190 125"
                  fill="none" stroke="#999" stroke-width="3"/>
            <path d="{tongue}"
                  fill="#E88A8A" stroke="#7B1E2E" stroke-width="2"/>
            {contact}
        </svg>
    </div>
    """


def stretch(word, v, sc):
    m = 0.28 * (sc - 1)
    return word.replace(v, f"<span style='display:inline-block;transform:scaleX({sc});margin:0 {m:.2f}em'>{v}</span>", 1)


def big(html, size=2.4):
    return f"<div class='center' style='font-size:{size}rem;font-weight:800;color:{BURGUNDY};word-break:break-word;'>{html}</div>"



def eat_it_svg():
    c = BURGUNDY
    return ('<svg viewBox="0 0 420 210" width="100%" style="max-height:48vh">'
            f'<text x="20" y="95" font-size="100" font-weight="800" fill="{c}" textLength="250" lengthAdjust="spacingAndGlyphs">eat</text>'
            f'<text x="305" y="95" font-size="100" font-weight="800" fill="{c}" textLength="85" lengthAdjust="spacingAndGlyphs">it</text>'
            f'<line x1="20" y1="125" x2="270" y2="125" stroke="{c}" stroke-width="7" stroke-linecap="round"/>'
            f'<line x1="305" y1="125" x2="390" y2="125" stroke="{c}" stroke-width="7" stroke-linecap="round"/>'
            '<text x="145" y="165" text-anchor="middle" font-size="19" fill="#444">길게 · /iː/ · 입을 작게</text>'
            '<text x="347" y="165" text-anchor="middle" font-size="19" fill="#444">짧게 · /ɪ/</text></svg>')


# ------------------------------------------------------------------
# 7. 영어 트랙 내용
# ------------------------------------------------------------------
def rl_item(w, mean, pos, ipa, kind):
    if kind == "r":
        tip = "/r/은 혀끝이 윗잇몸에 닿지 않아요."
        wrong = "혀끝이 윗잇몸에 닿았을 수 있어요."
        ask = "혀끝이 윗잇몸에 닿지 않도록 다시 해 보세요."
        model = "혀를 입 안쪽으로 당기고 입술을 살짝 둥글게 만들어요."

    elif kind == "l":
        tip = "/l/은 혀끝이 윗잇몸에 닿아요."
        wrong = "혀끝이 윗잇몸에 닿지 않았을 수 있어요."
        ask = "혀끝을 윗잇몸에 닿게 다시 해 보세요."
        model = "혀끝을 윗잇몸에 붙인 채 소리를 내요."

    else:
        tip = "/r/과 /l/의 혀 위치를 구분해 보세요."
        wrong = "두 소리의 혀 위치가 명확하게 구분되지 않았어요."
        ask = "혀끝이 윗잇몸에 닿는지 확인해 보세요."
        model = "/r/은 닿지 않고, /l/은 닿아요."

    return dict(
        w=w, mean=mean, pos=pos, ipa=ipa,
        tip=tip, wrong=wrong, ask=ask, model=model
    )


RL_ITEMS = [
    rl_item("Right / Light", "오른쪽 / 빛", "1단계 (단어)", "/raɪt/ vs /laɪt/", "b"),
    rl_item("Rice / Lice", "쌀 / 이", "2단계 (단어)", "/raɪs/ vs /laɪs/", "b"),
    rl_item("Curriculum", "교육과정", "3단계 (단어 내부)", "/kəˈrɪkjələm/", "b"),
    rl_item("Charging bus card", "버스 카드 충전하기", "4단계 (구 단위)", "/ˈtʃɑːrdʒɪŋ bʌs kɑːrd/", "b"),
    rl_item("There are a lot of people.", "여기에는 많은 사람들이 있어요.", "5단계 (문장 단위)", "/ðɛr ɑːr ə lɒt əv ˈpiːpəl/", "b")
]


RL_PAGES = [
    dict(
        t="두 단어의 차이를 들어보세요!",
        lines=[
            "Right와 Light의 발음에서 어떤 소리가 더 입 안쪽에서 만들어질까요?",
            "**Right** /raɪt/ : 오른쪽",
            "**Light** /laɪt/ : 빛"
        ],
        words=["right", "light"],
        vis=lambda: (
            big("Right /raɪt/", 2.2)
            + "<p class='center'>오른쪽</p>"
            + big("Light /laɪt/", 2.2)
            + "<p class='center'>빛</p>"
        ),
        tab="소리 비교",
        tip="두 단어를 번갈아 듣고 /r/과 /l/의 차이를 찾아보세요."
    ),
    dict(
        t="발음 원리 이해하기",
        lines=[
            "**/l/ 발음**",
            "• 혀끝을 윗앞니 뒤쪽의 윗잇몸에 붙여요.",
            "• 공기가 혀의 양옆으로 빠져나가요.",
            "• 예시: light, lice, loud",
            "",
            "**/r/ 발음**",
            "• 혀끝이 윗잇몸에 닿지 않아요.",
            "• 혀끝을 살짝 말거나 혀 가운데를 뒤쪽으로 모아요.",
            "• 입술을 살짝 둥글게 만들 수 있어요.",
            "• 예시: right, rice, red"
        ],
        words=["right", "light"],
        vis=render_r_l_gif,
        tab="발음 원리",
        tip="/l/은 혀끝을 윗잇몸에 닿게 하고, /r/은 혀가 윗잇몸에 닿지 않도록 주의하세요."
    )
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
         vis=lambda: (
             "<div style='text-align:center; padding-top:15px; transform:translateY(-20px);'>"
             + big("e ?", 3.5) +
             "<p style='font-size:18px; color:#444; margin-top:8px;'>"
             "같은 e라도 단어마다 다른 소리를 낼 수 있어요."
             "</p></div>"
         )),
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
        border-radius:14px;padding:7px 16px;margin:2px 0 6px}
    .hd b{color:#fff !important}
    .pill{display:inline-block;padding:3px 12px;border-radius:999px;font-size:.85rem;
          margin-left:6px;background:#a0495a;color:#fff !important}
    .pill.on{background:#fff;color:#7B1E2E !important;font-weight:800}
    .tip{background:#fdf0f2;border-left:6px solid #7B1E2E;border-radius:10px;
         padding:7px 12px;margin:6px 0;color:#5a1522 !important}
    [data-testid="stVerticalBlockBorderWrapper"]{border:2px solid #ecd0d5 !important;
         border-radius:18px !important;background:#fffafb}

    /* 페이지 상하 여백 축소 */
    .block-container{
        padding-top:1.2rem !important;
        padding-bottom:1rem !important;
    }

    /* 요소 사이 간격 축소 */
    [data-testid="stVerticalBlock"]{
        gap:0.65rem;
    }
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
    image_data = base64.b64encode(HINT_BEAR_IMG.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div class='tip'>
            <img src="data:image/png;base64,{image_data}"
                 style="width:28px; height:auto; vertical-align:middle; margin-right:3px;">
            {P['tip']}
        </div>
        """,
        unsafe_allow_html=True
    )   
    
    nav_row(left=("← 이전", pg_move, (-1,), f"pv{pg}") if pg > 0 else None,
            right=("다음 →", pg_move, (1,), f"nx{pg}") if pg < n - 1 else ("개념 완료 ✓", finish_step, (), "cdone"))

def rl_item(w, mean, pos, kind):
    if kind == "r":
        tip, wrong = "r은 혀끝이 입천장에 닿지 않고 뒤로 말려요.", "l처럼 혀끝이 윗잇몸에 닿았어요."
        ask, model = "혀끝이 어디에 닿았나요? 닿지 않게 다시 해 볼까요?", "입술을 살짝 모으고 혀를 뒤로 당기며 시작해요."
    elif kind == "l":
        tip, wrong = "l은 혀끝이 윗잇몸에 닿아요.", "r처럼 혀끝이 닿지 않았어요."
        ask, model = "혀끝이 윗잇몸에 닿았나요? 다시 해 볼까요?", "혀끝을 윗잇몸에 딱 붙인 채 소리를 내요."
    else:
        tip, wrong = "r과 l을 구분해서 말해요.", "r과 l 중 일부가 같은 소리로 들렸어요."
        ask, model = "어느 소리가 r이고 어느 소리가 l인지 다시 확인해 볼까요?", "r은 혀를 말고, l은 혀끝을 윗잇몸에 붙여요."
    return dict(w=w, mean=mean, pos=pos, tip=tip, wrong=wrong, ask=ask, model=model)

RL_ITEMS = [
    rl_item("Right / Light", "오른쪽 / 빛", "1단계 (단어)", "b"),
    rl_item("Rice / Lice", "쌀 / 이", "2단계 (단어)", "b"),
    rl_item("Curriculum", "교육과정", "3단계 (단어 내부)", "b"),
    rl_item("Charging bus card", "버스 카드 충전", "4단계 (구 단위)", "b"),
    rl_item("There are a lot of people.", "사람이 많아요", "5단계 (문장 단위)", "b")
]

EI_PAIRS = [("bed", "침대", "/bɛd/", "bid", "입찰", "/bɪd/"), ("pen", "펜", "/pɛn/", "pin", "핀", "/pɪn/"),
            ("set", "놓다", "/sɛt/", "sit", "앉다", "/sɪt/"),
            ("pet", "반려동물", "/pɛt/", "pit", "구덩이", "/pɪt/"), ("bet", "내기", "/bɛt/", "bit", "조금", "/bɪt/")]
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
        if ss.lang == "en" and ss.step == 1:
            if ss.rl_sound == "r":
                st.warning(
                    "/r/: 혀끝을 윗잇몸에 닿지 않게 하고, "
                    "입술을 살짝 둥글게 만들어 보세요."
                )
            elif ss.rl_sound == "l":
                st.warning(
                    "/l/: 혀끝을 윗앞니 뒤 윗잇몸에 닿게 하고 "
                    "소리를 내 보세요."
                )
        else:
            st.warning(it["model"])


def highlight_rl(text):
    return re.sub(
        r"[rRlL]",
        lambda m: (
            f"<span style='color:{'#C62828' if m.group().lower() == 'r' else '#2878B8'};"
            " font-weight:900;'>"
            f"{m.group()}</span>"
        ),
        text
    )
def practice_rec(it, idx):
    # 단어 또는 문장
    st.markdown(
        f"<div style='font-size:2.2rem; text-align:center; font-weight:700;'>"
        f"{highlight_rl(it['w'])}</div>",
        unsafe_allow_html=True
    )

    # 뜻, 품사, IPA 구분
    st.markdown(
        f"""
        <div style="text-align:center; line-height:2;">
            <div>📖 뜻: {it['mean']}</div>
            <div>🏷️ 유형: {it['pos']}</div>
            <div>🔤 IPA: {it['ipa']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if it.get("q"):
        st.markdown(
            f"<p class='center'><b>{it['q']}</b></p>",
            unsafe_allow_html=True
        )


    # 엄마곰 옆 발음 들어보기 힌트
    hint_icon, hint_control = st.columns([0.45, 6], gap="small")

    with hint_icon:
        st.image(str(HINT_BEAR_IMG), width=42)

    with hint_control:
        with st.expander("힌트: 발음 들어보기"):

            if ss.lang == "ko":
                # 한국어 연습은 현재 문제의 단어 또는 문장 재생
                practice_audio = [it["w"]]
                audio_lang = "ko-KR"

            else:
                # 영어 연습은 기존 문제별 오디오 유지
                english_audio = {
                    0: ["right", "light"],
                    1: ["rice", "lice"],
                    2: ["curriculum"],
                    3: ["charging bus card"],
                    4: ["There are a lot of people."]
                }

                practice_audio = english_audio.get(idx, [it["w"]])
                audio_lang = "en-US"

            listen(
                practice_audio,
                audio_lang,
                hide=False
            )

    # 녹음 및 채점
    st.markdown("**녹음하기**")

    if ss.lang == "en" and ss.step == 1 and idx in [0, 1]:
        selected_sound = st.radio(
            "연습할 발음 선택",
            ["/r/", "/l/"],
            horizontal=True,
            index=0 if ss.rl_sound == "r" else 1,
            key="rl_sound_choice"
        )

        new_sound = "r" if selected_sound == "/r/" else "l"

        if new_sound != ss.rl_sound:
            ss.rl_sound = new_sound
            ss.ps = {}
            ss.rnd += 1
            st.rerun()

    a = st.audio_input(
        "녹음하기",
        key=f"a{ss.step}_{idx}_{ss.rnd}",
        label_visibility="collapsed"
    )

    if not a:
        return False

    if ss.lang == "ko":
        # 한국어: 녹음 후 일치율 표시
        s, _ = score_audio(a, bump(1, 0.7))
        ss.ps[idx] = s

        st.success(f"녹음이 완료되었어요! 일치율: {s}%")

    else:
        # 영어: 기존 파형 비교 채점 유지
        s, _ = score_audio(a, bump(1, 0.7))
        ss.ps[idx] = s
        ss.rl_scores[ss.rl_sound][idx] = s
        feedback(s, it)

    if it.get("checks"):
        st.markdown(
            "**확인할 항목:** " +
            " · ".join("☐ " + c_ for c_ in it["checks"])
        )

    return True



def practice_pair(it, idx):
    k = f"{ss.step}_{idx}_{ss.rnd}"

    # 곰돌이 힌트와 발음 듣기
    hint_icon, hint_control = st.columns([0.7, 6])

    with hint_icon:
        st.image(str(HINT_BEAR_IMG), width=48)

    with hint_control:
        hint = st.toggle(
            "힌트: 발음 들어보기",
            key=f"h{k}"
        )

    if hint:
        listen([p[0] for p in it["p"]], "en-US", hide=False)

    # 두 단어를 나란히 카드로 제시
    col1, col2 = st.columns(2)

    for j, col in enumerate([col1, col2]):
        w, mean, _, v = it["p"][j]

        with col:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #ddd;
                    border-radius: 14px;
                    padding: 20px 8px;
                    text-align: center;
                    min-height: 110px;
                ">
                    <div style="font-size: 2rem; font-weight: 700;">{w}</div>
                    <div style="margin-top: 8px;">{mean}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # 녹음할 단어 선택
    tgt = st.radio(
        "녹음할 단어",
        [0, 1],
        format_func=lambda j: f"{it['p'][j][0]} ({it['p'][j][1]})",
        horizontal=True,
        key=f"r{k}"
    )

    w, mean, _, v = it["p"][tgt]
    hi = v == "i"

    rt = bump(0.9 if hi else 0.55, 0.5 if hi else 0.7)
    rm = bump(0.35 if hi else 0.8, 0.5 if hi else 0.7)

    a = st.audio_input("녹음하기", key=f"a{k}_{tgt}")

    if not a:
        return False

    s, e = score_audio(a, rt)
    ss.ps[idx] = s


    it2 = dict(
        wrong="모음 길이와 입 모양이 목표와 달랐어요.",
        ask="이 단어의 모음이 길어야 할까요, 짧아야 할까요?",
        model="긴 모음은 충분히 길게, 짧은 모음은 짧고 분명하게 발음해요."
    )

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






def render_practice(items, fn):
    slide_css()
    if ss.pact is None:
        ss.pact, ss.pi, ss.ps = list(range(len(items))), 0, {}

    act = ss.pact


    def redo(indices):
        ss.pact = list(indices)
        ss.pi = 0
        ss.ps = {}

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
    if ss.lang == "en" and items is RL_ITEMS:
        header("r/l 발음 - 듣고 말하기", [str(k + 1) for k in range(len(act))], ss.pi)
    else:
        header(("영어" if ss.lang == "en" else "한국어") + " 발음 교실 · 연습", [str(k + 1) for k in range(len(act))], ss.pi)

    with st.container(border=True):
        done = fn(items[idx], idx)

    it = items[idx]
    tip = it.get("tip") or ("두 단어의 모음 길이와 혀 높이를 비교해 봐요." if "p" in it else "모음 소리 하나가 음절 하나예요.")

    image_data = base64.b64encode(HINT_BEAR_IMG.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div class='tip'>
            <img src="data:image/png;base64,{image_data}"
                 style="width:28px; height:auto; vertical-align:middle; margin-right:3px;">
            유의할 점: {tip}
        </div>
        """,
        unsafe_allow_html=True
    )

    if done:
        _, right = st.columns([8, 2])

        with right:
            st.button(
                "다음으로 →",
                on_click=adv,
                key=f"next_{ss.step}_{ss.pi}",
                use_container_width=True
            )
    else:
        _, right = st.columns([8, 2])

        with right:
            st.button(
                "건너뛰기",
                on_click=adv,
                key=f"skip_{ss.step}_{ss.pi}",
                use_container_width=True
            )

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

def tissue_svg(title, strength, description):
    # strength에 따라 휴지가 휘어지는 정도 조절
    movement = max(0, min(60, strength))
    bend = movement * 0.45

    return f"""
    <div style="
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 6px;
        margin: 4px 0;
        text-align: center;
        background: #ffffff;
    ">
        <div style="
            font-weight: 700;
            margin-bottom: 8px;
            color: #333333;
        ">
            {title}
        </div>

        <svg viewBox="0 0 320 125"
             width="100%"
             style="max-height:90px;">

            <!-- 입에서 나오는 공기 -->
            <path d="M35 60 Q65 60 90 60"
                  fill="none"
                  stroke="#999"
                  stroke-width="3"
                  stroke-dasharray="5 5"/>

            <!-- 공기 흐름 표시 -->
            <path d="M75 52 L90 60 L75 68"
                  fill="none"
                  stroke="#999"
                  stroke-width="2"/>

            <!-- 휴지 -->
            <path d="
                M110 15
                Q{110 + 20 + bend} 35 {110 + 20 + bend} 60
                Q{110 + 20 + bend} 85 {115 + 20 + bend} 108
                L{140 + bend} 108
                Q{135 + bend} 75 {140 + bend} 15
                Z"
                fill="#f5f5f5"
                stroke="#999"
                stroke-width="2"/>

            <!-- 움직임 표시 -->
            <path d="
                M65 35 L85 35
                M65 60 L85 60
                M65 85 L85 85"
                stroke="#aaa"
                stroke-width="2"
                stroke-linecap="round"/>
        </svg>

        <div style="
            font-size:0.9rem;
            color:#666;
            margin-top:4px;
        ">
            {description}
        </div>
    </div>
    """


KO_CONS_PAGES = [
    dict(t="평음과 격음, 바람 세기가 달라요",
         lines=["**평음** ㅂ ㄷ ㄱ ㅈ ㅅ: 바람이 약하고 성대가 부드럽게 울려요.",
                "**격음** ㅍ ㅌ ㅋ ㅊ: 바람이 강하게 터져 나와요.",
                "입 앞에 손가락이나 휴지를 대고 발음해 차이를 느껴 보세요."],
         words=["바다", "파다"],
         vis=lambda: (
             "<div style='display:flex; gap:10px; width:100%;'>"
             + "<div style='flex:1; min-width:0;'>"
             + tissue_svg("평음 (바다)", 10, "휴지가 살짝 움직여요")
             + "</div>"
             + "<div style='flex:1; min-width:0;'>"
             + tissue_svg("격음 (파다)", 55, "휴지가 크게 날려요")
             + "</div>"
             + "</div>"
         )),
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

    dict(
        tab="바다 / 파다",
        t="바다 / 파다",
        lines=["두 단어의 첫소리에 집중해서 들어 보세요."],
        pair=("바다", "파다"),
        words=["바다", "파다"],
        contrast="ㅂ ↔ ㅍ",
        tip="ㅂ은 평음, ㅍ은 격음이에요."
    ),

    dict(
        tab="비다 / 피다",
        t="비다 / 피다",
        lines=["첫소리의 차이에 따라 단어의 의미가 달라져요."],
        pair=("비다", "피다"),
        words=["비다", "피다"],
        contrast="ㅂ ↔ ㅍ",
        tip="두 단어의 첫 자음에서 바람의 세기를 비교해 보세요."
    ),

    dict(
        tab="달 / 탈",
        t="달 / 탈",
        lines=["첫 자음의 발음 차이를 구별해 보세요."],
        pair=("달", "탈"),
        words=["달", "탈"],
        contrast="ㄷ ↔ ㅌ",
        tip="ㄷ은 평음, ㅌ은 격음이에요."
    ),

    dict(
        tab="자다 / 차다",
        t="자다 / 차다",
        lines=["두 단어를 번갈아 들으며 첫소리를 비교해 보세요."],
        pair=("자다", "차다"),
        words=["자다", "차다"],
        contrast="ㅈ ↔ ㅊ",
        tip="ㅈ과 ㅊ의 바람 세기 차이에 집중해 보세요."
    )
]

KO_VOW_PAGES = [
    dict(
        tab="모음 체계",
        t="먼저, 두 언어의 모음은 어떻게 다를까요?",
        lines=[
            "일본어 「う」는 입술을 강하게 둥글게 하지 않아요.",
            "한국어 모음은 혀의 앞뒤·높이와 입술 모양에 따라 달라져요.",
            "일본어 「う」와 한국어 ㅜ는 비슷하지만 입술 모양에 차이가 있어요.",
            "각 모음을 눌러 소리를 들어 보세요."
        ],
        words=["이", "으", "우", "에", "어", "오", "아"],
        vis=vowel_svg
    ),
    dict(
        tab="모음 비교",
        t="모음 비교하기",
        cards=["굴", "글"]
    ),
    dict(
        tab="모음 비교",
        t="모음 비교하기",
        cards=["곰", "검", "금"]
    ),
    dict(
        tab="이중모음",
        t="이중모음",
        cards=["과일", "원", "왜", "웨이터", "의사", "의자"]
    ),
    dict(
        tab="기타 모음",
        t="기타 모음",
        cards=["예", "세계"]
    ),
]

def syllable_visual(content, font_size=42, move_y=0):
    return f"""
    <div style="
        width:100%;
        height:220px;
        display:flex;
        align-items:center;
        justify-content:center;
        box-sizing:border-box;
    ">
        <div style="
            transform:translate(25px, {move_y}px);
            text-align:center;
            color:#7B1E2E;
            font-size:{font_size}px;
            font-weight:800;
            line-height:1.6;
            letter-spacing:2px;
        ">
            {content}
        </div>
    </div>
    """
KO_SYL_PAGES = [
    dict(t="받침의 종류를 구분해 봐요",
         lines=["일본어 ん은 하나지만 한국어 받침은 셋이에요.", "**감** 입술이 닫혀요 · **간** 혀끝이 윗잇몸 · **강** 혀뿌리가 올라가요"],
         words=["감", "간", "강"],
         vis=lambda: syllable_visual("감 · 간 · 강", 44, -35)),

    dict(t="한국어의 음절 리듬을 이해해 봐요",
         lines=["일본어는 모라를 중심으로 리듬을 인식하지만,",
                "한국어는 음절을 중심으로 리듬을 형성해요.",
                "한국어의 음절 단위를 인식하는 것이 중요해요.",
                "일본어 パン · かん처럼 ん으로 끝나는 말과 비교해 봐요."],
         words=["사랑", "친구", "공부"],
         vis=lambda: syllable_visual(
             "사 · 랑<br>친 · 구<br>공 · 부<br><span style='font-size:30px;'>2음절</span>",
             34, -20
         )),
]
for _pages, _tabs, _tips in (
    (KO_CONS_PAGES, ["바람 세기", "조음 위치", "바다 / 파다", "비다 / 피다", "달 / 탈", "자다 / 차다"], ["평음은 약하게, 격음은 강하게 바람을 내요.", "혀와 입술이 닿는 위치를 정확히 지켜요.", "소리 하나 차이로 뜻이 달라져요.", "첫소리의 차이를 구별해 보세요.", "평음과 격음의 차이를 들어 보세요.", "두 자음의 바람 세기를 비교해 보세요."]),
    (KO_VOW_PAGES, ["도입", "모음 비교"], ["일본어 う와 한국어 ㅜ는 입술 모양이 달라요.", "활음(/w/)이 약해지거나 바뀌지 않게 주의해요."]),
    (KO_SYL_PAGES, ["받침 구분", "박자"], ["받침 소리가 끝나는 위치를 느껴 봐요.", "한 글자는 한 박자로 읽어요."]),
):
    for _p, _t, _tip in zip(_pages, _tabs, _tips):
        _p["tab"], _p["tip"] = _t, _tip


def ko_item(w, mean, pos, tip, q="", checks=None):
    return dict(
        kind="rec", lang="ko-KR",
        w=w, mean=mean, pos=pos,
        tip=tip, q=q, checks=checks,
        wrong=f"{tip} 부분이 목표와 달랐어요.",
        ask="어디가 달랐는지 다시 들어 보고 해 볼까요?",
        model=tip
    )


def ko_listen(say, opts, tip):
    ans = next(
        i for i, o in enumerate(opts)
        if o.strip().split()[-1] == say.strip()
    )
    return dict(
        kind="listen",
        w=say,
        say=say,
        opts=opts,
        ans=ans,
        tip=tip
    )


def ko_pair(a, b, tip, cons=False, checks=None):
    return dict(kind="pair", p=[a, b], tip=tip, cons=cons, checks=checks)


VCHK = ["입술의 원순성", "혀의 높이", "활음의 연결 여부"]

KO_CONS_ITEMS = [
    ko_listen(s_, o_, "평음은 바람이 약하고, 격음은 바람이 강해요.")
    for s_, o_ in (
        ("가", ["ㄱ  가", "ㅋ  카"]),
        ("타", ["ㄷ  다", "ㅌ  타"]),
        ("바", ["ㅂ  바", "ㅍ  파"]),
        ("차", ["ㅈ  자", "ㅊ  차"]),
        ("카", ["ㄱ  가", "ㅋ  카"]),
        ("다", ["ㄷ  다", "ㅌ  타"]),
        ("파", ["ㅂ  바", "ㅍ  파"]),
        ("자", ["ㅈ  자", "ㅊ  차"])
    )
] + [
    ko_pair(
        ("바다", "넓고 짠물이 있는 곳（海）"),
        ("파다", "땅에 구멍을 내다（掘る）"),
        "격음 ㅍ은 입 앞 손가락에 센 바람이 느껴져요.", True
    ),
    ko_pair(
        ("비다", "속이 없다（空いている・中身がない）"),
        ("피다", "꽃이 열리다（花が咲く）"),
        "격음 ㅍ은 입술을 터뜨리며 센 바람을 내요.", True
    ),
    ko_pair(
        ("달", "하늘의 달（月）"),
        ("탈", "얼굴에 쓰는 탈（仮面）"),
        "ㅌ은 더 센 바람이 나와요.", True
    ),
    ko_pair(
        ("자다", "잠을 자다（寝る）"),
        ("차다", "발로 차다（蹴る）"),
        "ㅊ은 더 센 바람이 나와요.", True
    ),
    ko_pair(
        ("불", "타는 불（火）"),
        ("풀", "자라는 풀（草）"),
        "ㅍ은 센 바람을 내요.", True
    ),
]
KO_VOW_ITEMS = [
    ko_pair(
        ("굴", "굴（カキ）"),
        ("글", "글（文章）"),
        "ㅜ는 입술을 둥글게 오므려요.", checks=VCHK
    ),
    ko_pair(
        ("곰", "곰（クマ）"),
        ("검", "칼（剣）"),
        "ㅗ는 입술을 둥글게, ㅓ는 입을 더 열어요.", checks=VCHK
    ),
    ko_pair(
        ("곰", "곰（クマ）"),
        ("금", "금（金）"),
        "ㅗ는 입술을 둥글게, ㅡ는 둥글게 하지 않아요.", checks=VCHK
    ),
    ko_pair(
        ("검", "칼（剣）"),
        ("금", "금（金）"),
        "ㅓ는 입을 열고 ㅡ는 입술을 펴요.", checks=VCHK
    ),

    ko_item("과일", "과일（果物）", "명사",
            "ㅘ의 첫 입술소리가 사라지지 않게 해요.",
            "입술 모양이 자연스럽게 이어지나요?", VCHK),
    ko_item("원", "동그라미（円）", "명사",
            "첫 입술소리가 분명하게 들리게 해요.",
            "첫소리가 분명하게 들리나요?", VCHK),
    ko_item("왜", "어째서（なぜ）", "부사",
            "두 소리가 끊기지 않고 이어지게 해요.",
            "두 소리가 끊기지 않나요?", VCHK),
    ko_item("웨이터", "식당 종업원（ウェイター）", "명사",
            "입 모양이 자연스럽게 바뀌게 해요.",
            "입 모양이 자연스럽게 바뀌나요?", VCHK),
    ko_item("의사", "의사（医者）", "명사",
            "ㅢ의 첫소리가 다른 소리로 바뀌지 않게 해요.",
            "첫소리를 정확하게 발음했나요?", VCHK),
    ko_item("저는 손이 커요", "손이 크다는 표현（私は手が大きいです）", "문장",
            "ㅓ와 ㅗ를 구분해요.",
            "최종 미션: 문장 발음하기 (먼저 목표 단어를 하나씩 연습해요)", VCHK),
]

KO_SYL_ITEMS = [
    ko_item("감", "감（柿）", "명사", "ㅁ: 입술을 닫고 끝내요."),
    ko_item("간", "간（肝臓）", "명사", "ㄴ: 혀끝을 윗잇몸에 대요."),
    ko_item("강", "강（川）", "명사", "ㅇ: 혀뿌리를 올리고 입은 열어요."),
    ko_item("밤", "밤（栗）", "명사", "ㅁ: 입술을 닫고 끝내요."),
    ko_item("방", "방（部屋）", "명사", "ㅇ: 입은 열고 코로 소리를 내요."),
    ko_item("사랑", "사랑（愛）", "명사", "한 글자를 한 박자로 읽어요."),
    ko_item("친구", "친구（友達）", "명사", "ㄴ 받침이 별도 박자가 되지 않게 해요.")
]

KO_SYL_ITEMS.append(
    ko_item(
        "저는 감이 좋아요",
        "감이 좋다는 표현（柿が好きだという表現）",
        "문장",
        "받침 소리를 구분해 이어 읽어요."
    )
)


def retry():
    ss.rnd += 1


def practice_ko(it, idx):
    k = f"{ss.step}_{idx}_{ss.rnd}"

    if it["kind"] == "rec":
        return practice_rec(it, idx)

    if it["kind"] == "listen":
        st.markdown(
            big("🎧 듣고 고르기", 2)
            + "<p class='center'>들린 첫소리와 같은 자음을 골라요. 실수하면 한 번 더 들어 봐요.</p>",
            unsafe_allow_html=True
        )
        listen([it["say"]], "ko-KR", hide=True)

        c = st.radio(
            "들린 소리를 고르세요",
            it["opts"],
            index=None,
            key=f"q{k}",
            horizontal=True
        )

        if c is None:
            return False

        ok = c == it["opts"][it["ans"]]
        ss.ps[idx] = 100 if ok else 0
        (st.success if ok else st.error)(
            ("정답이에요! " if ok else "아쉬워요. ")
            + f"정답은 {it['opts'][it['ans']]}이에요. {it['tip']}"
        )
        return True

    st.markdown(
        "".join(big(p[0], 2.2) + f"<p class='center'>{p[1]}</p>" for p in it["p"]),
        unsafe_allow_html=True
    )

    # 엄마곰 옆 발음 듣기 힌트
    hint_icon, hint_control = st.columns([0.45, 6], gap="small")

    with hint_icon:
        st.image(str(HINT_BEAR_IMG), width=42)

    with hint_control:
        with st.expander("힌트: 발음 들어보기"):
           listen([p[0] for p in it["p"]], "ko-KR", hide=False)

    if it.get("cons"):
        if not st.checkbox(
            "✓ 뜻을 확인했어요 (확인한 뒤 녹음해요)",
            key=f"m{k}"
        ):
            return False

        st.info(
            "기식 확인: 입 앞에 손가락을 대고 약한 공기(평음), 강한 공기(격음)를 느껴 보세요. "
        )

    t = st.radio(
        "녹음할 단어",
        [0, 1],
        format_func=lambda j: it["p"][j][0],
        horizontal=True,
        key=f"r{k}"
    )

    a = st.audio_input("녹음하기", key=f"a{k}_{t}")

    if not a:
        return False

    s, e = score_audio(a, bump(1, 0.6))
    ss.ps[idx] = s


    feedback(
        s,
        dict(
            wrong="목표 소리와 달랐어요.",
            ask="입 모양과 바람을 다시 확인하고 해 볼까요?",
            model=it["tip"]
        )
    )

    if it.get("checks"):
        st.markdown(
            "**확인할 항목:** " + " · ".join("☐ " + c_ for c_ in it["checks"])
        )

    st.button("다시 발음하기", on_click=retry, key=f"rt{k}")
    return True


def render_ko(i):
    if i == 0: render_concept(KO_CONS_PAGES, "ko-KR")
    elif i == 1: render_practice(KO_CONS_ITEMS, practice_ko)
    elif i == 2: render_concept(KO_VOW_PAGES, "ko-KR")
    elif i == 3: render_practice(KO_VOW_ITEMS, practice_ko)
    elif i == 4: render_concept(KO_SYL_PAGES, "ko-KR")
    elif i == 5: render_practice(KO_SYL_ITEMS, practice_ko)


def ko_articulation_svg():
    return """
    <div style="width:100%; background:#FFF9FA; border-radius:14px; padding:8px;">
    <svg viewBox="0 0 540 370" width="100%" xmlns="http://www.w3.org/2000/svg">
        <rect x="1" y="1" width="538" height="368" rx="14"
              fill="#FFF9FA" stroke="#E8D5DA"/>

        <text x="270" y="27" text-anchor="middle"
              font-size="18" font-weight="bold" fill="#7B1E2E">
            한국어 발음기관의 단면
        </text>

        <!-- 입천장과 구강 -->
        <path d="M105 105 Q145 65 225 72 Q310 73 365 112
                 Q390 130 400 160"
              fill="none" stroke="#B87983" stroke-width="13"
              stroke-linecap="round"/>

        <!-- 코와 인두 -->
        <path d="M105 105 Q65 92 55 125 Q50 148 90 158"
              fill="#F3D5D8" stroke="#B87983" stroke-width="2"/>

        <!-- 입술과 치아 -->
        <path d="M105 105 Q90 118 104 137 L130 143"
              fill="none" stroke="#B87983" stroke-width="9"
              stroke-linecap="round"/>
        <path d="M126 119 L143 126 L139 148 L122 141 Z"
              fill="white" stroke="#9B777B" stroke-width="2"/>
        <path d="M145 126 L160 130 L155 150 L140 146 Z"
              fill="white" stroke="#9B777B" stroke-width="2"/>

        <!-- 혀 -->
        <path d="M135 205 Q175 165 235 169
                 Q300 171 350 210 Q365 224 378 238
                 Q310 250 250 238 Q190 230 135 205"
              fill="#D98D98" stroke="#A64F60" stroke-width="3"/>

        <!-- 인두와 목청 -->
        <path d="M400 160 Q420 205 405 260 Q395 290 370 310"
              fill="none" stroke="#B87983" stroke-width="13"
              stroke-linecap="round"/>
        <path d="M380 270 Q395 280 385 300"
              fill="none" stroke="#7B1E2E" stroke-width="4"/>

        <!-- 조음 위치 표시 -->
        <g fill="#7B1E2E" stroke="white" stroke-width="2">
            <circle cx="112" cy="132" r="7"/>
            <circle cx="151" cy="139" r="7"/>
            <circle cx="185" cy="91" r="7"/>
            <circle cx="285" cy="84" r="7"/>
            <circle cx="390" cy="286" r="7"/>
        </g>

        <!-- 설명 선과 라벨 -->
        <g stroke="#7B1E2E" stroke-width="1.5" fill="none">
            <path d="M112 132 L65 175 L18 175"/>
            <path d="M151 139 L150 185 L115 185"/>
            <path d="M185 91 L205 48 L245 48"/>
            <path d="M285 84 L320 48 L360 48"/>
            <path d="M390 286 L430 286 L430 310"/>
        </g>

        <g font-size="13" fill="#57202B" font-weight="bold">
            <text x="15" y="169">입술</text>
            <text x="95" y="200">윗니·잇몸</text>
            <text x="248" y="49">센입천장</text>
            <text x="363" y="49">여린입천장</text>
            <text x="435" y="314">목청</text>
            <text x="245" y="211" text-anchor="middle">혀</text>
            <text x="270" y="345" text-anchor="middle"
                  font-size="12" font-weight="normal">
                공기가 지나가는 입안의 구조를 옆에서 본 모습
            </text>
        </g>
    </svg>
    </div>
    """


def render_concept(pages, lang="en-US"):
    slide_css()
    n = len(pages)
    pg = min(ss.page, n - 1)
    P = pages[pg]

    if pages is KO_VOW_PAGES:
        header(
            ("영어" if ss.lang == "en" else "한국어") + " 발음 교실",
            [str(k + 1) for k in range(n)],
            pg
        )
    else:
        header(
            ("영어" if ss.lang == "en" else "한국어") + " 발음 교실",
            [f"{k + 1:02d} {q['tab']}" for k, q in enumerate(pages)],
            pg
        )
    with st.container(border=True):
        st.markdown(
            f"<h2 style='color:{BURGUNDY};margin:0 0 6px'>{P['t']}</h2>",
            unsafe_allow_html=True
        )
        if P.get("cards"):
            words = P["cards"]
            cols_per_row = 2 if len(words) == 2 else 3

            for start in range(0, len(words), cols_per_row):
                row_words = words[start:start + cols_per_row]
                cols = st.columns(cols_per_row, gap="medium")

                for col, word in zip(cols, row_words):
                    with col:
                        with st.container(border=True):
                            st.markdown(
                                f"""
                                <div style="
                                    min-height:85px;
                                    display:flex;
                                    align-items:center;
                                    justify-content:center;
                                    text-align:center;
                                    font-size:32px;
                                    font-weight:800;
                                    color:{BURGUNDY};
                                ">
                                    {word}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            listen([word], lang)

        elif P.get("pair"):
            st.markdown(
                f"<h3 style='text-align:center;color:{BURGUNDY};'>{P['contrast']}</h3>",
                unsafe_allow_html=True
            )

            for line in P["lines"]:
                st.markdown(line)

            left, right = st.columns(2, gap="medium")

            for col, word, consonant in [
                (left, P["pair"][0], P["contrast"].split("↔")[0].strip()),
                (right, P["pair"][1], P["contrast"].split("↔")[1].strip())
            ]:
                with col:
                    with st.container(border=True):
                        st.markdown(
                            f"""
                            <div style="text-align:center; padding:15px 5px;">
                                <div style="font-size:30px; font-weight:800; color:{BURGUNDY};">
                                    {word}
                                </div>
                                <div style="background:#F5E8EC; color:{BURGUNDY};
                                            padding:5px 12px; border-radius:20px;
                                            display:inline-block; margin-top:8px;">
                                    {consonant}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        listen([word], lang)

        elif callable(P.get("vis")) or P.get("words"):
            L, R = st.columns([5, 6])

            is_ko_position = (
                pages is KO_CONS_PAGES
                and P.get("t") == "소리가 만들어지는 위치 (조음 위치)"
            )

            with L:
                for line in P.get("lines", []):
                    st.markdown(line)

                if not is_ko_position:
                    listen(P.get("words", []), lang)

            with R:
                if is_ko_position:
                    components.html(
                        ko_articulation_svg(),
                        height=370,
                        scrolling=False
                    )
                elif pages is RL_PAGES:
                    st.markdown(
                        "<div style='text-align:center; margin-bottom:8px;'>"
                        "<b style='color:#7B1E2E; font-size:18px;'>혀의 위치</b>"
                        "</div>",
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        tongue_svg("r") + tongue_svg("l"),
                        unsafe_allow_html=True
                    )
                    st.caption(
                        "/r/은 혀끝이 윗잇몸에 닿지 않고, "
                        "/l/은 혀끝이 윗잇몸에 닿아요."
                    )
                elif callable(P.get("vis")):
                    html_content = P["vis"]()

                    visual_height = 320 if pages is EI_PAGES else 220

                    components.html(
                        html_content,
                        height=visual_height,
                        scrolling=False
                    )

    # R/L 첫 번째 화면에만 확인 질문 표시
    if pages is RL_PAGES and pg == 0:
        st.markdown("### 🔎 소리 구별하기")
        st.write("Right와 Light 중 어떤 소리가 더 입 안쪽에서 만들어질까요?")

        with st.form("rl_concept_question"):
            answer = st.radio(
                "정답을 선택하세요.",
                ["/r/ (Right)", "/l/ (Light)"],
                index=None
            )
            submitted = st.form_submit_button("정답 확인")

        if submitted:
            if answer == "/r/ (Right)":
                st.success(
                    "맞아요! /r/은 혀가 윗잇몸에 닿지 않고 "
                    "입 안쪽에서 만들어져요."
                )
            elif answer == "/l/ (Light)":
                st.error(
                    "다시 확인해 보세요. /r/은 혀끝이 윗잇몸에 닿지 않고 "
                    "더 안쪽에서 만들어져요."
                )
            else:
                st.warning("답을 선택해 주세요.")

    image_data = base64.b64encode(HINT_BEAR_IMG.read_bytes()).decode("utf-8")

    if P.get("tip"):
        st.markdown(
            f"""
            <div class='tip'>
                <img src="data:image/png;base64,{image_data}"
                     style="width:28px; height:auto; vertical-align:middle; margin-right:3px;">
                {P['tip']}
            </div>
            """,
            unsafe_allow_html=True
        )

    nav_row(
        left=("← 이전", pg_move, (-1,), f"pv{pg}") if pg > 0 else None,
        right=("다음 →", pg_move, (1,), f"nx{pg}")
        if pg < n - 1
        else ("개념 완료 ✓", finish_step, (), "cdone")
    )


def render_en(i):
    if i == 0:
        render_concept(RL_PAGES)
    elif i == 1:
        render_practice(RL_ITEMS, practice_rec)
    elif i == 2:
        render_concept(EI_PAGES)
    elif i == 3:
        render_practice(EI_ITEMS, practice_pair)
    elif i == 4:
        render_syllable_concepts()
    elif i == 5:
        render_syllable_practice()

def render_syllable_concepts():
    slide_css()

    types = ["cluster", "stress", "count"]
    type_index = ss.get("syl_concept_type_index", 0)
    page_index = ss.get("syl_concept_page_index", 0)

    module = SYL_MODULES[types[type_index]]
    pages = module["pages"]
    page = pages[page_index]

    # 기존 페이지와 같은 상단 헤더
    header(
        "영어 발음 교실",
        [f"{i + 1:02d} {SYL_MODULES[t]['title']}" for i, t in enumerate(types)],
        type_index
    )

    # 기존 페이지와 같은 테두리 컨테이너
    with st.container(border=True):

        st.markdown(
            f"<h2 style='color:{BURGUNDY};margin:0 0 6px'>{page['heading']}</h2>",
            unsafe_allow_html=True
        )



        L, R = st.columns([5, 6], gap="small")

        with L:
            st.markdown(page["text"])

            st.markdown("**예시 단어**")
            listen(page["words"], "en-US", max_per_row=3)


        with R:
            st.markdown(
                f"""
                <div style="
                    background:#fdf0f2;
                    border-left:5px solid {BURGUNDY};
                    border-radius:10px;
                    padding:12px 16px;
                    color:#5a1522;
                    font-size:16px;
                    line-height:1.6;
                ">
                    <b style="color:{BURGUNDY};">핵심 내용</b><br>
                    {page['focus']}
                </div>
                """,
                unsafe_allow_html=True
            )


    # 기존 페이지와 같은 하단 이동 버튼
    st.divider()

    left, right = st.columns([5, 1])

    with left:
        if type_index > 0 or page_index > 0:
            if st.button("← 이전 내용"):
                if page_index > 0:
                    ss.syl_concept_page_index -= 1
                else:
                    ss.syl_concept_type_index -= 1
                    previous_type = types[ss.syl_concept_type_index]
                    ss.syl_concept_page_index = (
                        len(SYL_MODULES[previous_type]["pages"]) - 1
                    )
                st.rerun()

    with right:
        if page_index < len(pages) - 1:
            if st.button("다음 내용 →", use_container_width=True):
                ss.syl_concept_page_index += 1
                st.rerun()

        elif type_index < len(types) - 1:
            if st.button("다음 개념 →", use_container_width=True):
                ss.syl_concept_type_index += 1
                ss.syl_concept_page_index = 0
                st.rerun()

        else:
            if st.button("개념 학습 완료 →", use_container_width=True):
                finish_step()
                st.rerun()


def render_syllable_practice():
    slide_css()

    type_order = ["cluster", "stress", "count"]

    type_titles = {
        "cluster": "자음 연결",
        "stress": "음절 강세",
        "count": "실제 발음에 따른 음절 구분",
    }

    questions = [
        (type_key, item)
        for type_key in type_order
        for item in SYL_QUIZZES[type_key]
    ]

    practice_words = {
        "cluster": ["school", "spring", "street"],
        "stress": ["banana", "computer", "important"],
        "count": ["cup", "comb", "speak"],
    }

    words = [
        (type_key, word)
        for type_key in type_order
        for word in practice_words[type_key]
    ]

    phase = ss.get("syl_page", "quiz")

    # 현재 학습 유형에 맞춰 상단 헤더 표시
    if phase == "quiz":
        current_type = questions[ss.syl_quiz_index][0]
    elif phase == "practice":
        current_type = words[ss.syl_practice_index][0]
    else:
        current_type = "count"

    type_index = type_order.index(current_type)

    header(
        "영어 발음 교실",
        [f"{i + 1:02d} {type_titles[t]}" for i, t in enumerate(type_order)],
        type_index
    )

    with st.container(border=True):

        st.markdown(
            f"<h2 style='color:{BURGUNDY};margin:0 0 6px'>음절 통합 연습</h2>",
            unsafe_allow_html=True
        )

        # ① 개념 확인 퀴즈
        if phase == "quiz":
            idx = ss.syl_quiz_index
            type_key, item = questions[idx]

            L, R = st.columns([5, 6], gap="medium")

            with L:
                st.markdown("### ① 개념 확인 퀴즈")
                st.caption(
                    f"{idx + 1} / 9 문제 · {type_titles[type_key]}"
                )
                st.markdown(f"**Q. {item['q']}**")

                if not ss.syl_submitted:
                    choice = st.radio(
                        "정답을 선택하세요.",
                        range(len(item["opts"])),
                        format_func=lambda x: item["opts"][x],
                        index=None,
                        key=f"syl_all_quiz_choice_{idx}"
                    )

                    if st.button("답 제출", key=f"syl_all_submit_{idx}"):
                        if choice is None:
                            st.warning("정답을 먼저 선택해 주세요.")
                        else:
                            ss.syl_answers[idx] = choice
                            ss.syl_submitted = True
                            st.rerun()

                else:
                    answer = ss.syl_answers[idx]

                    if answer == item["ans"]:
                        st.success("정답이에요!")
                    else:
                        st.error("아쉽지만 정답이 아니에요.")

                    st.info(item["why"])

            with R:
                st.markdown(
                    f"""
                    <div style="
                        background:#fdf0f2;
                        border-left:5px solid {BURGUNDY};
                        border-radius:10px;
                        padding:18px;
                        color:#5a1522;
                        min-height:220px;
                        line-height:1.7;
                    ">
                        <b style="color:{BURGUNDY};font-size:18px;">
                            이번 학습의 핵심
                        </b>
                        <p>{type_titles[type_key]}의 발음 원리를 떠올리며
                        문제를 풀어 보세요.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if ss.syl_submitted:
                st.divider()
                left, right = st.columns([7, 3])

                with right:
                    if idx < len(questions) - 1:
                        if st.button("다음 문제 →", key=f"syl_all_next_{idx}",
                                     use_container_width=True):
                            ss.syl_quiz_index += 1
                            ss.syl_submitted = False
                            st.rerun()
                    else:
                        if st.button("발음 연습 시작 →",
                                     key="syl_all_start_practice",
                                     use_container_width=True):
                            ss.syl_page = "practice"
                            ss.syl_practice_index = 0
                            ss.syl_scores = {}
                            st.rerun()

        # ② 발음 연습
        elif phase == "practice":
            idx = ss.syl_practice_index
            type_key, word = words[idx]

            L, R = st.columns([5, 6], gap="medium")

            with L:
                st.markdown("### ② 발음 연습")
                st.caption(
                    f"{idx + 1} / 9 단어 · {type_titles[type_key]}"
                )

                st.markdown(
                    f"<h1 style='text-align:center;color:{BURGUNDY};"
                    f"margin:20px 0'>{word}</h1>",
                    unsafe_allow_html=True
                )

                st.write("원어민 발음을 듣고 소리 내어 따라 해 보세요.")
                listen([word])

                st.markdown("#### 녹음하기")

                recording = st.audio_input(
                    "내 발음 녹음하기",
                    key=f"syl_all_record_{idx}"
                )

                if recording is not None:
                    st.audio(recording)

                    score, _ = score_audio(recording, bump(1, 0.7))
                    ss.syl_scores[idx] = score

                    st.metric("소리 패턴 참고 점수", f"{score}점")

                    st.info(
                        "이 점수는 녹음과 인공 기준 파형의 소리 크기 변화 패턴을 "
                        "비교한 참고값이에요. 실제 발음의 정확도를 측정한 점수는 아니에요."
                    )

            with R:
                focus_text = {
                    "cluster": "자음 사이에 불필요한 모음 소리를 넣지 않고 "
                               "자연스럽게 이어 발음해 보세요.",
                    "stress": "강세가 있는 음절은 상대적으로 또렷하게, "
                              "나머지 음절은 약하게 발음해 보세요.",
                    "count": "철자 개수가 아니라 실제로 발음되는 "
                             "모음 소리를 기준으로 음절을 구분해 보세요."
                }

                st.markdown(
                    f"""
                    <div style="
                        background:#fdf0f2;
                        border-left:5px solid {BURGUNDY};
                        border-radius:10px;
                        padding:18px;
                        color:#5a1522;
                        min-height:280px;
                        line-height:1.7;
                    ">
                        <b style="color:{BURGUNDY};font-size:18px;">
                            이번 발음의 핵심
                        </b>
                        <p style="font-size:16px;margin-top:18px;">
                            {focus_text[type_key]}
                        </p>
                        <p style="margin-top:24px;">
                            <b>연습 단어</b><br>{word}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.divider()

            left_col, right_col = st.columns([7, 3])

            with right_col:
                if recording is None:
                    button_label = "건너뛰기 →"
                    button_key = f"syl_all_skip_{idx}"
                else:
                    button_label = (
                        "다음 단어 →"
                        if idx < len(words) - 1
                        else "결과 보기 →"
                    )
                    button_key = f"syl_next_{idx}"

                if st.button(
                    button_label,
                    key=button_key,
                    use_container_width=True
                ):
                    ss.syl_scores.setdefault(idx, 0)

                    if idx < len(words) - 1:
                        ss.syl_practice_index += 1
                    else:
                        ss.syl_page = "result"

                    st.rerun()

        # ③ 통합 결과
        elif phase == "result":
            answers = ss.get("syl_answers", {})

            correct = sum(
                1 for idx, (_, item) in enumerate(questions)
                if answers.get(idx) == item["ans"]
            )

            wrong_items = [
                (idx, type_key, item)
                for idx, (type_key, item) in enumerate(questions)
                if answers.get(idx) != item["ans"]
            ]

            wrong_rate = len(wrong_items) / len(questions) * 100

            scores = ss.get("syl_scores", {})
            pronunciation_scores = [
                scores.get(idx, 0) for idx in range(9)
            ]
            average_score = sum(pronunciation_scores) / 9

            if average_score >= 80:
                pronunciation_grade = "A"
            elif average_score >= 60:
                pronunciation_grade = "B"
            else:
                pronunciation_grade = "C"

            st.markdown("### 최종 학습 결과")
            st.success("음절 통합 연습을 모두 마쳤어요!")

            L, R = st.columns([5, 6], gap="medium")

            with L:
                st.markdown("#### ① 개념 확인 퀴즈")
                st.metric("퀴즈 정답", f"{correct} / 9")
                st.metric("전체 오답률", f"{wrong_rate:.1f}%")

                st.markdown("#### 유형별 오답률")

                for type_key in type_order:
                    type_questions = SYL_QUIZZES[type_key]
                    type_indices = [
                        i for i, (key, _) in enumerate(questions)
                        if key == type_key
                    ]
                    type_wrong = sum(
                        1 for i in type_indices
                        if answers.get(i) != questions[i][1]["ans"]
                    )
                    rate = type_wrong / len(type_questions) * 100

                    st.write(
                        f"**{type_titles[type_key]}** "
                        f"{type_wrong}/{len(type_questions)}문제 오답 · "
                        f"{rate:.0f}%"
                    )
                    st.progress(rate / 100)

            with R:
                st.markdown("#### ② 발음 연습 결과")
                st.metric("발음 등급", pronunciation_grade)
                st.metric("평균 참고 점수", f"{average_score:.1f}점")
                st.caption(
                    "녹음 점수는 소리 패턴을 비교한 참고값이며, "
                    "실제 발음 정확도와 동일하지 않아요."
                )

            if wrong_items:
                st.markdown("#### 오답 다시 확인하기")
                for idx, type_key, item in wrong_items:
                    with st.expander(f"{idx + 1}번 · {type_titles[type_key]}"):
                        st.write(f"**문제:** {item['q']}")
                        st.write(f"**정답:** {item['opts'][item['ans']]}")
                        st.write(item["why"])

            st.divider()
            _, button_col = st.columns([7, 3])
            with button_col:
                if st.button(
                    "다음 단계로 →",
                    key="syl_all_result_next",
                    use_container_width=True
                ):
                    finish_step()
                    st.rerun()
                  
def render_syllable_hub():
    slide_css()

    if ss.get("syl_type"):
        render_syllable_module()
        return

    st.markdown(
        f"<h2 style='color:{BURGUNDY}'>음절 발음 학습</h2>",
        unsafe_allow_html=True
    )
    st.write("학습할 발음 오류 유형을 선택하세요.")

    modules = [
        ("cluster", "① 자음 사이에 모음 삽입하기",
         "school, spring, street"),
        ("stress", "② 음절 강세 구별하기",
         "banana, computer, important"),
        ("count", "③ 실제 발음과 철자상 음절 수 구별하기",
         "cup, comb, speak"),
    ]

    for key, title, words in modules:
        with st.container(border=True):
            st.markdown(f"### {title}")
            st.write(words)

            if st.button("이 유형 학습하기 →", key=f"syl_select_{key}"):
                ss.syl_type = key
                ss.syl_page = "concept"
                ss.syl_index = 0
                ss.syl_quiz_index = 0
                ss.syl_answers = {}
                ss.syl_submitted = False
                ss.syl_practice_index = 0
                st.rerun()

    st.divider()

    if st.button("🏠 홈으로", key="syl_hub_home"):
        go_home()  
SYL_MODULES = {
    "cluster": {
        "title": "자음 연결과 모음 삽입",
        "goal": "영어에서 연속되는 자음을 중간에 모음을 넣지 않고 자연스럽게 연결하기",
        "pages": [
            {
                "heading": "자음이 연속될 때",
                "text": "영어에서는 여러 자음이 연속해서 나올 수 있어요. 이때 자음 사이에 불필요한 모음을 넣지 않아요.",
                "words": ["school", "spring", "street"],
                "focus": "school의 첫소리는 /s/와 /k/가 이어져요."
            },
            {
                "heading": "모음을 넣지 않고 연결하기",
                "text": "자음 하나씩 끊어 읽기보다 소리를 자연스럽게 이어 보세요.",
                "words": ["screen", "clean"],
                "focus": "자음 사이에 별도의 모음 소리가 생기지 않도록 해요."
            },
        ],
    },
    "stress": {
        "title": "음절 강세 구별하기",
        "goal": "강세가 있는 음절과 약하게 발음되는 음절의 차이 알아보기",
        "pages": [
            {
                "heading": "영어의 강세",
                "text": "영어 단어에서는 음절마다 발음의 힘과 길이가 달라질 수 있어요.",
                "words": ["banana", "computer"],
                "focus": "banana는 두 번째 음절에 강세가 있어요."
            },
            {
                "heading": "강한 소리와 약한 소리",
                "text": "강세가 있는 음절은 상대적으로 또렷하게, 나머지 음절은 약하게 발음해요.",
                "words": ["important", "family"],
                "focus": "모든 음절을 똑같은 세기로 발음하지 않는 것이 중요해요."
            },
        ],
    },
    "count": {
        "title": "실제 발음에 따른 음절 구분",
        "goal": "철자 개수가 아니라 실제로 발음되는 모음 소리를 기준으로 음절 세기",
        "pages": [
            {
                "heading": "모음 글자와 모음 소리",
                "text": "모음 글자가 여러 개여도 하나의 모음 소리로 발음될 수 있어요.",
                "words": ["cup", "comb", "tail"],
                "focus": "speak의 ea는 하나의 모음 소리 /iː/를 나타내므로<br>1음절이에요."
            },
            {
                "heading": "음절의 경계 찾기",
                "text": "단어의 의미 단위와 실제 발음 흐름을 함께 살펴보세요.",
                "words": ["seashell", "replay", "teacher", "pilot"],
                "focus": "합성어 seashell은 sea와 shell의 두 부분으로 나눌 수 있어요."
            },
        ],
    },
}
SYL_QUIZZES = {
    "cluster": [
        {
            "q": "school의 첫소리를 발음할 때 알맞은 것은?",
            "opts": ["자음 사이에 모음을 넣는다", "자음 /s/와 /k/를 이어 발음한다"],
            "ans": 1,
            "why": "school은 첫소리 /s/와 /k/ 사이에 별도의 모음 소리를 넣지 않아요."
        },
        {
            "q": "spring의 첫소리에서 주의할 점은?",
            "opts": ["자음들을 자연스럽게 연결한다", "각 자음 사이에 모음을 넣는다"],
            "ans": 0,
            "why": "spring의 /s/, /p/, /r/은 모음을 추가하지 않고 연결해요."
        },
        {
            "q": "다음 중 자음 사이에 모음을 넣지 않고 발음해야 하는 단어는?",
            "opts": ["street", "banana"],
            "ans": 0,
            "why": "street의 첫소리 /s/, /t/, /r/은 연속된 자음이에요."
        },
    ],
    "stress": [
        {
            "q": "banana에서 강세가 오는 음절은?",
            "opts": ["첫 번째", "두 번째", "세 번째"],
            "ans": 1,
            "why": "banana는 두 번째 음절에 강세가 있어요."
        },
        {
            "q": "computer에서 강세가 오는 음절은?",
            "opts": ["첫 번째", "두 번째", "세 번째"],
            "ans": 2,
            "why": "computer는 마지막 음절에 강세가 있어요."
        },
        {
            "q": "영어 단어의 강세를 연습할 때 알맞은 방법은?",
            "opts": ["모든 음절을 똑같이 강조한다", "강한 음절과 약한 음절을 구별한다"],
            "ans": 1,
            "why": "영어는 강세가 있는 음절과 약하게 발음되는 음절의 차이가 중요해요."
        },
    ],
    "count": [
        {
            "q": "speak의 음절 수는?",
            "opts": ["1개", "2개", "3개"],
            "ans": 0,
            "why": "ea가 하나의 모음 소리 /iː/를 나타내므로 1음절이에요."
        },
        {
            "q": "comb의 음절 수는?",
            "opts": ["1개", "2개", "3개"],
            "ans": 0,
            "why": "comb는 하나의 모음 소리로 발음되는 1음절 단어예요."
        },
        {
            "q": "seashell의 음절 경계로 알맞은 것은?",
            "opts": ["SEA | SHELL", "SE | ASHELL"],
            "ans": 0,
            "why": "합성어 seashell은 sea와 shell로 나눌 수 있어요."
        },
    ],
}
def render_syllable_module():
    module = SYL_MODULES[ss.syl_type]
    pages = module["pages"]
    page_index = ss.get("syl_index", 0)

    slide_css()

    st.markdown(
        f"<h2 style='color:{BURGUNDY}'>{module['title']}</h2>",
        unsafe_allow_html=True
    )
    st.caption(module["goal"])

    if ss.get("syl_page") == "concept":
        page = pages[page_index]

        st.markdown(f"### {page['heading']}")
        st.write(page["text"])

        st.markdown("**예시 단어**")
        for word in page["words"]:
            listen([word])

        with st.container(border=True):
            st.info(page["focus"])

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            if page_index > 0:
                if st.button("← 이전 내용", use_container_width=True):
                    ss.syl_index -= 1
                    st.rerun()

        with col2:
            if page_index < len(pages) - 1:
                if st.button("다음 내용 →", use_container_width=True):
                    ss.syl_index += 1
                    st.rerun()
            else:
                if st.button("개념 확인 퀴즈 →", use_container_width=True):
                    ss.syl_page = "quiz"
                    ss.syl_index = 0
                    ss.syl_quiz_index = 0
                    ss.syl_answers = {}
                    ss.syl_submitted = False
                    st.rerun()




    elif ss.get("syl_page") == "quiz":
        questions = SYL_QUIZZES[ss.syl_type]

        if "syl_quiz_index" not in ss:
            ss.syl_quiz_index = 0
            ss.syl_answers = {}
            ss.syl_submitted = False

        idx = ss.syl_quiz_index

        st.markdown("### 개념 확인 퀴즈")
        st.caption(f"{idx + 1} / {len(questions)} 문제")

        item = questions[idx]
        choice_key = f"syl_choice_{ss.syl_type}_{idx}"

        st.markdown(f"**Q. {item['q']}**")

        if not ss.syl_submitted:
            choice = st.radio(
                "정답을 선택하세요.",
                range(len(item["opts"])),
                format_func=lambda x: item["opts"][x],
                index=None,
                key=choice_key
            )

            if st.button("답 제출", key=f"syl_submit_{idx}"):
                if choice is None:
                    st.warning("정답을 먼저 선택해 주세요.")
                else:
                    ss.syl_answers[idx] = choice
                    ss.syl_submitted = True
                    st.rerun()

        else:
            answer = ss.syl_answers[idx]

            if answer == item["ans"]:
                st.success("정답이에요!")
            else:
                st.error("아쉽지만 정답이 아니에요.")

            st.info(item["why"])

            st.divider()
            left, right = st.columns([8, 2])

            with right:
                if idx < len(questions) - 1:
                    if st.button(
                        "다음 문제 →",
                        key=f"syl_next_{idx}",
                        use_container_width=True
                    ):
                        ss.syl_quiz_index += 1
                        ss.syl_submitted = False
                        st.rerun()

                else:
                    if st.button(
                        "발음 연습 시작 →",
                        key="syl_start_practice",
                        use_container_width=True
                    ):
                        ss.syl_page = "practice"
                        ss.syl_practice_index = 0
                        ss.syl_submitted = False
                        ss.syl_scores = {}
                        st.rerun()


    elif ss.get("syl_page") == "practice":
        practice_words = {
            "cluster": ["school", "spring", "street"],
            "stress": ["banana", "computer", "important"],
            "count": ["cup", "comb", "speak"],
        }

        words = practice_words[ss.syl_type]
        idx = ss.get("syl_practice_index", 0)
        word = words[idx]

        st.markdown("### 발음 연습")
        st.caption(f"{idx + 1} / {len(words)} 단어")

        st.markdown(
            f"<h1 style='text-align:center;color:{BURGUNDY}'>{word}</h1>",
            unsafe_allow_html=True
        )

        st.write("먼저 원어민 발음을 듣고, 소리 내어 따라 해 보세요.")
        listen([word])

        st.markdown("#### 녹음하기")
        recording = st.audio_input(
            "내 발음 녹음하기",
            key=f"syl_record_{ss.syl_type}_{idx}"
        )

        if recording is not None:
            st.audio(recording)

            score, _ = score_audio(recording, bump(1, 0.7))

            if "syl_scores" not in ss:
                ss.syl_scores = {}

            ss.syl_scores[idx] = score

            st.metric("소리 패턴 참고 점수", f"{score}점")

            st.info(
                "이 점수는 녹음과 인공 기준 파형의 소리 크기 변화 패턴을 "
                "비교한 참고값이에요. 실제 발음의 정확도를 측정한 점수는 아니에요."
            )

        st.divider()



    elif ss.get("syl_page") == "result":
        questions = SYL_QUIZZES[ss.syl_type]
        answers = ss.get("syl_answers", {})

        correct = sum(
            1 for i, item in enumerate(questions)
            if answers.get(i) == item["ans"]
        )

        scores = ss.get("syl_scores", {})
        pronunciation_scores = [
            scores.get(i, 0) for i in range(3)
        ]
        average_score = sum(pronunciation_scores) / 3

        if average_score >= 80:
            pronunciation_grade = "A"
        elif average_score >= 60:
            pronunciation_grade = "B"
        else:
            pronunciation_grade = "C"

        st.markdown("### 최종 학습 결과")
        st.success("이 유형의 학습을 마쳤어요!")

        st.divider()

        st.markdown("#### ① 개념 확인 퀴즈")
        st.metric("퀴즈 정답", f"{correct} / {len(questions)}")

        if correct == len(questions):
            st.write("모든 문제를 맞혔어요! 개념을 잘 이해했네요.")
        elif correct >= 2:
            st.write("잘했어요! 틀린 문제의 해설을 다시 확인해 보세요.")
        else:
            st.write("개념 설명을 한 번 더 읽고 다시 도전해 보세요.")

        st.divider()

        st.markdown("#### ② 발음 연습")
        st.metric("발음 종합 등급", pronunciation_grade)
        st.write(f"발음 참고 점수 평균: **{average_score:.0f}점 / 100점**")

        st.caption(
            "발음 점수는 실제 발음 정확도가 아니라 녹음과 인공 기준 파형의 "
            "소리 크기 변화 패턴을 비교한 참고값이에요."
        )

        st.divider()

        st.markdown("#### 스스로 발음 점검하기")

        if ss.syl_type == "cluster":
            st.write("- 자음 사이에 불필요한 모음을 넣지 않았나요?")
            st.write("- 자음들을 자연스럽게 이어 발음했나요?")
        elif ss.syl_type == "stress":
            st.write("- 강세가 있는 음절을 구별했나요?")
            st.write("- 약한 음절까지 지나치게 강조하지 않았나요?")
        else:
            st.write("- 철자 개수가 아니라 실제 모음 소리를 기준으로 셌나요?")
            st.write("- 단어의 음절 경계를 구별했나요?")

        st.divider()
        if "syl_completed_types" not in ss:
            ss.syl_completed_types = []

        if ss.syl_type not in ss.syl_completed_types:
            ss.syl_completed_types.append(ss.syl_type)

        all_syl_types_done = {
            "cluster", "stress", "count"
        }.issubset(set(ss.syl_completed_types))

        if not all_syl_types_done:
            left, right = st.columns(2)

            with left:
                if st.button("이 유형 다시 학습하기", use_container_width=True):
                    ss.syl_page = "concept"
                    ss.syl_index = 0
                    ss.syl_quiz_index = 0
                    ss.syl_answers = {}
                    ss.syl_submitted = False
                    ss.syl_practice_index = 0
                    ss.syl_scores = {}
                    st.rerun()

            with right:
                if st.button("다음 유형으로 →", use_container_width=True):
                    ss.syl_type = None
                    ss.syl_page = "concept"
                    ss.syl_index = 0
                    ss.syl_quiz_index = 0
                    ss.syl_answers = {}
                    ss.syl_submitted = False
                    ss.syl_practice_index = 0
                    ss.syl_scores = {}
                    st.rerun()

        else:
            left, center, right = st.columns([1, 1, 1])

            with center:
                if st.button("다른 유형으로", use_container_width=True):
                    ss.syl_type = None
                    ss.syl_page = "concept"
                    ss.syl_index = 0
                    ss.syl_quiz_index = 0
                    ss.syl_answers = {}
                    ss.syl_submitted = False
                    ss.syl_practice_index = 0
                    ss.syl_scores = {}
                    st.rerun()

            with right:
                if st.button("다음 단계로 →", use_container_width=True):
                    finish_step()
                    st.rerun()
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
            
            left, right = st.columns([8, 2])
            with right:
                st.button(
                    "답 체크",
                    on_click=t_submit,
                    args=(ok,),
                    disabled=not ready,
                    key=f"tb{key}",
                    use_container_width=True
                )
        else:
            ok = t["a"][q]
            st.markdown(big("✅ 정답이에요!" if ok else "❌ 아쉬워요", 2.4), unsafe_allow_html=True)
            ans = Qd["w"] if Qd["k"] == "rec" else Qd["opts"][Qd["ans"]]
            st.markdown(f"<p class='center'>정답/목표: <b>{ans}</b></p>", unsafe_allow_html=True)
            tag = (f"<span style='font-size:.75rem;background:#fff;border:1px solid {BURGUNDY};"
                   f"border-radius:8px;padding:1px 8px'>{STEPS[lang][Qd['s']]}</span>")
            image_data = base64.b64encode(HINT_BEAR_IMG.read_bytes()).decode("utf-8")
            st.markdown(
                f"""
                <div class='tip'>
                    <img src="data:image/png;base64,{image_data}"
                         style="width:28px; height:auto; vertical-align:middle; margin-right:3px;">
                    관련 개념: {Qd['c']} {tag}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            left, right = st.columns([8, 2])
            with right:
                st.button(
                    "결과 보기 →" if q >= 9 else "다음 문제 →",
                    on_click=t_next,
                    key=f"tn{q}",
                    use_container_width=True
                )
        return

    wrong = [i for i, ok in enumerate(t["a"]) if not ok]
    if ph == "res":
        pct = (10 - len(wrong)) * 10
        header(sub, ["결과"], 0)
        st.markdown(f"<div class='center'>{donut_svg(pct)}<h3>정답 {10 - len(wrong)}개 · "
                    f"<span style='color:#2e9e5b'>정답률 {pct}%</span> · "
                    f"<span style='color:#d9534f'>오답률 {100 - pct}%</span></h3></div>", unsafe_allow_html=True)
        
        left, right = st.columns([8, 2])

        with left:
            if wrong:
                st.button("틀린 문제 복습", on_click=t_goto, args=("rev",), key="r_rev")
            else:
                st.success("모두 맞혔어요! 🎉")

        with right:
            st.button(
                "🏠 홈으로 돌아가기",
                on_click=go_home,
                key="r_home",
                use_container_width=True
            )
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
    
    left, right = st.columns([8, 2])

    with left:
        st.button("테스트 재응시", on_click=retake, key="retake")

    with right:
        st.button(
            "🏠 홈으로 돌아가기",
            on_click=go_home,
            key="rv_home",
            use_container_width=True
        )


# ------------------------------------------------------------------
# 10. 앱 메인 분기
# ------------------------------------------------------------------
SCREENS = {"start": screen_start, "home": screen_home, "step": screen_step,
           "stepend": screen_stepend, "finale": screen_finale}
SCREENS[ss.screen]()