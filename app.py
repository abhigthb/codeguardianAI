import streamlit as st
from repo_loader import load_from_github, load_from_uploads
from orchestrator import analyze_repo, summarize
from agents import ANALYSIS_AGENTS, fix_agent, test_agent, docs_agent
from report import build_markdown_report

st.set_page_config(page_title="CodeGuardian AI", page_icon="🛡️", layout="wide")
st.title("🛡️ CodeGuardian AI")
st.caption("Autonomous GenAI code review: bugs, security, smells, performance, fixes, tests and docs.")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Input")
    mode = st.radio("Source", ["GitHub URL", "Upload files"])
    url, uploads = "", None
    if mode == "GitHub URL":
        url = st.text_input("Public repo URL", placeholder="https://github.com/user/repo")
    else:
        uploads = st.file_uploader("Upload code files or a .zip", accept_multiple_files=True)
    agents_sel = st.multiselect("Analysis agents", list(ANALYSIS_AGENTS), default=list(ANALYSIS_AGENTS))
    go = st.button("🔍 Analyze", type="primary", use_container_width=True)

# ---------- Run analysis ----------
if go:
    try:
        with st.spinner("Loading code..."):
            files = load_from_github(url) if mode == "GitHub URL" else load_from_uploads(uploads or [])
        if not files:
            st.error("No supported code files found.")
        else:
            bar = st.progress(0.0, text="Starting agents...")
            results = analyze_repo(files, agents_sel, progress=lambda p, t: bar.progress(p, text=t))
            bar.empty()
            st.session_state.update(files=files, results=results, repo=url or "uploaded-project")
    except Exception as e:
        st.error(f"Error: {e}")

# ---------- Show results ----------
if "results" in st.session_state:
    files, results = st.session_state["files"], st.session_state["results"]
    s = summarize(results)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Health score", f"{s['score']}/100")
    c2.metric("High", s["counts"]["High"])
    c3.metric("Medium", s["counts"]["Medium"])
    c4.metric("Low", s["counts"]["Low"])
    if s["categories"]:
        st.bar_chart(s["categories"])

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Findings", "🔧 Fix & Refactor", "🧪 Tests", "📄 Docs"])

    with tab1:
        for path, findings in results.items():
            with st.expander(f"{path}  ({len(findings)} issues)"):
                for f in findings:
                    icon = {"High": "🔴", "Medium": "🟠", "Low": "🟡"}.get(f["severity"], "⚪")
                    st.markdown(f"{icon} **{f['title']}** · {f['category']} · line {f.get('line', '?')} · _{f['source']}_")
                    st.write(f["description"])
                    if f.get("suggested_fix"):
                        st.info(f"Fix: {f['suggested_fix']}")
        st.download_button("⬇️ Download report (.md)",
                           build_markdown_report(st.session_state["repo"], results),
                           file_name="codeguardian_report.md")

    chosen = None
    for tab, label in ((tab2, "fix"), (tab3, "test"), (tab4, "doc")):
        with tab:
            path = st.selectbox("Choose file", list(files), key=f"sel_{label}")
            if st.button(f"Generate {label}", key=f"btn_{label}"):
                with st.spinner("Agent working..."):
                    if label == "fix":
                        out = fix_agent(path, files[path], results.get(path, []))
                    elif label == "test":
                        out = test_agent(path, files[path])
                    else:
                        out = docs_agent(path, files[path])
                st.markdown(out)