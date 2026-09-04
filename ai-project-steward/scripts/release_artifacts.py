#!/usr/bin/env python3
"""Detect, collect, and audit project release artifacts."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

IGNORED = {".git", ".gradle", ".idea", ".dart_tool", ".venv", "node_modules", "coverage"}

def git_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    p = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return Path(p.stdout.strip()).resolve() if p.returncode == 0 else root

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""): digest.update(block)
    return digest.hexdigest()

def detect(root: Path) -> dict:
    plans = []
    gradlew = "gradlew.bat" if os.name == "nt" else "./gradlew"
    if (root / "pubspec.yaml").exists():
        plans += [{"kind":"flutter-apk","command":["flutter","build","apk","--release"],"outputs":["build/app/outputs/flutter-apk/*.apk"]}, {"kind":"flutter-aab","command":["flutter","build","appbundle","--release"],"outputs":["build/app/outputs/bundle/release/*.aab"]}]
    elif (root / "settings.gradle").exists() or (root / "settings.gradle.kts").exists():
        plans.append({"kind":"gradle","command":[gradlew,"assembleRelease"],"outputs":["**/build/outputs/**/*.apk","**/build/outputs/**/*.aab","**/build/libs/*.jar"]})
    if (root / "pom.xml").exists(): plans.append({"kind":"maven","command":["mvn","package"],"outputs":["target/*.jar","target/*.war"]})
    if (root / "package.json").exists(): plans.append({"kind":"node","command":["npm","run","build"],"outputs":["dist/**","build/**"]})
    if (root / "Cargo.toml").exists(): plans.append({"kind":"rust","command":["cargo","build","--release"],"outputs":["target/release/*"]})
    if (root / "go.mod").exists(): plans.append({"kind":"go","command":["go","build","-o","release/app","./..."],"outputs":["release/app","release/app.exe"]})
    if (root / "Dockerfile").exists(): plans.append({"kind":"docker","command":["docker","build","-t","<confirmed-image-name>:<version>","."],"outputs":["container-image"]})
    version_info = detect_versions(root)
    return {"root":str(root),"version":version_info,"plans":plans,"fallback":"generate a versioned single-root tar.gz source bundle with package.sh" if not plans else None}

def detect_versions(root: Path) -> dict:
    candidates = []
    def add(source: str, value: str | None):
        if value and value.strip(): candidates.append({"source":source,"version":value.strip().lstrip("v")})
    version_file = root / "VERSION"
    if version_file.is_file(): add("VERSION", version_file.read_text(encoding="utf-8",errors="replace").splitlines()[0])
    package_json = root / "package.json"
    if package_json.is_file():
        try: add("package.json", json.loads(package_json.read_text(encoding="utf-8")).get("version"))
        except json.JSONDecodeError: pass
    pubspec = root / "pubspec.yaml"
    if pubspec.is_file():
        match=re.search(r"(?m)^version:\s*['\"]?([^\s'\"]+)",pubspec.read_text(encoding="utf-8",errors="replace")); add("pubspec.yaml",match.group(1) if match else None)
    cargo = root / "Cargo.toml"
    if cargo.is_file():
        text=cargo.read_text(encoding="utf-8",errors="replace"); package=text.split("[package]",1)[1] if "[package]" in text else ""; match=re.search(r'(?m)^version\s*=\s*["\']([^"\']+)',package); add("Cargo.toml",match.group(1) if match else None)
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        text=pyproject.read_text(encoding="utf-8",errors="replace"); project=text.split("[project]",1)[1] if "[project]" in text else ""; match=re.search(r'(?m)^version\s*=\s*["\']([^"\']+)',project); add("pyproject.toml",match.group(1) if match else None)
    pom = root / "pom.xml"
    if pom.is_file():
        try:
            tree=ET.parse(pom); node=tree.getroot(); namespace=node.tag.partition("}")[0]+"}" if "}" in node.tag else ""; child=node.find(namespace+"version"); add("pom.xml",child.text if child is not None else None)
        except ET.ParseError: pass
    for filename in ("gradle.properties","build.gradle","build.gradle.kts","app/build.gradle","app/build.gradle.kts"):
        path=root/filename
        if not path.is_file(): continue
        text=path.read_text(encoding="utf-8",errors="replace")
        match=re.search(r'(?m)^\s*versionName\s*(?:=\s*)?["\']([^"\']+)',text) or re.search(r'(?m)^\s*(?:project\.)?version\s*=\s*["\']?([^\s"\']+)',text)
        add(filename,match.group(1) if match else None)
    unique=sorted({item["version"] for item in candidates})
    return {"resolved":unique[0] if len(unique)==1 else None,"candidates":candidates,"conflict":len(unique)>1}

def resolve_version(root: Path, requested: str | None) -> str:
    info=detect_versions(root)
    if info["conflict"]: raise ValueError("conflicting project versions: "+", ".join(f'{i["source"]}={i["version"]}' for i in info["candidates"]))
    detected=info["resolved"]
    if not detected: raise ValueError("project version not found; add an authoritative VERSION or supported manifest version")
    if requested and requested.lstrip("v") != detected: raise ValueError(f"requested version {requested} does not match project version {detected}")
    return detected

def iter_matches(root: Path, patterns: list[str]):
    seen = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if not path.is_file() or any(part in IGNORED for part in path.parts): continue
            resolved = path.resolve()
            if resolved not in seen: seen.add(resolved); yield resolved

def collect(root: Path, patterns: list[str], output_dir: str) -> dict:
    destination = (root / output_dir).resolve(); destination.mkdir(parents=True, exist_ok=True)
    copied = []
    for source in iter_matches(root, patterns):
        if destination in source.parents: target = source
        else:
            target = destination / source.name
            if target.exists() and target.resolve() != source: target = destination / f"{source.parent.name}-{source.name}"
            shutil.copy2(source, target)
        copied.append({"file":str(target.relative_to(root)),"source":str(source.relative_to(root)),"size":target.stat().st_size,"sha256":sha256(target)})
    manifest = {"generated_at":datetime.now(timezone.utc).isoformat(),"artifacts":copied}
    manifest_path = destination / "manifest.json"; manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"root":str(root),"output_dir":str(destination),"manifest":str(manifest_path),"artifacts":copied}

def audit(root: Path, output_dir: str) -> dict:
    directory=(root/output_dir).resolve(); manifest=directory/"manifest.json"; issues=[]
    if not manifest.exists(): return {"root":str(root),"issues":[{"type":"missing-manifest","path":str(manifest)}]}
    try: data=json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: return {"root":str(root),"issues":[{"type":"invalid-manifest","detail":str(exc)}]}
    for item in data.get("artifacts",[]):
        path=root/item["file"]
        if not path.exists(): issues.append({"type":"missing-artifact","path":item["file"]})
        elif sha256(path)!=item.get("sha256"): issues.append({"type":"checksum-mismatch","path":item["file"]})
    if not data.get("artifacts"): issues.append({"type":"empty-release","path":str(directory)})
    return {"root":str(root),"issues":issues,"artifacts":len(data.get("artifacts",[]))}

def safe_name(value: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._+-"
    cleaned = "".join(char if char in allowed else "-" for char in value).strip(".-")
    if not cleaned or cleaned in {".", ".."}: raise ValueError("invalid package name or version")
    return cleaned

def bundle(root: Path, name: str, version: str | None, includes: list[str], output_dir: str) -> dict:
    version = resolve_version(root, version)
    package_name = f"{safe_name(name)}-v{safe_name(version)}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    destination = (root / output_dir).resolve(); staging = destination / package_name
    if staging.exists(): raise ValueError(f"staging directory already exists: {staging}")
    staging.mkdir(parents=True)
    selected = list(iter_matches(root, includes))
    if not selected: raise ValueError("no files matched --include patterns")
    required_scripts = {"package.sh", "backup.sh", "restore.sh", "start.sh", "stop.sh", "upgrade.sh"}
    found_scripts = {path.name for path in selected}
    missing = sorted(required_scripts - found_scripts)
    if missing: raise ValueError("package is missing required scripts: " + ", ".join(missing))
    for source in selected:
        relative = source.relative_to(root)
        target = staging / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    (staging / "VERSION").write_text(version + "\n", encoding="utf-8")
    manifest_items = [{"file":str(path.relative_to(staging)),"size":path.stat().st_size,"sha256":sha256(path)} for path in sorted(staging.rglob("*")) if path.is_file()]
    (staging / "manifest.json").write_text(json.dumps({"name":name,"version":version,"artifacts":manifest_items},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    archive = destination / f"{package_name}.tar.gz"
    with tarfile.open(archive, "w:gz") as handle: handle.add(staging, arcname=package_name)
    return {"root":str(root),"version":version,"package_directory":str(staging),"archive":str(archive),"top_level_directory":package_name,"files":len(manifest_items)+1,"size":archive.stat().st_size,"sha256":sha256(archive)}

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("mode",choices=("detect","version","collect","bundle","audit")); ap.add_argument("--root",default=os.getcwd()); ap.add_argument("--artifact",action="append",default=[]); ap.add_argument("--include",action="append",default=[]); ap.add_argument("--name"); ap.add_argument("--version",help="Optional assertion; must match the detected project version"); ap.add_argument("--output-dir",default="release"); args=ap.parse_args(); root=git_root(args.root)
    if args.mode=="detect": result=detect(root); code=1 if result["version"]["conflict"] else 0
    elif args.mode=="version":
        try: result={"root":str(root),"version":resolve_version(root,args.version),"evidence":detect_versions(root)["candidates"]}; code=0
        except ValueError as exc: result={"root":str(root),"error":str(exc),"evidence":detect_versions(root)["candidates"]}; code=1
    elif args.mode=="collect":
        if not args.artifact: ap.error("collect requires one or more --artifact glob patterns")
        result=collect(root,args.artifact,args.output_dir); code=0 if result["artifacts"] else 1
    elif args.mode=="bundle":
        if not args.name or not args.include: ap.error("bundle requires --name and one or more --include patterns")
        try: result=bundle(root,args.name,args.version,args.include,args.output_dir); code=0
        except ValueError as exc: result={"root":str(root),"error":str(exc)}; code=1
    else: result=audit(root,args.output_dir); code=1 if result["issues"] else 0
    print(json.dumps(result,ensure_ascii=False,indent=2)); return code

if __name__=="__main__": sys.exit(main())
