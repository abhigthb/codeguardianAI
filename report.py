from datetime import datetime
from orchestrator import summarize


def build_markdown_report(repo_name: str, results: dict) -> str:
    s = summarize(results)
    lines = [f"# CodeGuardian AI Report: {repo_name}",
             f"_Generated: {datetime.now():%Y-%m-%d %H:%M}_", "",
             f"**Health score:** {s['score']}/100", "",
             f"- High: {s['counts']['High']}  - Medium: {s['counts']['Medium']}  - Low: {s['counts']['Low']}", ""]
    for path, findings in results.items():
        lines.append(f"## {path}")
        if not findings:
            lines.append("No issues found.\n")
            continue
        for f in findings:
            lines.append(f"- **[{f['severity']}] {f['category']}**: {f['title']} (line {f.get('line', '?')})")
            lines.append(f"  - {f['description']}")
            if f.get("suggested_fix"):
                lines.append(f"  - Fix: {f['suggested_fix']}")
        lines.append("")
    return "\n".join(lines)