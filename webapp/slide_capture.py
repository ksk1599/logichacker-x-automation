"""
slide_capture.py — HTML 슬라이드를 Chrome으로 렌더링해 스크린샷 → PPTX 변환
웹에서 보이는 것과 100% 동일한 시각 품질을 보장한다.
"""

import time
import tempfile
from io import BytesIO
from pathlib import Path


# ── 애니메이션 무효화 CSS ────────────────────────────────────────────────
# 스크린샷 캡처 시 전환 효과 없이 즉시 슬라이드를 표시하기 위한 오버라이드
_CAPTURE_CSS = """
<style id="capture-override">
*, *::before, *::after {
  transition: none !important;
  animation: none !important;
  animation-duration: 0s !important;
}
.slide {
  transition: none !important;
}
/* reveal 클래스 요소: 항상 표시 */
.reveal, [class*="reveal"], .appear, [data-reveal] {
  opacity: 1 !important;
  transform: none !important;
  filter: none !important;
}
</style>
"""


def _inject_capture_css(html: str) -> str:
    """HTML에 캡처용 CSS 주입 (애니메이션 제거, 콘텐츠 전부 표시)"""
    return html.replace('</head>', _CAPTURE_CSS + '</head>', 1)


def capture_slides(html: str, progress_callback=None) -> list[bytes]:
    """
    HTML 프레젠테이션 → 슬라이드별 PNG 스크린샷 리스트.

    Args:
        html: 완성된 HTML 프레젠테이션 문자열
        progress_callback: capture_slides(i, total) 형태로 호출되는 진행 콜백 (선택)

    Returns:
        PNG 바이트 리스트 (슬라이드 순서대로)
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError as e:
        raise RuntimeError(
            f"selenium 또는 webdriver-manager 미설치: {e}\n"
            "pip install selenium webdriver-manager 실행 후 재시도하세요."
        ) from e

    capture_html = _inject_capture_css(html)

    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.html', delete=False, encoding='utf-8'
    )
    tmp.write(capture_html)
    tmp.close()
    tmp_path = Path(tmp.name)

    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--hide-scrollbars')
    options.add_argument('--force-device-scale-factor=1')
    # 폰트 렌더링 개선
    options.add_argument('--disable-font-subpixel-positioning')
    options.add_argument('--enable-font-antialiasing')

    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(1920, 1080)

        file_url = 'file:///' + tmp_path.as_posix().lstrip('/')
        driver.get(file_url)

        # 폰트·이미지 로딩 대기
        time.sleep(2.0)

        # 총 슬라이드 수
        total = driver.execute_script(
            'return document.querySelectorAll("#viewport .slide").length || '
            'document.querySelectorAll(".slide").length'
        )
        if not total:
            raise RuntimeError("슬라이드를 찾을 수 없습니다. HTML 구조를 확인하세요.")

        screenshots: list[bytes] = []
        for i in range(total):
            if progress_callback:
                progress_callback(i, total)

            # DOM 직접 조작으로 슬라이드 전환 (CSS transition 없이 즉시)
            driver.execute_script(f"""
                const viewport = document.getElementById('viewport') ||
                                 document.querySelector('.slide-viewport') ||
                                 document.body;
                const slides = viewport.querySelectorAll('.slide');
                const idx = {i};
                slides.forEach((s, n) => {{
                    s.classList.remove('active', 'stand-left');
                    s.style.opacity   = '0';
                    s.style.transform = 'translateX(100%)';
                    s.style.pointerEvents = 'none';
                    if (n < idx) {{
                        s.classList.add('stand-left');
                        s.style.transform = 'translateX(-100%)';
                    }} else if (n === idx) {{
                        s.classList.add('active');
                        s.style.opacity   = '1';
                        s.style.transform = 'translateX(0)';
                        s.style.pointerEvents = 'auto';
                    }}
                }});
                /* 현재 슬라이드의 모든 reveal 요소 즉시 표시 */
                const cur = slides[idx];
                if (cur) {{
                    cur.querySelectorAll('.reveal, [class*="reveal"], .appear').forEach(el => {{
                        el.style.opacity   = '1';
                        el.style.transform = 'none';
                        el.style.filter    = 'none';
                    }});
                }}
            """)
            # 렌더링 완료 대기 (짧아도 됨 — transition 비활성화됨)
            time.sleep(0.15)
            screenshots.append(driver.get_screenshot_as_png())

        return screenshots

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        tmp_path.unlink(missing_ok=True)


def screenshots_to_pptx(screenshots: list[bytes]) -> bytes:
    """PNG 스크린샷 리스트 → PPTX 바이트 (슬라이드 = 이미지 1장)"""
    from pptx import Presentation
    from pptx.util import Inches
    from pptx.dml.color import RGBColor

    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]

    for png_bytes in screenshots:
        slide = prs.slides.add_slide(blank_layout)

        # 배경 검정 (이미지 사이 흰 틈 방지)
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(0x0A, 0x0A, 0x0F)

        # 슬라이드 전체를 스크린샷으로 채우기
        slide.shapes.add_picture(
            BytesIO(png_bytes),
            0, 0,
            prs.slide_width,
            prs.slide_height,
        )

    buf = BytesIO()
    prs.save(buf)
    return buf.getvalue()


def html_to_pptx(html: str, progress_callback=None) -> bytes:
    """HTML 프레젠테이션 → PPTX (스크린샷 기반, 웹과 100% 시각 동일)"""
    shots = capture_slides(html, progress_callback=progress_callback)
    return screenshots_to_pptx(shots)
