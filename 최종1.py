import streamlit as st
import zipfile
import os
import json
import google.generativeai as genai
import tempfile

# Gemini API 설정
genai.configure(api_key="AIzaSyBTkrU0kHkXYNvNtOyAnH76diDtWqRm218")
model = genai.GenerativeModel("gemini-1.5-flash")

st.title("📦 ZIP 기반 논문·텍스트 분석 시스템")

uploaded_zip = st.file_uploader("JSON/텍스트 파일들이 들어있는 ZIP 파일을 업로드하세요", type=["zip"])
question = st.text_input("AI에게 물어볼 질문을 입력하세요:")

ask = st.button("질문하기")

if uploaded_zip and question and ask:
    try:
        context_list = []

        # 임시 폴더에 ZIP 파일 풀기
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            for filename in os.listdir(temp_dir):
                path = os.path.join(temp_dir, filename)

                # JSON 파일 처리
                if filename.lower().endswith(".json"):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                    except Exception as e:
                        st.warning(f"⚠️ {filename} 파싱 실패: {e}")
                        continue

                    # JSON 내 sections 가져오기
                    sections = (
                        data.get("packages", {})
                            .get("gpt", {})
                            .get("sections")
                        or data.get("sections")
                    )
                    if not sections:
                        st.warning(f"⚠️ {filename}에 'sections'가 없어 스킵합니다.")
                        continue

                    title    = sections.get("title", "")
                    abstract = sections.get("abstract", "")
                    method   = sections.get("methodology", "")
                    result   = sections.get("results", "")

                    context_list.append(
                        f"📄 제목: {title}\n"
                        f"[초록]\n{abstract}\n"
                        f"[방법론]\n{method}\n"
                        f"[결과]\n{result}\n"
                    )

                # 텍스트 파일 처리
                elif filename.lower().endswith(".txt"):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                    except Exception as e:
                        st.warning(f"⚠️ {filename} 읽기 실패: {e}")
                        continue

                    # 파일명을 제목으로 사용
                    title = os.path.splitext(filename)[0]
                    context_list.append(
                        f"📄 제목: {title}\n"
                        f"[내용]\n{content}\n"
                    )

                else:
                    # .json/.txt 외 파일은 무시
                    continue

        if not context_list:
            st.error("❗ 유효한 JSON/텍스트 데이터를 찾지 못했습니다.")
        else:
            # 분석에 사용할 전체 컨텍스트 조합
            full_context = "\n\n---\n\n".join(context_list)
            prompt = (
                "다음은 여러 논문(JSON) 및 텍스트 파일에서 추출한 핵심 내용입니다. "
                "이 내용을 바탕으로 아래 질문에 답해주세요.\n\n"
                f"{full_context}\n\n"
                "[질문]\n"
                f"{question}"
            )
            response = model.generate_content(prompt)
            st.subheader("🧠 AI의 응답:")
            st.write(response.text)

    except Exception as e:
        st.error(f"❗ 오류 발생: {str(e)}")
