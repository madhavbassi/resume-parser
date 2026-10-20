import streamlit as st
from pathlib import Path
from tempfile import NamedTemporaryFile

from main import (
    read_resume,
    parse_resume,
    parse_job_description,
    final_score,
)


# ----------------------------
# Page configuration
# ----------------------------

st.set_page_config(
    page_title="ResumeAI | Resume Matcher",
    page_icon="📄",
    layout="wide",
)

st.title("📄 ResumeAI")
st.caption("AI-powered resume parsing and job matching")

st.divider()


# ----------------------------
# Input section
# ----------------------------

left, right = st.columns(2)

with left:
    st.subheader("Upload your resume")

    uploaded_file = st.file_uploader(
        "Choose a PDF or DOCX file",
        type=["pdf", "docx"],
    )

with right:
    st.subheader("Job description")

    job_description = st.text_area(
        "Paste the job description",
        placeholder="Paste the role, responsibilities, and required skills...",
        height=220,
    )

analyze_clicked = st.button(
    "Analyze Resume",
    type="primary",
    use_container_width=True,
)


# ----------------------------
# Analysis section
# ----------------------------

if analyze_clicked:

    if uploaded_file is None:
        st.warning("Please upload a resume.")

    elif not job_description.strip():
        st.warning("Please enter a job description.")

    else:
        suffix = Path(uploaded_file.name).suffix.lower()
        temp_path = None

        try:
            # Save the uploaded file temporarily
            with NamedTemporaryFile(
                suffix=suffix,
                delete=False,
            ) as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_path = Path(temp_file.name)

            # Parse the resume
            with st.spinner("Analyzing your resume..."):
                resume_text = read_resume(temp_path)

                if not resume_text or not resume_text.strip():
                    st.error(
                        "No readable text was found in the resume. "
                        "Try a text-based PDF or DOCX file."
                    )
                    st.stop()

                parsed_resume = parse_resume(resume_text)

            # Parse the job description
            with st.spinner("Understanding the job description..."):
                parsed_job = parse_job_description(job_description)

            # Calculate the match score
            with st.spinner("Calculating your match score..."):
                match_result = final_score(
                    parsed_job,
                    parsed_resume,
                )

            # ----------------------------
            # Display results
            # ----------------------------

            st.success("Resume analysis completed!")

            st.subheader(
                getattr(parsed_resume, "name", None)
                or "Candidate Analysis"
            )

            score = float(match_result.score)

            st.metric(
                "Estimated Match Score",
                f"{score:.1f}%",
            )

            st.progress(
                max(0.0, min(score / 100.0, 1.0))
            )

            details = match_result.details or {}

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Matching skills")

                matching_skills = details.get(
                    "matching_skills", []
                )

                if matching_skills:
                    for skill in matching_skills:
                        st.markdown(f"- ✅ {skill}")
                else:
                    st.write(
                        "No matching skills were returned."
                    )

            with col2:
                st.subheader("Skills to develop")

                missing_skills = details.get(
                    "missing_important_skills", []
                )

                if missing_skills:
                    for skill in missing_skills:
                        st.markdown(f"- 📌 {skill}")
                else:
                    st.write(
                        "No missing skills were returned."
                    )

            st.subheader("Match summary")

            st.write(
                details.get(
                    "final_verdict",
                    "No summary was returned.",
                )
            )

            st.caption(
                "The match score is an AI-generated estimate, "
                "not an objective measure of candidate suitability."
            )

            with st.expander(
                "View extracted resume information"
            ):
                st.json(parsed_resume.model_dump())

            with st.expander(
                "View extracted job requirements"
            ):
                st.json(parsed_job.model_dump())

        except Exception as error:
            st.error(
                f"Analysis failed: {type(error).__name__}: {error}"
            )
            st.exception(error)

        finally:
            # Remove the temporary file
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)