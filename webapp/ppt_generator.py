"""
ppt_generator.py — 전체 원고를 PPT로 변환
섹션별로 슬라이드를 자동 생성하고 bytes로 반환한다.
"""

import io
import re
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN


# ── 디자인 상수 ────────────────────────────────────────────────────────
BG_COLOR      = RGBColor(0x1A, 0x1A, 0x2E)   # 진한 남색 배경
ACCENT_COLOR  = RGBColor(0xE9, 0x4F, 0x37)   # 포인트 빨강
TITLE_COLOR   = RGBColor(0xFF, 0xFF, 0xFF)   # 흰색 제목
BODY_COLOR    = RGBColor(0xD0, 0xD0, 0xD0)   # 연회색 본문
TAG_COLOR     = RGBColor(0xE9, 0x4F, 0x37)   # 섹션 태그
SLIDE_W       = Inches(13.33)
SLIDE_H       = Inches(7.5)


def _set_bg(slide, color: RGBColor):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_textbox(slide, text: str, left, top, width, height,
                 font_size=24, bold=False, color=TITLE_COLOR,
                 align=PP_ALIGN.LEFT, wrap=True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    return txBox


def _add_divider(slide, top, color=ACCENT_COLOR):
    """가로 구분선 추가"""
    line = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(0.5), top, Inches(12.33), Pt(3)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()


# ── 슬라이드 유형별 생성 함수 ─────────────────────────────────────────

def _make_title_slide(prs, title: str):
    """표지 슬라이드"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # 빈 레이아웃
    _set_bg(slide, BG_COLOR)

    # 채널 태그
    _add_textbox(slide, "로직해커 엑스",
                 Inches(0.6), Inches(1.5), Inches(12), Inches(0.6),
                 font_size=18, color=ACCENT_COLOR)

    # 메인 제목 (줄바꿈 처리)
    display_title = title.split("|")[0].strip() if "|" in title else title
    _add_textbox(slide, display_title,
                 Inches(0.6), Inches(2.2), Inches(12), Inches(2.5),
                 font_size=36, bold=True, color=TITLE_COLOR, wrap=True)

    _add_divider(slide, Inches(5.0))

    # SEO 부분 (| 이후)
    if "|" in title:
        seo = title.split("|")[1].strip()
        _add_textbox(slide, seo,
                     Inches(0.6), Inches(5.2), Inches(12), Inches(0.8),
                     font_size=16, color=BODY_COLOR)


def _make_section_slide(prs, tag: str, heading: str, content: str):
    """섹션 슬라이드 (태그 + 제목 + 내용)"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, BG_COLOR)

    # 섹션 태그 (예: 📌 도입부 · 문제제시)
    _add_textbox(slide, tag,
                 Inches(0.6), Inches(0.4), Inches(12), Inches(0.5),
                 font_size=16, color=TAG_COLOR, bold=True)

    _add_divider(slide, Inches(1.1))

    # 슬라이드 제목
    _add_textbox(slide, heading,
                 Inches(0.6), Inches(1.3), Inches(12), Inches(1.2),
                 font_size=30, bold=True, color=TITLE_COLOR)

    # 본문 내용
    # 마크다운 기호(**) 제거 후 표시
    clean = re.sub(r"\*\*(.+?)\*\*", r"\1", content)
    clean = re.sub(r"\*(.+?)\*", r"\1", clean)
    clean = re.sub(r"`(.+?)`", r"\1", clean)
    clean = clean.strip()

    _add_textbox(slide, clean,
                 Inches(0.6), Inches(2.7), Inches(12), Inches(4.2),
                 font_size=20, color=BODY_COLOR, wrap=True)


# ── 원고 파싱 ─────────────────────────────────────────────────────────

def _parse_script(script: str) -> dict:
    """
    원고 텍스트에서 섹션별 내용을 추출한다.
    ## 📌 도입부, ## 📖 본문, ## 💛 개인가치, ## 🎬 결론 기준으로 분리.
    """
    sections = {}

    patterns = [
        ("도입부", r"##\s*📌\s*도입부(.+?)(?=##\s*📖|##\s*💛|##\s*🎬|$)"),
        ("본문",   r"##\s*📖\s*본문(.+?)(?=##\s*💛|##\s*🎬|$)"),
        ("개인가치", r"##\s*💛\s*개인가치(.+?)(?=##\s*🎬|$)"),
        ("결론",   r"##\s*🎬\s*결론(.+?)$"),
    ]

    for key, pattern in patterns:
        m = re.search(pattern, script, re.DOTALL)
        sections[key] = m.group(1).strip() if m else ""

    return sections


def _split_body(body: str) -> list:
    """
    본문에서 [주장], [근거], [원리], [예시], [반론], [대안] 블록을 분리.
    각 블록을 (태그, 내용) 튜플 리스트로 반환.
    """
    tags = ["주장", "근거", "원리", "예시", "반론", "대안"]
    result = []

    for tag in tags:
        # **[주장]** 또는 [주장] 형태 모두 인식
        pattern = rf"(?:\*\*)?\[{tag}\](?:\*\*)?(.+?)(?=(?:\*\*)?\[(?:주장|근거|원리|예시|반론|대안)\]|$)"
        m = re.search(pattern, body, re.DOTALL)
        if m:
            result.append((tag, m.group(1).strip()))

    # 블록 구분 실패 시 본문 전체를 하나의 슬라이드로
    if not result:
        result = [("본문", body)]

    return result


def _split_intro(intro: str) -> list:
    """도입부에서 문제/사례/유인 블록 분리 (없으면 전체를 1장으로)"""
    # 구분선(---) 기준으로 분리 시도
    parts = [p.strip() for p in re.split(r"\n---+\n", intro) if p.strip()]

    labels = ["문제제시", "사례제시", "유인제시"]
    if len(parts) >= 3:
        return list(zip(labels, parts[:3]))
    elif len(parts) == 2:
        return list(zip(labels[:2], parts))
    else:
        return [("도입부", intro)]


# ── 메인 함수 ─────────────────────────────────────────────────────────

def generate_ppt(title: str, script: str) -> bytes:
    """
    title  : 유튜브 제목
    script : 전체 원고 (## 섹션 마크다운 형식)
    return : .pptx 파일 bytes
    """
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    sections = _parse_script(script)

    # 1. 표지
    _make_title_slide(prs, title)

    # 2. 도입부 슬라이드들
    intro_parts = _split_intro(sections.get("도입부", ""))
    for label, content in intro_parts:
        _make_section_slide(prs, f"📌 도입부 · {label}", label, content)

    # 3. 본문 슬라이드들
    body_parts = _split_body(sections.get("본문", ""))
    body_labels = {"주장": "핵심 주장", "근거": "근거", "원리": "원리",
                   "예시": "예시", "반론": "반론", "대안": "대안"}
    for tag, content in body_parts:
        heading = body_labels.get(tag, tag)
        _make_section_slide(prs, f"📖 본문 · {tag}", heading, content)

    # 4. 개인가치
    if sections.get("개인가치"):
        # 선택 질문 줄 제거하고 내용만 추출
        pv_content = re.sub(r">?\s*선택한 질문:.+?\n", "", sections["개인가치"]).strip()
        _make_section_slide(prs, "💛 개인가치", "나의 이야기", pv_content)

    # 5. 결론
    if sections.get("결론"):
        _make_section_slide(prs, "🎬 결론", "마무리", sections["결론"])

    # bytes로 반환
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.getvalue()
