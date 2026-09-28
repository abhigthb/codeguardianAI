import time
from agents import ANALYSIS_AGENTS, run_analysis_agent
from static_analysis import run_static
from config import DELAY_BETWEEN_CALLS

SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def analyze_repo(files: dict, selected_agents: list, progress=None) -> dict:
    """Returns {file_path: [findings]}."""
    results = {}
    total = len(files) * max(len(selected_agents), 1)
    done = 0
    for path, code in files.items():
        findings = []
        for f in run_static(path, code):
            f["file"] = path
            findings.append(f)
        for agent in selected_agents:
            if agent in ANALYSIS_AGENTS:
                try:
                    findings.extend(run_analysis_agent(agent, path, code))
                except Exception as e:
                    findings.append({"severity": "Low", "category": "System", "line": 0, "file": path,
                                     "title": f"{agent} failed", "description": str(e), "source": "system"})
                time.sleep(DELAY_BETWEEN_CALLS)
            done += 1
            if progress:
                progress(done / total, f"{agent} → {path}")
        findings.sort(key=lambda x: SEVERITY_ORDER.get(x.get("severity", "Low"), 3))
        results[path] = findings
    return results


def summarize(results: dict) -> dict:
    counts = {"High": 0, "Medium": 0, "Low": 0}
    cats = {}
    for fl in results.values():
        for f in fl:
            counts[f.get("severity", "Low")] = counts.get(f.get("severity", "Low"), 0) + 1
            cats[f["category"]] = cats.get(f["category"], 0) + 1
    total = sum(counts.values())
    score = max(0, 100 - (counts["High"] * 10 + counts["Medium"] * 4 + counts["Low"]))
    return {"counts": counts, "categories": cats, "total": total, "score": score}