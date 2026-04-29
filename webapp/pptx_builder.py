"""
pptx_builder.py — HTML 슬라이드 → .pptx 변환
HTML의 <section> 요소를 파싱해 다크 테마 PowerPoint 파일을 생성한다.
"""

import re
from io import BytesIO

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── 색상 (template.html 디자인 시스템과 동일) ──────────────────────────
BG          = RGBColor(0x0A, 0x0A, 0x0F)   # 배경 (거의 검정)
ACCENT      = RGBColor(0xC6, 0xA5, 0x5C)   # 금색 강조
TEXT_PRI    = RGBColor(0xF0, 0xEB, 0xE0)   # 본문 (밝은 크림)
TEXT_SEC    = RGBColor(0xB8, 0xB0, 0xA0)   # 보조 텍스트
TEXT_DIM    = RGBColor(0x70, 0x68, 0x58)   # 흐린 텍스트
BULLET_DOT  = RGBColor(0xC6, 0xA5, 0x5C)   # 불릿 점 색상 (금색)

# ── 슬라이드 크기: 16:9 와이드 ────────────────────────────────────────
W = Inches(13.33)   # 너비
H = Inches(7.5)     # 높이

# ── 마진 ──────────────────────────────────────────────────────────────
MARGIN_L  = Inches(0.8)
MARGIN_T  = Inches(0.6)
MARGIN_R  = Inches(0.8)
CONTENT_W = W - MARGIN_L - MARGIN_R


# ═══════════════════════════════════════════════════════════════════════
# 내부 유틸
# ═══════════════════════════════════════════════════════════════════════

def _strip_tags(html: str) -> str:
    """HTML 태그 제거 후 공백 정리"""
    text = re.sub(r'<[^>]+>', '', html)
    # HTML 엔티티 기본 처리
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
               .replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
    return re.sub(r'\s+', ' ', text).strip()


def _set_bg(slide, color: RGBColor):
    """슬라이드 배경 단색 채우기"""
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_rect(slide, left, top, width, height, color: RGBColor):
    """단색 직사각형 도형 추가 (구분선, 배지 배경 등)"""
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height
    )
    shape.line.fill.background()          # 테두리 없음
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    return shape


def _add_text(slide, text, left, top, width, height,
              size=24, color=TEXT_PRI, bold=False,
              align=PP_ALIGN.LEFT, wrap=True, italic=False):
    """텍스트박스 추가 후 스타일 적용"""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic
    # 한국어 폰트 지정
    run.font.name = '맑은 고딕'
    return txBox


def _add_bullet_list(slide, items: list[str], left, top, width, height,
                     size=20, color=TEXT_PRI):
    """불릿 리스트 텍스트박스 추가"""
    if not items:
        return
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True

    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        # 불릿 기호
        dot = p.add_run()
        dot.text = '▸  '
        dot.font.size = Pt(size - 2)
        dot.font.color.rgb = ACCENT
        dot.font.name = '맑은 고딕'
        # 항목 텍스트
        run = p.add_run()
        run.text = item
        run.font.size = Pt(size)
        run.font.color.rgb = color
        run.font.name = '맑은 고딕'

        # 항목 간격
        from pptx.oxml.ns import qn
        from lxml import etree
        pPr = p._p.get_or_add_pPr()
        pPr.set(qn('a:spcBef'), '0')
        spcBef = etree.SubElement(pPr, qn('a:spcBef'))
        spc = etree.SubElement(spcBef, qn('a:spcPts'))
        spc.set('val', '160')  # 1.6pt 위 여백


# ═══════════════════════════════════════════════════════════════════════
# HTML 파싱
# ═══════════════════════════════════════════════════════════════════════

def _parse_slides(html: str) -> list[dict]:
    """<section class="slide ..."> 요소를 슬라이드 데이터로 파싱"""
    # section 태그 단위로 분리
    sections = re.findall(
        r'<section[^>]+class="([^"]*slide[^"]*)"[^>]*>(.*?)</section>',
        html, re.DOTALL | re.IGNORECASE
    )

    slides = []
    for classes, inner in sections:
        # 슬라이드 타입 결정
        if 'slide--intro' in classes:
            stype = 'intro'
        elif 'slide--end' in classes:
            stype = 'end'
        elif 'slide--diagram' in classes:
            stype = 'diagram'
        elif 'slide--code' in classes:
            stype = 'code'
        else:
            stype = 'content'

        # 제목 추출 (h1 > h2 > h3 우선순위)
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', inner, re.DOTALL)
        h2 = re.search(r'<h2[^>]*>(.*?)</h2>', inner, re.DOTALL)
        h3 = re.search(r'<h3[^>]*>(.*?)</h3>', inner, re.DOTALL)
        title = _strip_tags(
            (h1 or h2 or h3).group(1) if (h1 or h2 or h3) else ''
        )

        # terminal-badge (키워드 태그)
        badge = re.search(
            r'class="terminal-badge[^"]*"[^>]*>(.*?)</div>', inner, re.DOTALL
        )
        badge_text = _strip_tags(badge.group(1)) if badge else ''

        # 불릿 항목 (li)
        items = [_strip_tags(m) for m in re.findall(r'<li[^>]*>(.*?)</li>', inner, re.DOTALL)]
        items = [x for x in items if x]

        # 일반 단락 (li 블록 제외)
        no_list = re.sub(r'<ul[^>]*>.*?</ul>', '', inner, flags=re.DOTALL)
        no_list = re.sub(r'<ol[^>]*>.*?</ol>', '', no_list, flags=re.DOTALL)
        paras = [
            _strip_tags(m)
            for m in re.findall(r'<p[^>]*>(.*?)</p>', no_list, re.DOTALL)
        ]
        paras = [x for x in paras if x and len(x) > 1]

        # split-card 텍스트 (다이어그램 슬라이드용)
        cards = [
            _strip_tags(m)
            for m in re.findall(r'class="split-card[^"]*"[^>]*>(.*?)</div>', inner, re.DOTALL)
        ]
        cards = [x for x in cards if x]

        # 코드 블록 (code)
        code_block = re.search(r'<code[^>]*>(.*?)</code>', inner, re.DOTALL)
        code_text = _strip_tags(code_block.group(1)) if code_block else ''

        slides.append({
            'type':   stype,
            'title':  title,
            'badge':  badge_text,
            'items':  items,
            'paras':  paras,
            'cards':  cards,
            'code':   code_text,
        })

    return slides


# ═══════════════════════════════════════════════════════════════════════
# 슬라이드 타입별 렌더러
# ═══════════════════════════════════════════════════════════════════════

def _slide_intro(slide, data: dict):
    """타이틀 슬라이드 (slide--intro)"""
    _set_bg(slide, BG)

    # 왼쪽 금색 세로 강조선
    _add_rect(slide, Inches(0.4), Inches(1.5), Inches(0.06), Inches(4.5), ACCENT)

    # badge
    if data['badge']:
        _add_text(slide, f'> {data["badge"]}',
                  MARGIN_L, Inches(1.6), CONTENT_W, Inches(0.5),
                  size=14, color=ACCENT, bold=True)

    # 제목
    _add_text(slide, data['title'],
              MARGIN_L, Inches(2.2), CONTENT_W, Inches(2.0),
              size=40, color=TEXT_PRI, bold=True)

    # 수평 강조선
    _add_rect(slide, MARGIN_L, Inches(4.4), Inches(1.2), Inches(0.04), ACCENT)

    # 부제 (파라 첫 번째)
    if data['paras']:
        _add_text(slide, data['paras'][0],
                  MARGIN_L, Inches(4.6), CONTENT_W, Inches(0.8),
                  size=18, color=TEXT_SEC)

    # 안내 텍스트
    _add_text(slide, '← → 키 또는 버튼으로 이동',
              MARGIN_L, Inches(6.6), CONTENT_W, Inches(0.5),
              size=12, color=TEXT_DIM)


def _slide_content(slide, data: dict):
    """일반 콘텐츠 슬라이드 (slide--content / slide--content-alt)"""
    _set_bg(slide, BG)

    # 상단 금색 얇은 선
    _add_rect(slide, 0, 0, W, Inches(0.04), ACCENT)

    top = MARGIN_T

    # badge
    if data['badge']:
        _add_text(slide, f'> {data["badge"]}',
                  MARGIN_L, top, CONTENT_W, Inches(0.45),
                  size=13, color=ACCENT, bold=True)
        top += Inches(0.5)

    # 제목
    if data['title']:
        _add_text(slide, data['title'],
                  MARGIN_L, top, CONTENT_W, Inches(1.0),
                  size=28, color=TEXT_PRI, bold=True)
        top += Inches(1.0)

    # 강조선
    _add_rect(slide, MARGIN_L, top, Inches(0.8), Inches(0.035), ACCENT)
    top += Inches(0.25)

    # 불릿 항목
    if data['items']:
        item_h = Inches(0.5) * len(data['items']) + Inches(0.5)
        _add_bullet_list(slide, data['items'],
                         MARGIN_L, top, CONTENT_W, item_h,
                         size=20)
        top += item_h

    # 일반 단락
    for para in data['paras']:
        _add_text(slide, para,
                  MARGIN_L, top, CONTENT_W, Inches(0.8),
                  size=18, color=TEXT_SEC)
        top += Inches(0.75)


def _slide_diagram(slide, data: dict):
    """분할 레이아웃 슬라이드 (slide--diagram)"""
    _set_bg(slide, BG)
    _add_rect(slide, 0, 0, W, Inches(0.04), ACCENT)

    top = MARGIN_T
    if data['badge']:
        _add_text(slide, f'> {data["badge"]}',
                  MARGIN_L, top, CONTENT_W, Inches(0.45),
                  size=13, color=ACCENT, bold=True)
        top += Inches(0.5)

    if data['title']:
        _add_text(slide, data['title'],
                  MARGIN_L, top, CONTENT_W, Inches(0.9),
                  size=26, color=TEXT_PRI, bold=True)
        top += Inches(1.0)

    _add_rect(slide, MARGIN_L, top, Inches(0.8), Inches(0.035), ACCENT)
    top += Inches(0.3)

    # 카드 2열 배치
    card_w = (CONTENT_W - Inches(0.4)) / 2
    card_h = Inches(3.0)
    gap = Inches(0.4)

    for i, card_text in enumerate(data['cards'][:2]):
        cx = MARGIN_L + i * (card_w + gap)
        # 카드 배경
        bg_shape = slide.shapes.add_shape(1, cx, top, card_w, card_h)
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = RGBColor(0x11, 0x11, 0x18)
        bg_shape.line.color.rgb = RGBColor(0x1E, 0x1C, 0x18)
        bg_shape.line.width = Pt(1)
        # 카드 텍스트
        _add_text(slide, card_text,
                  cx + Inches(0.2), top + Inches(0.3),
                  card_w - Inches(0.4), card_h - Inches(0.4),
                  size=17, color=TEXT_PRI, wrap=True)


def _slide_code(slide, data: dict):
    """코드 슬라이드 (slide--code)"""
    _set_bg(slide, BG)
    _add_rect(slide, 0, 0, W, Inches(0.04), ACCENT)

    top = MARGIN_T
    if data['title']:
        _add_text(slide, data['title'],
                  MARGIN_L, top, CONTENT_W, Inches(0.9),
                  size=26, color=ACCENT, bold=True)
        top += Inches(1.0)

    if data['code']:
        # 코드 블록 배경
        code_h = Inches(4.5)
        bg = slide.shapes.add_shape(1, MARGIN_L, top, CONTENT_W, code_h)
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor(0x11, 0x11, 0x18)
        bg.line.color.rgb = RGBColor(0x1E, 0x1C, 0x18)
        bg.line.width = Pt(1)
        _add_text(slide, data['code'],
                  MARGIN_L + Inches(0.2), top + Inches(0.2),
                  CONTENT_W - Inches(0.4), code_h - Inches(0.4),
                  size=15, color=TEXT_PRI, wrap=True)


def _slide_end(slide, data: dict):
    """마무리 슬라이드 (slide--end)"""
    _set_bg(slide, BG)

    cx = W / 2
    _add_text(slide, data['title'] or '감사합니다',
              Inches(1), Inches(2.5), W - Inches(2), Inches(1.5),
              size=44, color=TEXT_PRI, bold=True, align=PP_ALIGN.CENTER)

    _add_rect(slide, cx - Inches(0.6), Inches(4.1), Inches(1.2), Inches(0.04), ACCENT)

    if data['paras']:
        _add_text(slide, data['paras'][0],
                  Inches(1), Inches(4.3), W - Inches(2), Inches(0.8),
                  size=20, color=TEXT_SEC, align=PP_ALIGN.CENTER)


# ═══════════════════════════════════════════════════════════════════════
# 공개 API
# ═══════════════════════════════════════════════════════════════════════

def build_pptx(html: str) -> bytes:
    """
    HTML 프레젠테이션 문자열 → .pptx 바이트 반환.
    앱에서 st.download_button(data=...) 에 바로 넣을 수 있다.
    """
    slides_data = _parse_slides(html)

    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H

    # 빈 레이아웃(인덱스 6) 사용 — 텍스트박스/도형 자유 배치
    blank_layout = prs.slide_layouts[6]

    renderer = {
        'intro':   _slide_intro,
        'content': _slide_content,
        'diagram': _slide_diagram,
        'code':    _slide_code,
        'end':     _slide_end,
    }

    for data in slides_data:
        ppt_slide = prs.slides.add_slide(blank_layout)
        fn = renderer.get(data['type'], _slide_content)
        fn(ppt_slide, data)

    buf = BytesIO()
    prs.save(buf)
    return buf.getvalue()
