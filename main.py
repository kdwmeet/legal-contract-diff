import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Contract Diff")

# 데이터 구조 정의
class ContractChange(BaseModel):
    article_name: str = Field(description="변경된 조항의 이름 또는 번호 (예: 제5조 배상책임)")
    original_text: str = Field(description="원래 계약서의 내용 요약")
    revised_text: str = Field(description="수정된 계약서의 내용 요약")
    risk_level: str = Field(description="리스크 수준 (High, Medium, Low)")
    analysis: str = Field(description="법적으로 어떤 의미가 변했는지, 왜 불리한지 설명")

class ContractAnalysisResult(BaseModel):
    changes: List[ContractChange] = Field(description="발견된 주요 변경 사항 목록")

# 분석 로직
def analyze_contracts(original, revised):
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)

    # LangChain이 Pydantic 객체를 알아서 JSON Schema로 변환해줌
    structured_llm = llm.with_structured_output(ContractAnalysisResult)

    system_prompt = (
        "당신은 전문 기업 변호사입니다. 두 개의 계약서(원안, 수정안)를 비교하여 "
        "상대방(수정안을 보낸 쪽)이 우리 측(을/수급사)에게 불리하게 변경한 독소 조항을 찾아내세요. "
        "단순한 오타 수정이나 문맥상 차이가 없는 변경은 무시하세요. "
        "법적 효력이나 책임 소재가 변경된 '중요한 차이'만 분석하세요."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "--- [원안 계약서] ---\n{original}\n\n--- [수정안 계약서] ---\n{revised}")
    ])

    chain = prompt | structured_llm

    return chain.invoke({"original": original, "revised": revised})

# UI 구성
st.title("AI 계약서 비교 분석기")

col1, col2 = st.columns(2)

sample_original = """
제5조 (손해배상)
1. '을'의 귀책사유로 인하여 '갑'에게 손해가 발생한 경우, '을'은 그 손해를 배상하여야 한다.
2. 손해배상의 범위는 통상손해에 한하며, 특별손해는 '을'이 알았거나 알 수 있었을 경우에만 책임진다.
3. 배상액의 총액은 본 계약금액의 100%를 초과할 수 없다.
"""

sample_revised = """
제5조 (손해배상 및 책임)
1. '을'은 본 계약과 관련하여 '갑'에게 발생한 모든 직/간접적 손해를 배상할 책임이 있다.
2. 손해배상의 범위에는 통상손해뿐만 아니라 일실수익을 포함한 모든 특별손해를 포함한다.
3. '을'의 고의 또는 중과실이 있는 경우 배상액의 한도는 없다.
"""

with col1:
    st.subheader("원안")
    original_text = st.text_area("원래 계약서 내용을 입력하세요", value=sample_original, height=300)

with col2:
    st.subheader("수정안")
    revised_text = st.text_area("상대방이 보낸 수정안을 입력하세요", value=sample_revised, height=300)

if st.button("리스크 분석 실행", type="primary"):
    if not original_text or not revised_text:
        st.error("두 계약서 내용을 모두 입력해주세요.")
    else:
        with st.spinner("변호사 AI가 두 계약서를 정밀 대조 중입니다..."):
            try:
                result = analyze_contracts(original_text, revised_text)

                st.divider()
                st.subheader("분석 리포트")

                if not result.changes:
                    st.success("특이한 리스크 조항이 발견되지 않았습니다.")

                for change in result.changes:
                    color = "red" if change.risk_level == "High" else "orange" if change.risk_level == "Medium" else "green"

                    with st.expander(f"[{change.risk_level}] {change.article_name}", expanded=True):
                        st.markdown(f"분석 결과: {color} [{change.analysis}]")

                        comp_col1, comp_col2 = st.columns(2)
                        with comp_col1:
                            st.info(f"원안 : \n{change.original_text}")
                        with comp_col2:
                            st.warning(f"수정안 :\n{change.revised_text}")
            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")

