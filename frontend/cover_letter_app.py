"""자소서 작성 자동화 — Streamlit 5단계 위자드."""

import streamlit as st

from cover_letter import (
    company_service,
    generation_service,
    jd_service,
    mapping_service,
    profile_service,
    question_service,
)

st.set_page_config(page_title="자소서 도우미", page_icon="✍️", layout="centered")

STEPS = [
    "프로필 등록",
    "기업·직무 분석",
    "문항 분석",
    "경험-문항 매핑",
    "답변 생성",
]


def _init_session() -> None:
    """session_state 초기화."""
    defaults: dict = {
        "step": 0,
        "profile": None,
        "company_analysis": None,
        "job_analysis": None,
        "questions": [],
        "mappings": {},
        "drafts": {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _render_progress() -> None:
    """상단 진행 표시줄 렌더링."""
    step = st.session_state["step"]
    st.progress((step) / (len(STEPS) - 1) if len(STEPS) > 1 else 1.0)
    cols = st.columns(len(STEPS))
    for i, name in enumerate(STEPS):
        label = f"**{name}**" if i == step else name
        cols[i].markdown(label, unsafe_allow_html=False)


# ============================================================
# Step 0: 프로필 등록
# ============================================================
def render_step0() -> None:
    """Step 0: 사용자 프로필 등록."""
    st.subheader("Step 1: 프로필 등록")
    st.caption(
        "경력 자료(포트폴리오, 이전 자소서 등)를 업로드하거나 직접 붙여넣으세요."
    )

    tab_upload, tab_paste = st.tabs(["📁 파일 업로드", "✏️ 텍스트 붙여넣기"])

    with tab_upload:
        uploaded = st.file_uploader(
            "파일을 업로드하세요 (TXT·MD·DOCX, 여러 파일 가능)",
            type=["txt", "md", "docx"],
            accept_multiple_files=True,
        )

    with tab_paste:
        pasted_text = st.text_area(
            "경력 자료를 여기에 붙여넣으세요",
            height=200,
            placeholder="인턴 경험, 프로젝트, 수상 이력 등을 자유롭게 입력하세요.",
        )

    # 기존 프로필 로드
    existing_profile = profile_service.load_profile()
    if existing_profile:
        st.info(
            "💾 저장된 프로필이 있습니다. 새 자료를 추가하면 기존 프로필과 병합됩니다."
        )

    if st.button("🔍 프로필 추출", type="primary"):
        texts: list[str] = []

        # 파일 업로드 처리
        file_names: list[str] = []
        if uploaded:
            for f in uploaded:
                try:
                    text = profile_service.parse_input(None, f.read(), filename=f.name)
                    texts.append(text)
                    file_names.append(f.name)
                except ValueError:
                    st.warning(f"'{f.name}'은 빈 파일입니다. 건너뜁니다.")

        # 텍스트 붙여넣기 처리
        if pasted_text and pasted_text.strip():
            try:
                text = profile_service.parse_input(pasted_text, None)
                texts.append(text)
            except ValueError:
                pass

        if not texts:
            st.error("파일 또는 텍스트 중 하나 이상을 입력해 주세요.")
            return

        with st.spinner("프로필을 분석하고 있습니다..."):
            try:
                if existing_profile:
                    profile = profile_service.merge_profile(existing_profile, texts)
                else:
                    profile = profile_service.extract_profile(texts)
                if file_names:
                    profile["source_files"] = (
                        existing_profile.get("source_files", [])
                        if existing_profile
                        else []
                    ) + file_names
            except RuntimeError as e:
                st.error(f"프로필 추출 실패: {e}")
                return

        st.session_state["profile"] = profile
        st.success("프로필 추출 완료! 아래에서 내용을 검토하고 수정하세요.")

    # 프로필 검토 및 수정 UI
    profile = st.session_state.get("profile") or existing_profile
    if profile:
        _render_profile_editor(profile)


def _render_profile_editor(profile: dict) -> None:
    """추출된 프로필 검토/수정 UI."""
    st.divider()
    st.subheader("📋 추출된 프로필 검토")

    # 경험 목록
    st.markdown("#### 경험 목록")
    experiences = profile.get("experiences", [])
    updated_experiences = []
    for i, exp in enumerate(experiences):
        with st.expander(
            f"경험 {i + 1}: {exp.get('title', '제목 없음')}", expanded=(i == 0)
        ):
            col1, col2 = st.columns([3, 1])
            title = col1.text_input(
                "활동명", value=exp.get("title", ""), key=f"exp_title_{i}"
            )
            period = col2.text_input(
                "기간", value=exp.get("period", ""), key=f"exp_period_{i}"
            )
            description = st.text_area(
                "내용",
                value=exp.get("description", ""),
                height=100,
                key=f"exp_desc_{i}",
            )
            comps = st.text_input(
                "역량 (쉼표 구분)",
                value=", ".join(exp.get("competencies", [])),
                key=f"exp_comp_{i}",
            )
            remove = st.checkbox("이 경험 삭제", key=f"exp_remove_{i}")

        if not remove:
            updated_experiences.append(
                {
                    "key": exp.get("key", f"exp_{i + 1:02d}"),
                    "title": title,
                    "period": period,
                    "description": description,
                    "competencies": [c.strip() for c in comps.split(",") if c.strip()],
                }
            )

    # 핵심 역량
    st.markdown("#### 핵심 역량")
    competencies_str = st.text_area(
        "핵심 역량 (줄바꿈으로 구분)",
        value="\n".join(profile.get("competencies", [])),
        height=100,
    )

    # 저장 버튼
    st.divider()
    if st.button("✅ 프로필 저장 및 다음 단계로", type="primary"):
        profile["experiences"] = updated_experiences
        profile["competencies"] = [
            c.strip() for c in competencies_str.split("\n") if c.strip()
        ]
        st.session_state["profile"] = profile

        with st.spinner("저장 중..."):
            try:
                profile_service.save_profile(profile)
            except Exception as e:
                st.error(f"DB 저장 실패: {e}")
                return

        st.success("프로필이 저장되었습니다!")
        st.session_state["step"] = 1
        st.rerun()


# ============================================================
# Step 1~4: Placeholder (Phase 4~6에서 구현)
# ============================================================
def render_step1() -> None:
    """Step 2: 기업·직무 분석."""
    st.subheader("Step 2: 기업·직무 분석")
    st.caption(
        "기업명과 지원 직무를 입력하면 3개 소스(DART·뉴스·홈페이지)를 분석합니다."
    )

    col1, col2 = st.columns(2)
    company_name = col1.text_input("기업명", placeholder="예: 카카오, 당근마켓")
    job_title = col2.text_input("지원 직무", placeholder="예: 백엔드 개발자")

    if st.button(
        "🔍 기업·직무 분석 시작",
        type="primary",
        disabled=not (company_name and job_title),
    ):
        with st.spinner(
            f"'{company_name}' 기업을 분석하는 중... (최초 분석 시 30~60초 소요)"
        ):
            try:
                company_analysis = company_service.get_or_analyze_company(company_name)
                if company_analysis.get("analyzed_at"):
                    st.info("💾 이전 분석 결과를 재사용합니다 (7일 이내 캐시).")
            except Exception as e:
                st.error(f"기업 분석 실패: {e}")
                return

        with st.spinner(f"'{job_title}' 직무를 분석하는 중..."):
            try:
                job_analysis = company_service.analyze_job(
                    company_analysis["id"], job_title
                )
            except Exception as e:
                st.error(f"직무 분석 실패: {e}")
                return

        st.session_state["company_analysis"] = company_analysis
        st.session_state["job_analysis"] = job_analysis
        st.success("분석 완료!")

    # 분석 결과 검토 UI
    ca = st.session_state.get("company_analysis")
    ja = st.session_state.get("job_analysis")

    if ca and ja:
        _render_company_job_editor(ca, ja)


def _render_company_job_editor(ca: dict, ja: dict) -> None:
    """기업·직무 분석 결과 검토/수정 UI."""
    st.divider()
    st.subheader(f"📊 {ca['company_name']} 분석 결과")

    with st.expander("기업 개요", expanded=True):
        overview = st.text_area(
            "기업 개요", value=ca.get("overview", ""), height=100, key="ca_overview"
        )
    with st.expander("인재상·기업 문화"):
        culture = st.text_area(
            "인재상·기업 문화",
            value=ca.get("culture_and_values", ""),
            height=80,
            key="ca_culture",
        )
    with st.expander("업계 동향"):
        trends = st.text_area(
            "업계 동향", value=ca.get("industry_trends", ""), height=80, key="ca_trends"
        )
    with st.expander("DART 사업보고서 요약"):
        dart = st.text_area(
            "DART 요약", value=ca.get("dart_summary", ""), height=80, key="ca_dart"
        )
    with st.expander("직무 분석"):
        responsibilities = st.text_area(
            "주요 업무", value=ja.get("responsibilities", ""), height=80, key="ja_resp"
        )
        pain_points = st.text_area(
            "직무 페인 포인트",
            value=ja.get("pain_points", ""),
            height=80,
            key="ja_pain",
        )

    # JD 섹션: 자동 수집 결과 or 수기 입력 폼
    with st.expander("📋 직무기술서(JD)"):
        jd_data = st.session_state.get("jd_data")
        if jd_data is None:
            jd_data = jd_service.load_jd(ja["id"])
            if jd_data:
                st.session_state["jd_data"] = jd_data

        if jd_data and jd_data.get("raw_text"):
            source_badge = {
                "firecrawl": "🌐 Firecrawl 자동 수집",
                "pdf": "📄 PDF 자동 수집",
                "manual": "✏️ 수기 입력",
            }.get(jd_data.get("source_type", ""), "")
            st.caption(f"{source_badge} | {jd_data.get('source_url', '')}")
            competencies = jd_data.get("required_competencies", [])
            if competencies:
                st.markdown("**요구 역량:** " + " · ".join(competencies))
            st.text_area(
                "JD 원문",
                value=jd_data.get("raw_text", ""),
                height=150,
                key="jd_raw",
            )
        else:
            st.info("JD 자동 수집에 실패했습니다. 직접 입력하거나 생략할 수 있습니다.")
            manual_jd = st.text_area(
                "JD 수기 입력 (선택)",
                height=150,
                placeholder="채용공고에서 직무 기술서를 복사·붙여넣으세요.",
                key="jd_manual",
            )
            if st.button("💾 JD 저장", key="jd_save"):
                if manual_jd.strip():
                    saved_id = jd_service.save_jd(
                        ja["id"],
                        {
                            "success": True,
                            "text": manual_jd.strip(),
                            "source_url": "",
                            "source_type": "manual",
                            "required_competencies": [],
                        },
                    )
                    st.session_state["jd_data"] = jd_service.load_jd(ja["id"])
                    st.success(f"JD 저장 완료 (ID: {saved_id})")
                    st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 수정 내용 저장"):
            company_service.save_overrides(
                "company",
                ca["id"],
                {
                    "overview": overview,
                    "culture_and_values": culture,
                    "industry_trends": trends,
                    "dart_summary": dart,
                },
            )
            company_service.save_overrides(
                "job",
                ja["id"],
                {
                    "responsibilities": responsibilities,
                    "pain_points": pain_points,
                },
            )
            st.success("저장됨")

    with col2:
        if st.button("✅ 다음 단계로 (문항 분석)", type="primary"):
            st.session_state["step"] = 2
            st.rerun()

    if st.button("← 이전 단계 (프로필 등록)"):
        st.session_state["step"] = 0
        st.rerun()


def render_step2() -> None:
    """Step 3: 문항 분석."""
    st.subheader("Step 3: 문항 분석")
    st.caption("자소서 문항을 입력하면 측정 역량과 기대 수준을 분석합니다.")

    ja = st.session_state.get("job_analysis")
    if not ja:
        st.warning("먼저 기업·직무 분석을 완료해 주세요.")
        if st.button("← 기업·직무 분석으로"):
            st.session_state["step"] = 1
            st.rerun()
        return

    question_text = st.text_area(
        "문항 입력",
        height=120,
        placeholder="예: 지원 동기와 자신의 강점을 중심으로 기술하세요.",
    )
    char_limit = st.number_input(
        "글자 수 제한 (없으면 0 입력)", min_value=0, value=0, step=100
    )
    char_limit_val = int(char_limit) if char_limit > 0 else None

    if st.button("🔍 문항 분석", type="primary", disabled=not question_text):
        with st.spinner("문항을 분석하는 중..."):
            try:
                question = question_service.analyze_question(
                    ja["id"], question_text, char_limit_val
                )
            except Exception as e:
                st.error(f"문항 분석 실패: {e}")
                return

        questions = st.session_state.get("questions", [])
        questions.append(question)
        st.session_state["questions"] = questions
        st.success("문항 분석 완료!")

    questions = st.session_state.get("questions", [])
    if questions:
        st.divider()
        st.subheader("📝 분석된 문항 목록")
        for i, q in enumerate(questions):
            with st.expander(
                f"문항 {i + 1}: {q['text'][:50]}...", expanded=(i == len(questions) - 1)
            ):
                st.markdown(
                    f"**측정 역량**: {', '.join(q.get('measured_competencies', []))}"
                )
                st.markdown(f"**기대 수준**: {q.get('expected_level', '')}")
                if q.get("char_limit"):
                    st.markdown(
                        f"**글자 수**: {q['target_char_min']}~{q['target_char_max']}자 목표"
                    )
        st.info(
            f"현재 {len(questions)}개 문항이 분석되었습니다. 더 추가하거나 다음 단계로 진행하세요."
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 이전 단계 (기업·직무 분석)"):
            st.session_state["step"] = 1
            st.rerun()
    with col2:
        if st.button(
            "✅ 다음 단계로 (경험-문항 매핑)", type="primary", disabled=not questions
        ):
            st.session_state["step"] = 3
            st.rerun()


def render_step3() -> None:
    """Step 4: 경험-문항 매핑."""
    st.subheader("Step 4: 경험-문항 매핑")

    profile = st.session_state.get("profile")
    job_analysis = st.session_state.get("job_analysis")
    company_analysis = st.session_state.get("company_analysis")
    questions = st.session_state.get("questions", [])

    if not profile or not job_analysis or not questions:
        st.warning("이전 단계를 먼저 완료해 주세요.")
        if st.button("← 이전 단계"):
            st.session_state["step"] = 2
            st.rerun()
        return

    experiences = profile.get("experiences", [])
    if not experiences:
        st.error("프로필에 경험 정보가 없습니다. Step 1로 돌아가 프로필을 수정하세요.")
        if st.button("← 이전 단계"):
            st.session_state["step"] = 2
            st.rerun()
        return

    mappings: dict = st.session_state.get("mappings", {})

    # 아직 매핑이 없는 문항에 대해 LLM 자동 생성
    unmapped = [q for q in questions if str(q["id"]) not in mappings]
    if unmapped:
        if st.button("🤖 LLM으로 매핑 자동 생성", type="primary"):
            with st.spinner("경험-문항 적합도 평가 중..."):
                for q in unmapped:
                    entries = mapping_service.generate_mapping(
                        question_id=q["id"],
                        question_text=q["text"],
                        measured_competencies=q.get("measured_competencies", []),
                        expected_level=q.get("expected_level", ""),
                        company_name=company_analysis.get("company_name", ""),
                        job_title=job_analysis.get("job_title", ""),
                        culture_and_values=company_analysis.get(
                            "culture_and_values", ""
                        ),
                        experiences=experiences,
                    )
                    mappings[str(q["id"])] = {
                        "question_text": q["text"],
                        "entries": entries,
                    }
                st.session_state["mappings"] = mappings
            st.rerun()
        return

    # 매핑 결과 표시 + 편집
    # 중복 검증
    all_mappings_for_check = [
        {
            "question_id": q["id"],
            "question_text": q["text"],
            "entries": mappings.get(str(q["id"]), {}).get("entries", []),
        }
        for q in questions
    ]
    warnings = mapping_service.validate_duplicates(all_mappings_for_check)
    if warnings:
        st.warning("⚠️ 경험 중복 사용 감지")
        for w in warnings:
            q_texts = " / ".join(f"Q{q['id']}" for q in w["questions"])
            st.caption(
                f"경험 `{w['experience_key']}` ({w['usage_type']})이 복수 문항에 사용됨: {q_texts}"
            )

    for q in questions:
        q_id = str(q["id"])
        q_mapping = mappings.get(q_id, {})
        entries = q_mapping.get("entries", [])

        with st.expander(f"📝 {q['text'][:60]}...", expanded=True):
            if not entries:
                st.info("적합한 경험 매핑이 없습니다 (score < 3).")
            else:
                for i, entry in enumerate(entries):
                    cols = st.columns([3, 1, 1])
                    with cols[0]:
                        exp = next(
                            (
                                e
                                for e in experiences
                                if e.get("key") == entry.get("experience_key")
                            ),
                            None,
                        )
                        exp_title = (
                            exp["title"] if exp else entry.get("experience_key", "")
                        )
                        st.markdown(f"**{exp_title}** — {entry.get('rationale', '')}")
                    with cols[1]:
                        new_usage = st.selectbox(
                            "활용 유형",
                            ["primary", "supporting", "background"],
                            index=["primary", "supporting", "background"].index(
                                entry.get("usage_type", "supporting")
                            ),
                            key=f"usage_{q_id}_{i}",
                        )
                        entries[i]["usage_type"] = new_usage
                    with cols[2]:
                        st.metric("적합도", f"{entry.get('relevance_score', 0)}/5")

    # 저장 + 다음 단계
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 이전 단계"):
            st.session_state["step"] = 2
            st.rerun()
    with col2:
        if st.button("✅ 매핑 확정 후 답변 생성", type="primary"):
            with st.spinner("매핑 저장 중..."):
                for q in questions:
                    q_id = str(q["id"])
                    entries = mappings.get(q_id, {}).get("entries", [])
                    if entries:
                        mapping_id = mapping_service.save_mapping(q["id"], entries)
                        mappings[q_id]["mapping_table_id"] = mapping_id
                st.session_state["mappings"] = mappings
            st.session_state["step"] = 4
            st.rerun()


def render_step4() -> None:
    """Step 5: 답변 생성 + 자가진단."""
    st.subheader("Step 5: 답변 생성")

    profile = st.session_state.get("profile")
    company_analysis = st.session_state.get("company_analysis")
    job_analysis = st.session_state.get("job_analysis")
    questions = st.session_state.get("questions", [])
    mappings = st.session_state.get("mappings", {})
    drafts: dict = st.session_state.get("drafts", {})

    if not profile or not company_analysis or not questions:
        st.warning("이전 단계를 먼저 완료해 주세요.")
        if st.button("← 이전 단계"):
            st.session_state["step"] = 3
            st.rerun()
        return

    for q in questions:
        q_id = str(q["id"])
        q_mapping = mappings.get(q_id, {})
        entries = q_mapping.get("entries", [])
        mapping_table_id = q_mapping.get("mapping_table_id")
        draft_info = drafts.get(q_id, {})

        with st.expander(f"📝 {q['text'][:60]}...", expanded=True):
            col_char = st.columns([2, 1])
            with col_char[0]:
                st.caption(
                    f"글자 수 제한: {q.get('char_limit', '—')}자 / "
                    f"목표: {q.get('target_char_min', '—')}~{q.get('target_char_max', '—')}자"
                )

            # 초안 생성
            if not draft_info.get("text"):
                user_instruction = st.text_area(
                    "작성 지시 (선택 사항)",
                    placeholder="예: 더 구체적인 수치를 포함하세요",
                    key=f"instr_{q_id}",
                    height=60,
                )
                if st.button("✍️ 초안 생성", key=f"gen_{q_id}", type="primary"):
                    with st.spinner("답변 생성 중... (최대 3회 시도)"):
                        result = generation_service.generate_answer(
                            question_id=q["id"],
                            question_text=q["text"],
                            char_limit=q.get("char_limit", 1000),
                            target_char_min=q.get("target_char_min", 800),
                            target_char_max=q.get("target_char_max", 950),
                            measured_competencies=q.get("measured_competencies", []),
                            expected_level=q.get("expected_level", ""),
                            company_analysis=company_analysis,
                            job_analysis=job_analysis,
                            profile=profile,
                            mapping_entries=entries,
                            user_instruction=user_instruction,
                        )
                        drafts[q_id] = result
                        drafts[q_id]["mapping_table_id"] = mapping_table_id
                        drafts[q_id]["version"] = 1
                        drafts[q_id]["status"] = "draft"
                        st.session_state["drafts"] = drafts
                    st.rerun()
            else:
                # 초안 표시
                text = draft_info["text"]
                char_count = draft_info.get("char_count", len(text))
                in_range = draft_info.get("in_range", False)
                attempt = draft_info.get("attempt", 1)

                range_icon = "✅" if in_range else "⚠️"
                st.info(
                    f"{range_icon} {char_count}자 (시도 {attempt}회) — {'범위 내' if in_range else '범위 초과'}"
                )
                st.text_area("생성된 답변", value=text, height=200, key=f"draft_{q_id}")

                # 자가진단
                diag_issues = draft_info.get("diagnosis_issues")
                if st.button("🔍 자가진단", key=f"diag_{q_id}"):
                    with st.spinner("답변 품질 진단 중..."):
                        issues = generation_service.run_self_diagnosis(
                            draft_text=text,
                            question_text=q["text"],
                            target_char_min=q.get("target_char_min", 800),
                            target_char_max=q.get("target_char_max", 950),
                            measured_competencies=q.get("measured_competencies", []),
                        )
                        drafts[q_id]["diagnosis_issues"] = issues
                        st.session_state["drafts"] = drafts
                    st.rerun()

                if diag_issues is not None:
                    if diag_issues:
                        st.warning(f"⚠️ {len(diag_issues)}개 문제 발견")
                        for issue in diag_issues:
                            st.markdown(
                                f"- **[{issue['issue']}]** `{issue['text']}` → {issue['suggestion']}"
                            )
                    else:
                        st.success("✅ 문제 없음")

                # 환각 검증
                hallucination_result = draft_info.get("hallucination_detected")
                hallucination_retries = draft_info.get("hallucination_retries", 0)
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    if st.button("🔎 환각 검증", key=f"hall_{q_id}"):
                        with st.spinner("환각 여부 검증 중..."):
                            detected = generation_service.check_hallucination(
                                answer_text=text,
                                mapping_entries=entries,
                                profile=profile,
                            )
                            drafts[q_id]["hallucination_detected"] = detected
                            st.session_state["drafts"] = drafts
                        st.rerun()
                with col_h2:
                    if hallucination_result and st.button(
                        "♻️ 환각 없이 재생성", key=f"hallregen_{q_id}"
                    ):
                        with st.spinner("환각 없는 답변 재생성 중..."):
                            hall_result = (
                                generation_service.regenerate_without_hallucination(
                                    answer_params=dict(
                                        question_id=q["id"],
                                        question_text=q["text"],
                                        char_limit=q.get("char_limit", 1000),
                                        target_char_min=q.get("target_char_min", 800),
                                        target_char_max=q.get("target_char_max", 950),
                                        measured_competencies=q.get(
                                            "measured_competencies", []
                                        ),
                                        expected_level=q.get("expected_level", ""),
                                        company_analysis=company_analysis,
                                        job_analysis=job_analysis,
                                        profile=profile,
                                        mapping_entries=entries,
                                    ),
                                    mapping_entries=entries,
                                    profile=profile,
                                )
                            )
                            drafts[q_id]["text"] = hall_result["text"]
                            drafts[q_id]["hallucination_retries"] = (
                                hallucination_retries
                                + hall_result["hallucination_retries"]
                            )
                            drafts[q_id]["hallucination_detected"] = hall_result[
                                "hallucination_detected"
                            ]
                            drafts[q_id]["char_count"] = len(hall_result["text"])
                            st.session_state["drafts"] = drafts
                        st.rerun()

                if hallucination_result is True:
                    st.error("🚨 환각 감지: 경험 목록에 없는 내용이 포함되었습니다.")
                elif hallucination_result is False:
                    st.success("✅ 환각 없음")

                # 수동 지시 + 재생성
                user_instruction = st.text_area(
                    "수정 지시",
                    placeholder="예: 3번째 문장을 더 구체적으로 바꾸세요",
                    key=f"reinstr_{q_id}",
                    height=60,
                )
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🔄 재생성", key=f"regen_{q_id}"):
                        with st.spinner("재생성 중..."):
                            result = generation_service.apply_diagnosis_and_regenerate(
                                question_id=q["id"],
                                draft_text=text,
                                diagnosis_issues=diag_issues or [],
                                user_instruction=user_instruction,
                                question_text=q["text"],
                                char_limit=q.get("char_limit", 1000),
                                target_char_min=q.get("target_char_min", 800),
                                target_char_max=q.get("target_char_max", 950),
                                measured_competencies=q.get(
                                    "measured_competencies", []
                                ),
                                expected_level=q.get("expected_level", ""),
                                company_analysis=company_analysis,
                                job_analysis=job_analysis,
                                profile=profile,
                                mapping_entries=entries,
                            )
                            result["version"] = draft_info.get("version", 1) + 1
                            result["mapping_table_id"] = mapping_table_id
                            result["status"] = "draft"
                            drafts[q_id] = result
                            st.session_state["drafts"] = drafts
                        st.rerun()

                with col_btn2:
                    if st.button("✅ 확정", key=f"confirm_{q_id}", type="primary"):
                        with st.spinner("저장 중..."):
                            draft_id = generation_service.confirm_draft(
                                question_id=q["id"],
                                mapping_table_id=mapping_table_id,
                                text=text,
                                self_diagnosis_issues=diag_issues or [],
                                generation_params={
                                    "attempt": attempt,
                                    "version": draft_info.get("version", 1),
                                },
                                version=draft_info.get("version", 1),
                                hallucination_retries=draft_info.get(
                                    "hallucination_retries", 0
                                ),
                            )
                            drafts[q_id]["status"] = "confirmed"
                            drafts[q_id]["draft_id"] = draft_id
                            st.session_state["drafts"] = drafts
                        st.success(f"저장 완료 (ID: {draft_id})")
                        st.rerun()

    # 하단 네비게이션
    if st.button("← 이전 단계"):
        st.session_state["step"] = 3
        st.rerun()


# ============================================================
# 메인 라우터
# ============================================================
def main() -> None:
    """앱 진입점."""
    st.title("✍️ 자소서 도우미")
    _init_session()
    _render_progress()
    st.divider()

    step = st.session_state["step"]
    renderers = [render_step0, render_step1, render_step2, render_step3, render_step4]
    renderers[step]()


if __name__ == "__main__":
    main()
