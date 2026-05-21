import streamlit as st
from analyzer import analyze_resume
import base64
import matplotlib.pyplot as plt

# PDF
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="ATS Resume Analyzer", layout="wide")
st.title("🚀 ATS Resume Analyzer")

# ---------- STATE ----------
if "mode" not in st.session_state:
    st.session_state.mode = "Select"

if "jd" not in st.session_state:
    st.session_state.jd = ""

# ---------- MODE SELECT (HOME FIX) ----------
mode = st.radio(
    "Select Mode",
    ["Select", "Single Resume", "Multiple Resume"],
    index=0
)

# ---------- RESET ON MODE CHANGE ----------
if mode != st.session_state.mode:
    st.session_state.mode = mode

    # clear uploads
    for key in ["single_file", "multi_file"]:
        if key in st.session_state:
            del st.session_state[key]

    # clear JD (🔥 main fix)
    st.session_state.jd = ""

    st.rerun()

files = []

# ---------- SINGLE ----------
if mode == "Single Resume":
    file = st.file_uploader(
        "Upload ONE Resume",
        type=["pdf"],
        key="single_file",
        accept_multiple_files=False
    )
    if file:
        files = [file]

# ---------- MULTIPLE ----------
elif mode == "Multiple Resume":
    files = st.file_uploader(
        "Upload Multiple Resumes",
        type=["pdf"],
        key="multi_file",
        accept_multiple_files=True
    )

# ---------- JD ----------
jd_text = st.text_area(
    "Paste Job Description (Optional)",
    key="jd"
)

# ---------- PDF FUNCTION (UNCHANGED FEATURE) ----------
def generate_pdf(file_name, result):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("<b>ATS Resume Report</b>", styles["Title"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"<b>Resume:</b> {file_name}", styles["Normal"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"<b>Resume Domain:</b> {result['resume_domain']}", styles["Normal"]))
    story.append(Paragraph(f"<b>JD Domain:</b> {result['jd_domain']}", styles["Normal"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Score:</b> {result['score']}%", styles["Normal"]))
    story.append(Paragraph(f"<b>JD Score:</b> {result['jd_score']}%", styles["Normal"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Matched Skills:</b>", styles["Heading3"]))
    story.append(Paragraph(", ".join(result["matched"]) or "None", styles["Normal"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Missing Skills:</b>", styles["Heading3"]))
    story.append(Paragraph(", ".join(result["missing"]) or "None", styles["Normal"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Repeated Words:</b>", styles["Heading3"]))

    if result["repeated"]:
        for w, c in result["repeated"].items():
            story.append(Paragraph(f"{w} → {c} times", styles["Normal"]))
    else:
        story.append(Paragraph("No repetition", styles["Normal"]))

    # Chart inside PDF
    labels = ["Matched", "Missing", "JD"]
    values = [len(result["matched"]), len(result["missing"]), result["jd_score"]]

    fig, ax = plt.subplots()
    ax.bar(labels, values)

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close(fig)
    img_buffer.seek(0)

    story.append(Spacer(1, 20))
    story.append(Image(img_buffer, width=300, height=180))

    doc.build(story)
    return buffer.getvalue()

# ---------- ANALYZE ----------
if st.button("Analyze"):

    if mode == "Select":
        st.warning("Select mode first")
        st.stop()

    if not files:
        st.warning("Upload resume first")
        st.stop()

    for file in files:

        st.divider()
        st.subheader(f"📄 {file.name}")

        result = analyze_resume(file, jd_text)

        col1, col2 = st.columns([1.3, 1])

        # PDF VIEW
        with col1:
            st.markdown("### 📄 Resume View")

            try:
                file.seek(0)
                pdf_bytes = file.read()
                base64_pdf = base64.b64encode(pdf_bytes).decode()

                st.markdown(
                    f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500"></iframe>',
                    unsafe_allow_html=True
                )
            except:
                st.error("PDF preview failed")

        # RESULTS (UNCHANGED)
        with col2:

            st.markdown("### 🎯 Domain Analysis")

            # ---------- DOMAIN CARD ----------
            if result["resume_domain"] == result["jd_domain"]:
                domain_color = "#22c55e"
                domain_bg = "#dcfce7"
                domain_text = f"✔ MATCHED — {result['resume_domain']}"
            else:
                domain_color = "#ef4444"
                domain_bg = "#fee2e2"
                domain_text = f"❌ NOT MATCHED (Resume: {result['resume_domain']} | JD: {result['jd_domain']})"

            st.markdown(f"""
            <div style="
                background:{domain_bg};
                padding:15px;
                border-radius:12px;
                border-left:6px solid {domain_color};
                margin-bottom:10px;">
                <b>{domain_text}</b>
            </div>
            """, unsafe_allow_html=True)


            # ---------- SCORE COLOR LOGIC ----------
            def score_color(score):
                if score >= 75:
                    return "#22c55e", "#dcfce7"
                elif score >= 50:
                    return "#eab308", "#fef9c3"
                else:
                    return "#ef4444", "#fee2e2"


            # ---------- ATS SCORE ----------
            c, bg = score_color(result["score"])
            st.markdown("### 📊 ATS Score")
            st.markdown(f"""
            <div style="
                background:{bg};
                padding:15px;
                border-radius:12px;
                border-left:6px solid {c};
                font-size:18px;
                font-weight:bold;">
                {result['score']}%
            </div>
            """, unsafe_allow_html=True)

            # ---------- JD SCORE ----------
            c, bg = score_color(result["jd_score"])
            st.markdown("### 📌 JD Match Score")
            st.markdown(f"""
            <div style="
                background:{bg};
                padding:15px;
                border-radius:12px;
                border-left:6px solid {c};
                font-size:18px;
                font-weight:bold;">
                {result['jd_score']}%
            </div>
            """, unsafe_allow_html=True)

            # ---------- MATCHED SKILLS ----------
            st.markdown("### ✔ Matched Skills")

            matched_html = "".join([
                f"<span style='background:#22c55e;color:white;padding:5px 10px;margin:5px;border-radius:8px;display:inline-block;'>{s}</span>"
                for s in result["matched"]
            ]) or "None"

            st.markdown(f"""
            <div style="
                background:#f0fdf4;
                padding:10px;
                border-radius:12px;
                border:1px solid #22c55e;">
                {matched_html}
            </div>
            """, unsafe_allow_html=True)

            # ---------- MISSING SKILLS ----------
            st.markdown("### ✖ Missing Skills")

            missing_html = "".join([
                f"<span style='background:#ef4444;color:white;padding:5px 10px;margin:5px;border-radius:8px;display:inline-block;'>{s}</span>"
                for s in result["missing"]
            ]) or "None"

            st.markdown(f"""
            <div style="
                background:#fef2f2;
                padding:10px;
                border-radius:12px;
                border:1px solid #ef4444;">
                {missing_html}
            </div>
            """, unsafe_allow_html=True)

            # ---------- REPETITION ----------
            st.markdown("### ⚠ Repeated Words")

            if result["repeated"]:
                rep_html = "".join([
                    f"<div style='margin-bottom:5px;'>🔁 <b>{w}</b> → {c} times</div>"
                    for w, c in result["repeated"].items()
                ])
            else:
                rep_html = "No repetition"

            st.markdown(f"""
            <div style="
                background:#f1f5f9;
                padding:10px;
                border-radius:12px;
                border:1px solid #64748b;">
                {rep_html}
            </div>
            """, unsafe_allow_html=True)

        # CHART (UNCHANGED SIZE SMALL)
        labels = ["Matched", "Missing", "JD"]
        values = [len(result["matched"]), len(result["missing"]), result["jd_score"]]

        fig, ax = plt.subplots(figsize=(8, 3))
        ax.bar(labels, values)
        st.pyplot(fig)

        # DOWNLOAD
        pdf_data = generate_pdf(file.name, result)

        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_data,
            file_name=f"{file.name}_ATS_Report.pdf",
            mime="application/pdf"
        )