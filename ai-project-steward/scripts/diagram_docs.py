#!/usr/bin/env python3
"""Manage an Archify diagram workspace inside a project repository."""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path

TYPES = ("architecture", "workflow", "sequence", "dataflow", "lifecycle")
CODE_EXTENSIONS = {".c", ".cc", ".cpp", ".cs", ".dart", ".go", ".java", ".js", ".jsx", ".kt", ".php", ".py", ".rb", ".rs", ".swift", ".ts", ".tsx", ".vue"}

def git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.returncode, p.stdout.strip()

def resolve_root(value):
    root = Path(value).expanduser().resolve(); code, out = git(root, "rev-parse", "--show-toplevel")
    return Path(out).resolve() if code == 0 and out else root

def write_missing(path, content):
    if path.exists() and path.stat().st_size: return False
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content.rstrip() + "\n", encoding="utf-8"); return True

def init(root):
    files = {
      root/"docs/ai/diagram-index.md": """# Diagram index

Archify JSON files are authoritative. HTML files are validated, generated deliverables.

| Diagram | Type | Question answered | Evidence | JSON source | HTML output | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 待分析 | 待分析 | 待分析 | 待分析 | 待分析 | 待分析 | pending |
""",
      root/"docs/ai/diagrams/README.md": """# Archify diagram workspace

This directory follows [Archify](https://github.com/tt-a1i/archify).

- `sources/`: authoritative typed JSON IR.
- `output/`: self-contained HTML produced by Archify `deliver`.
- `receipts/`: optional validation, delivery, and visual-check receipts.

Create sources from repository evidence, validate them, then deliver HTML atomically. Never edit generated HTML by hand.
""",
      root/"docs/ai/diagrams/archify.json": json.dumps({"schema_version":1,"engine":"tt-a1i/archify","quality_profile":"showcase","locale":"zh-CN","source_dir":"sources","output_dir":"output","receipt_dir":"receipts"}, ensure_ascii=False, indent=2),
      root/"docs/ai/diagrams/sources/.gitkeep": "", root/"docs/ai/diagrams/output/.gitkeep": "", root/"docs/ai/diagrams/receipts/.gitkeep": "",
    }
    created = [str(p.relative_to(root)) for p,c in files.items() if write_missing(p,c)]
    return {"root":str(root),"created":created,"preserved":len(files)-len(created)}

def sources(root):
    base=root/"docs/ai/diagrams/sources"; return sorted(base.glob("*.json")) if base.exists() else []

def source_type(path, data=None):
    bits=path.stem.rsplit(".",1)
    if len(bits)==2 and bits[1] in TYPES: return bits[1]
    value=(data or {}).get("diagram_type") or (data or {}).get("type"); return value if value in TYPES else None

def inventory(root):
    items=[]
    for path in sources(root):
        try: data=json.loads(path.read_text(encoding="utf-8")); error=None
        except (OSError,json.JSONDecodeError) as exc: data={}; error=str(exc)
        output=root/"docs/ai/diagrams/output"/f"{path.stem}.html"
        items.append({"path":str(path.relative_to(root)),"type":source_type(path,data),"title":data.get("meta",{}).get("title"),"html":str(output.relative_to(root)) if output.exists() else None,"error":error})
    return {"root":str(root),"engine":"tt-a1i/archify","sources":items}

def audit(root):
    issues=[]
    for rel in ("docs/ai/diagram-index.md","docs/ai/diagrams/README.md","docs/ai/diagrams/archify.json"):
        if not (root/rel).exists(): issues.append({"type":"missing-workspace-file","path":rel,"detail":"run init"})
    for path in sources(root):
        rel=str(path.relative_to(root))
        try: data=json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc: issues.append({"type":"invalid-json","path":rel,"detail":str(exc)}); continue
        if not source_type(path,data): issues.append({"type":"unknown-archify-type","path":rel,"detail":"use <name>.<type>.json"})
        if not isinstance(data.get("meta"),dict) or data["meta"].get("quality_profile")!="showcase": issues.append({"type":"missing-showcase-profile","path":rel,"detail":"set meta.quality_profile to showcase"})
    return {"root":str(root),"files_checked":len(sources(root)),"issues":issues}

def changed_files(root):
    paths=[]
    for args in (("diff","--name-only","--diff-filter=ACMRD"),("diff","--cached","--name-only","--diff-filter=ACMRD"),("ls-files","--others","--exclude-standard")):
        code,out=git(root,*args)
        if code==0: paths.extend(out.splitlines())
    return sorted(set(filter(None,paths)))

def impact(root):
    changed=changed_files(root); signals=("api","controller","route","service","module","schema","migration","entity","model","state","workflow","event","queue","config")
    candidates=[p for p in changed if not p.startswith("docs/") and (Path(p).suffix.lower() in CODE_EXTENSIONS or any(s in p.lower() for s in signals))]
    diagrams=[p for p in changed if p.startswith("docs/ai/diagrams/") or p=="docs/ai/diagram-index.md"]
    return {"root":str(root),"changed":changed,"diagram_impact_candidates":candidates,"diagrams_changed":diagrams,"needs_semantic_review":bool(candidates)}

def find_archify(value):
    candidates=[]
    if value: candidates.append(Path(value).expanduser())
    if os.environ.get("ARCHIFY_ROOT"): candidates.append(Path(os.environ["ARCHIFY_ROOT"]).expanduser())
    candidates += [Path.cwd()/"archify",Path.home()/".agents/skills/archify"]
    return next((p/"bin/archify.mjs" for p in candidates if (p/"bin/archify.mjs").is_file()),None)

def archify_run(root,args):
    cli=find_archify(args.archify)
    if not cli: return {"ok":False,"error":"Archify CLI not found; pass --archify or set ARCHIFY_ROOT"}
    source=Path(args.source).expanduser(); source=source if source.is_absolute() else root/source
    dtype=args.type or source_type(source)
    if dtype not in TYPES: return {"ok":False,"error":"type is required or must appear in <name>.<type>.json"}
    output=None; command=["node",str(cli),"validate",dtype,str(source),"--quality","showcase","--json"]
    if args.mode=="deliver":
        output=Path(args.output).expanduser() if args.output else root/"docs/ai/diagrams/output"/f"{source.stem}.html"
        output=output if output.is_absolute() else root/output; output.parent.mkdir(parents=True,exist_ok=True)
        command=["node",str(cli),"deliver",dtype,str(source),str(output),"--quality","showcase","--json"]
    p=subprocess.run(command,cwd=cli.parent.parent,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    return {"ok":p.returncode==0,"command":command,"exit_code":p.returncode,"output":str(output) if output else None,"stdout":p.stdout.strip(),"stderr":p.stderr.strip()}

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("mode",choices=("init","inventory","impact","audit","validate","deliver")); ap.add_argument("--root",default=os.getcwd()); ap.add_argument("--archify"); ap.add_argument("--type",choices=TYPES); ap.add_argument("--source"); ap.add_argument("--output"); args=ap.parse_args(); root=resolve_root(args.root)
    if args.mode in ("validate","deliver"):
        if not args.source: ap.error("--source is required")
        result=archify_run(root,args); code=0 if result.get("ok") else 1
    else:
        result={"init":init,"inventory":inventory,"impact":impact,"audit":audit}[args.mode](root); code=1 if args.mode=="audit" and result["issues"] else 0
    print(json.dumps(result,ensure_ascii=False,indent=2)); return code

if __name__=="__main__": sys.exit(main())
