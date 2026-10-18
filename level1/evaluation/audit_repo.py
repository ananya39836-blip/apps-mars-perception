"""Repository Static Analysis Scanner for Task 41.
Part 6 Appendix AP.
"""
import ast
import os
import re

PATTERNS = {
    "hgb": r"HistGradientBoostingClassifier",
    "astar": r"heapq|a\*|astar|dijkstra",
    "pickle_load": r"pickle\.load|joblib\.load",
    "abs_path": r"[\"'](/home/|/Users/|[A-Z]:\\\\)",
    "secret": r"(api[_-]?key|secret|token)\s*=\s*[\"'][A-Za-z0-9_\-]{12,}",
    "eval_exec": r"\b(eval|exec)\("
}


def audit_repo(root: str) -> dict:
    """Static scan only: scans and reports codebase architecture, imports, and safety patterns."""
    rep = dict(
        py_files=[], tests=[], hits={k: [] for k in PATTERNS}, syntax_errors=[],
        big_files=[], has_requirements=False, has_readme=False, imports=set()
    )
    for d, _, fs in os.walk(root):
        if ".git" in d.split(os.sep) or "__pycache__" in d.split(os.sep):
            continue
        for f in fs:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, root)
            if f in ("requirements.txt", "pyproject.toml"):
                rep["has_requirements"] = True
            if f.lower().startswith("readme"):
                rep["has_readme"] = True
            if not f.endswith(".py"):
                continue
            rep["py_files"].append(rel)
            if f.startswith("test_") or "tests" in d.split(os.sep):
                rep["tests"].append(rel)
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            if txt.count("\n") > 400:
                rep["big_files"].append((rel, txt.count("\n")))
            try:
                for nd in ast.walk(ast.parse(txt)):
                    if isinstance(nd, ast.Import):
                        rep["imports"].update(a.name.split(".")[0] for a in nd.names)
                    if isinstance(nd, ast.ImportFrom) and nd.module:
                        rep["imports"].add(nd.module.split(".")[0])
            except SyntaxError as e:
                rep["syntax_errors"].append((rel, e.lineno))
            for k, rx in PATTERNS.items():
                if re.search(rx, txt, re.I):
                    rep["hits"][k].append(rel)
    rep["imports"] = sorted(rep["imports"])
    return rep
