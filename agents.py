from llm import ask, ask_json

ANALYSIS_AGENTS = {
    "Bug Detector": "logic errors, unhandled exceptions, off-by-one errors, null/None issues, race conditions, wrong edge-case handling",
    "Security Auditor": "SQL injection, XSS, command injection, hardcoded secrets, insecure deserialization, weak crypto, missing input validation, path traversal",
    "Code Smell Detector": "duplicated code, long functions, deep nesting, poor naming, dead code, magic numbers, missing docstrings, tight coupling",
    "Performance Analyzer": "inefficient loops, repeated computation, O(n^2) patterns, unnecessary I/O or DB calls, memory waste, missing caching",
}

JSON_RULES = """Return ONLY a JSON array, no other text. Each item:
{"severity": "High|Medium|Low", "line": <int>, "title": "<short>", "description": "<1-2 sentences>", "suggested_fix": "<short fix>"}
If nothing is found, return []."""


def number_lines(code: str) -> str:
    return "\n".join(f"{i}: {l}" for i, l in enumerate(code.splitlines(), 1))


def run_analysis_agent(agent_name: str, path: str, code: str) -> list:
    focus = ANALYSIS_AGENTS[agent_name]
    system = f"You are {agent_name}, an expert senior code reviewer. Focus ONLY on: {focus}. Be precise; do not invent issues."
    prompt = f"File: {path}\n\n{number_lines(code)}\n\n{JSON_RULES}"
    results = ask_json(prompt, system)
    category = agent_name.replace(" Detector", "").replace(" Auditor", "").replace(" Analyzer", "")
    for r in results:
        r["category"] = category
        r["source"] = "AI"
        r["file"] = path
    return results


def fix_agent(path: str, code: str, findings: list) -> str:
    issues = "\n".join(f"- line {f.get('line')}: {f.get('title')} - {f.get('description')}" for f in findings[:15])
    system = "You are an expert refactoring engineer. Fix the listed issues while preserving behaviour."
    prompt = (f"File: {path}\n\nOriginal code:\n{code}\n\nIssues:\n{issues}\n\n"
              "Return the COMPLETE corrected file inside one fenced code block, then a short bullet list of what changed.")
    return ask(prompt, system)


def test_agent(path: str, code: str) -> str:
    system = "You are a QA engineer who writes clean pytest test suites."
    prompt = (f"Write pytest test cases for this file ({path}). Include normal, edge and failure cases. "
              f"Return one fenced code block only.\n\n{code}")
    return ask(prompt, system)


def docs_agent(path: str, code: str) -> str:
    system = "You are a technical writer."
    prompt = (f"Write Markdown documentation for {path}: purpose, functions/classes with parameters and return values, "
              f"and a usage example.\n\n{code}")
    return ask(prompt, system)