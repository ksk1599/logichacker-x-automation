"""
app.py — 로직해커 엑스 콘텐츠 도구 (Streamlit 로컬 웹앱)

실행: streamlit run app.py
      또는 run.bat 더블클릭
"""

import sys
from pathlib import Path

# webapp/ 폴더를 모듈 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from claude_client import call_thumbnail, call_script, call_full_script
from ppt_generator import generate_ppt
from auto_save import (
    get_next_thumbnail_letter,
    get_next_script_number,
    save_thumbnail_reference,
    save_script_reference,
)

# ── 페이지 설정 ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="로직해커 엑스 콘텐츠 도구",
    page_icon="🎬",
    layout="centered",
)
st.title("🎬 로직해커 엑스 콘텐츠 도구")
st.caption("썸네일 문구·제목 생성 / 첫 30초 후킹 원고 생성")

tab_thumbnail, tab_script, tab_full = st.tabs(["📌 썸네일 만들기", "🎙️ 30초 원고", "📝 전체 원고"])


# ── 탭 1: 썸네일 만들기 ───────────────────────────────────────────────
with tab_thumbnail:
    st.subheader("썸네일 문구 + 유튜브 제목")

    topic = st.text_input(
        "영상 주제",
        placeholder="상세페이지 최상단 기획하는 법",
        key="thumb_topic",
    )
    image_file = st.file_uploader(
        "참고 이미지 (선택) — 다른 채널 터진 영상 캡처를 주면 학습 후 카피라이팅",
        type=["png", "jpg", "jpeg"],
        key="thumb_image",
    )
    note = st.text_area(
        "특별 요청 (선택)",
        placeholder="Before→After 패턴으로 만들어주세요 / 공포감 강조 등",
        height=80,
        key="thumb_note",
    )

    if st.button("✨ 생성하기", key="thumb_btn", type="primary"):
        if not topic.strip():
            st.warning("영상 주제를 입력해주세요.")
        else:
            # 저장 전에 다음 알파벳 미리 계산해서 Claude에게 전달 (응답 블록 번호 일치)
            next_letter = get_next_thumbnail_letter()
            image_bytes = image_file.read() if image_file else None

            with st.spinner("Claude가 카피라이팅 중..."):
                try:
                    result = call_thumbnail(topic, image_bytes, note, next_letter)
                except Exception as e:
                    st.error(f"API 오류: {e}")
                    st.stop()

            # 마커 제거 후 결과 표시 (마커 텍스트가 UI에 노출되지 않도록)
            display = result.replace("<!-- SAVE_START -->", "").replace("<!-- SAVE_END -->", "").strip()
            st.markdown(display)

            # 자동 저장
            saved = save_thumbnail_reference(result)
            if saved:
                st.success(f"✅ patterns.md에 레퍼런스 {saved} 자동 저장됨 — PC 재시작 후에도 유지")
            elif image_file:
                st.info("저장 블록을 찾지 못했습니다. 결과를 직접 확인해주세요.")

    st.divider()
    st.caption("💡 참고 이미지를 첨부하면 패턴 학습 + 카피라이팅을 동시에 진행합니다.")


# ── 탭 2: 30초 원고 ───────────────────────────────────────────────────
with tab_script:
    st.subheader("첫 30초 후킹 원고")

    topic2 = st.text_input(
        "영상 주제",
        placeholder="상세페이지 최상단의 비밀",
        key="script_topic",
    )
    ref_script = st.text_area(
        "레퍼런스 30초 원고 (선택) — 터진 영상의 원고를 붙여넣으면 패턴 학습 후 제 채널 스타일로 원고 생성",
        placeholder=(
            "예시:\n"
            "자, 여러분, 지금 장난감 결제 버튼 누르려던 손 잠시만 멈추고...\n"
            "(원고를 붙여넣어 주세요)"
        ),
        height=200,
        key="script_ref",
    )

    if st.button("✨ 생성하기", key="script_btn", type="primary"):
        if not topic2.strip():
            st.warning("영상 주제를 입력해주세요.")
        else:
            next_num = get_next_script_number()

            with st.spinner("Claude가 원고 작성 중..."):
                try:
                    result2 = call_script(topic2, ref_script, next_num)
                except Exception as e:
                    st.error(f"API 오류: {e}")
                    st.stop()

            display2 = result2.replace("<!-- SAVE_START -->", "").replace("<!-- SAVE_END -->", "").strip()
            st.markdown(display2)

            # 자동 저장
            saved2 = save_script_reference(result2)
            if saved2:
                st.success(f"✅ hook_patterns.md에 레퍼런스 #{saved2} 자동 저장됨 — PC 재시작 후에도 유지")
            elif ref_script.strip():
                st.info("저장 블록을 찾지 못했습니다. 결과를 직접 확인해주세요.")

    st.divider()
    st.caption("💡 레퍼런스 원고 없이도 기존 학습 패턴으로 원고를 생성할 수 있습니다.")


# ── 탭 3: 전체 원고 ───────────────────────────────────────────────────
with tab_full:
    st.subheader("전체 원고 다듬기")
    st.caption("도입부·본문 초안을 주면 다듬어드리고, 개인가치·결론을 자동으로 생성합니다.")

    full_title = st.text_area(
        "유튜브 제목 — 제목을 넣으면 원고 방향이 정확해집니다",
        placeholder=(
            "예:\n"
            "유료강의에서 50만원 받고 가르치는 상세페이지 기획법, 걍 공개 | 스마트스토어 상세페이지 전환율\n"
            "셀러 99%가 모르는 상세페이지 최상단의 비밀 | 스마트스토어 상세페이지 만들기 전환율"
        ),
        height=100,
        key="full_title",
    )
    script_draft = st.text_area(
        "원고 초안 — 도입부+본문 전체를 한 번에 붙여넣기 하세요",
        placeholder="예: 지금 상세페이지 디자이너한테 의뢰하려던 분, 잠시만 멈추고 이것부터 보세요...\n\n(도입부와 본문을 구분 없이 전체 붙여넣기 하시면 됩니다. AI가 구조를 파악합니다.)",
        height=400,
        key="full_draft",
    )

    if st.button("✨ 원고 완성하기", key="full_btn", type="primary"):
        if not full_title.strip():
            st.warning("유튜브 제목을 입력해주세요.")
        elif not script_draft.strip():
            st.warning("원고 초안을 입력해주세요.")
        else:
            with st.spinner("Claude가 원고를 다듬는 중... (약 20~30초 소요)"):
                try:
                    result_full = call_full_script(full_title, script_draft, full_title)
                except Exception as e:
                    st.error(f"API 오류: {e}")
                    st.stop()

            st.markdown(result_full)
            st.session_state["full_script_result"] = result_full
            st.session_state["full_script_title"]  = full_title

    # PPT 다운로드 버튼 (원고가 생성된 경우에만 표시)
    if st.session_state.get("full_script_result"):
        st.divider()
        if st.button("📊 PPT로 만들기", key="ppt_btn"):
            with st.spinner("PPT 생성 중..."):
                try:
                    ppt_bytes = generate_ppt(
                        st.session_state["full_script_title"],
                        st.session_state["full_script_result"],
                    )
                except Exception as e:
                    st.error(f"PPT 생성 오류: {e}")
                    st.stop()
            st.download_button(
                label="⬇️ PPT 다운로드",
                data=ppt_bytes,
                file_name="로직해커엑스_원고.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                key="ppt_download",
            )

    st.divider()
    st.caption("💡 개인가치는 15가지 질문 중 영상 주제에 가장 맞는 1개를 AI가 자동 선택합니다.")
