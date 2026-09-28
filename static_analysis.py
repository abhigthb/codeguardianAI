import ast, re

SECRET_PATTERN = re.compile(
    r"(password|passwd|secret|api[_-]?key|token)\s*=\s*['\"][^'\"]{4,}['\"]", re.I
)
DANGEROUS_CALLS = {"eval", "exec", "pickle.loads", "os.system", "subprocess.call"}


def analyze_python(code: str) -> list:
    findings = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [{"severity": "High", "category": "Bug", "line": e.lineno or 0,
                 "title": "Syntax error", "description": str(e), "source": "static"}]

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            length = (node.end_lineno or node.lineno) - node.lineno
            if length > 50:
                findings.append({"severity": "Medium", "category": "Code Smell", "line": node.lineno,
                                 "title": f"Long function '{node.name}'",
                                 "description": f"{length} lines. Consider splitting it.", "source": "static"})
            if len(node.args.args) > 5:
                findings.append({"severity": "Low", "category": "Code Smell", "line": node.lineno,
                                 "title": f"Too many parameters in '{node.name}'",
                                 "description": f"{len(node.args.args)} parameters.", "source": "static"})
            for d in node.args.defaults:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                    findings.append({"severity": "Medium", "category": "Bug", "line": node.lineno,
                                     "title": "Mutable default argument",
                                     "description": "Default list/dict is shared between calls.", "source": "static"})
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            findings.append({"severity": "Medium", "category": "Bug", "line": node.lineno,
                             "title": "Bare except", "description": "Catches everything, hides errors.",
                             "source": "static"})
        if isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            if name in DANGEROUS_CALLS:
                findings.append({"severity": "High", "category": "Security", "line": node.lineno,
                                 "title": f"Dangerous call: {name}()",
                                 "description": "Can allow code execution or injection.", "source": "static"})

    for i, line in enumerate(code.splitlines(), 1):
        if SECRET_PATTERN.search(line):
            findings.append({"severity": "High", "category": "Security", "line": i,
                             "title": "Hardcoded secret",
                             "description": "Move credentials to environment variables.", "source": "static"})
    return findings


def run_static(path: str, code: str) -> list:
    return analyze_python(code) if path.endswith(".py") else []