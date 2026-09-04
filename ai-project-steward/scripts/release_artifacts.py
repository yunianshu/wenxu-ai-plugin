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
    return {"root":str(root),"version":version_info,"plans":plans,"fallback":"no build plan detected; run scaffold to create the missing deployment scripts, then bundle the reviewed source tree as a versioned tar.gz" if not plans else None}

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

REQUIRED_SCRIPTS = ("package.sh", "backup.sh", "restore.sh", "start.sh", "stop.sh", "upgrade.sh")

SCRIPT_HEADER = (
    "#!/usr/bin/env bash\n"
    "# Generated by ai-project-steward scaffold -- review every TODO(project) marker before deployment.\n"
    "set -Eeuo pipefail\n"
    'SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"\n'
    "log() { printf '[__NAME__] %s\\n' \"$*\" >&2; }\n"
    'die() { log "ERROR: $*"; exit 1; }\n'
)

START_TEMPLATE = """# TODO(project): replace this template with the real service manager (systemd unit, docker compose, pm2, ...) and validate configuration and prerequisites first.
# __START_NOTE__
PID_FILE="${PID_FILE:-$SCRIPT_DIR/app.pid}"
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then log "already running (pid $(cat "$PID_FILE"))"; exit 0; fi

__START_CMD__ >/dev/null 2>&1 &
echo $! > "$PID_FILE"

# TODO(project): verify readiness against the real health endpoint with a bounded timeout.
HEALTH_URL="${HEALTH_URL:-}"
if [ -n "$HEALTH_URL" ]; then
  for _ in $(seq 1 30); do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then log "healthy at $HEALTH_URL"; exit 0; fi
    sleep 2
  done
  die "service did not become healthy at $HEALTH_URL within 60s"
fi
log "started (pid $(cat "$PID_FILE"))"
"""

STOP_TEMPLATE = """# TODO(project): stop through the real service manager; escalate (SIGKILL) only when configured.
PID_FILE="${PID_FILE:-$SCRIPT_DIR/app.pid}"
if [ ! -f "$PID_FILE" ]; then log "not running"; exit 0; fi
pid="$(cat "$PID_FILE")"
if kill -0 "$pid" 2>/dev/null; then
  kill "$pid"
  for _ in $(seq 1 30); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
  kill -0 "$pid" 2>/dev/null && die "process $pid did not exit within 30s"
  log "stopped (pid $pid)"
fi
rm -f -- "$PID_FILE"
"""

DOCKER_START = """# TODO(project): confirm the compose file, service names, and pinned image digests before deployment.
COMPOSE_FILE="${COMPOSE_FILE:-$SCRIPT_DIR/docker-compose.yml}"
[ -f "$COMPOSE_FILE" ] || die "compose file not found: $COMPOSE_FILE (set COMPOSE_FILE)"
docker compose -f "$COMPOSE_FILE" up -d
# TODO(project): verify service health (HTTP endpoint), not only container state.
docker compose -f "$COMPOSE_FILE" ps
"""

DOCKER_STOP = """# TODO(project): confirm the shutdown model -- named data volumes must survive 'down'.
COMPOSE_FILE="${COMPOSE_FILE:-$SCRIPT_DIR/docker-compose.yml}"
[ -f "$COMPOSE_FILE" ] || die "compose file not found: $COMPOSE_FILE (set COMPOSE_FILE)"
docker compose -f "$COMPOSE_FILE" down
"""

PACKAGE_TEMPLATE = """# Contract: build verified artifacts, stage one clean version directory, write VERSION and checksums,
# reject secrets and mutable data, then create a tar.gz with exactly one top-level directory.
PROJECT_NAME="${PROJECT_NAME:?set the project name}"
PROJECT_VERSION="$(tr -d '[:space:]' < "$SCRIPT_DIR/VERSION")"
[ -n "$PROJECT_VERSION" ] || die "VERSION is empty"

# TODO(project): run the repository's verified release build command here, e.g.: __BUILD_HINT__
# TODO(project): copy runtime artifacts, migrations, example configuration, and the six deployment scripts into the staging directory; never secrets, databases, logs, or caches.

STAMP="$(date -u +%Y%m%d%H%M%S)"
STAGING="${RELEASE_DIR:-$SCRIPT_DIR/release}/${PROJECT_NAME}-v${PROJECT_VERSION}-${STAMP}"
[ ! -e "$STAGING" ] || die "staging directory already exists: $STAGING"
mkdir -p -- "$STAGING"
for script in VERSION package.sh backup.sh restore.sh start.sh stop.sh upgrade.sh; do
  cp -- "$SCRIPT_DIR/$script" "$STAGING/$script"
done
# TODO(project): cp the built runtime artifacts into "$STAGING" before archiving.

( cd -- "$(dirname -- "$STAGING")" && find "$(basename -- "$STAGING")" -type f ! -name checksums.txt -exec sha256sum -- {} + > "$STAGING/checksums.txt" )
( cd -- "$(dirname -- "$STAGING")" && tar -czf "$(basename -- "$STAGING").tar.gz" "$(basename -- "$STAGING")" )
log "packaged $STAGING.tar.gz"
"""

BACKUP_TEMPLATE = """# Contract: quiesce or consistently snapshot databases/uploads/configuration, check free space,
# write a timestamp and manifest, and produce a checksummed backup that never contains itself.
BACKUP_ROOT="${BACKUP_ROOT:-$SCRIPT_DIR/backups}"
# TODO(project): set the real data locations (database, uploads, configuration) -- never invent paths.
# TODO(project): quiesce the service or take a consistent snapshot before copying.
STAMP="$(date -u +%Y%m%d%H%M%S)"
DEST="$BACKUP_ROOT/backup-$STAMP"
[ ! -e "$DEST" ] || die "backup directory already exists: $DEST"
mkdir -p -- "$DEST"
# TODO(project): capture the real data, e.g.
#   pg_dump "$DATABASE_URL" | gzip > "$DEST/database.sql.gz"
#   tar -czf "$DEST/uploads.tar.gz" -C /srv/app uploads
printf '{"generated_at":"%s","tool":"backup.sh","version":"%s"}\\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || printf unknown)" > "$DEST/manifest.json"
# TODO(project): check free space before writing the backup.
( cd -- "$BACKUP_ROOT" && find "backup-$STAMP" -type f ! -name checksums.txt -exec sha256sum -- {} + > "backup-$STAMP/checksums.txt" )
tar -czf "$DEST.tar.gz" -C "$BACKUP_ROOT" "backup-$STAMP"
log "backup written: $DEST.tar.gz"
"""

RESTORE_TEMPLATE = """# Contract: validate checksums/version/target, protect current state with a pre-restore backup,
# restore atomically where possible, fix ownership, and verify service health.
[ "$#" -eq 1 ] || die "usage: restore.sh <backup.tar.gz>"
ARCHIVE="$1"
[ -f "$ARCHIVE" ] || die "backup archive not found: $ARCHIVE"
# TODO(project): verify checksums.txt inside the archive and version compatibility before touching data.
# TODO(project): refuse ambiguous targets and require explicit confirmation for destructive replacement unless invoked by the upgrade.sh rollback path.
# TODO(project): write a pre-restore backup with backup.sh before replacing anything.
# TODO(project): stop/quiesce the service, restore data atomically, fix ownership, restart, and verify health.
die "restore.sh is a template: implement the steps above against the real data locations before use"
"""

UPGRADE_TEMPLATE = """# Contract: this script runs from the extracted new-version directory. Discover the installed
# directory from explicit configuration or a stable 'current' symlink, lock against concurrent
# upgrades, validate the package, back up, stop the old service, preserve mutable data/config,
# switch immutable resources atomically, migrate, start, health-check, and roll back on failure.
LOCK_FILE="${LOCK_FILE:-$SCRIPT_DIR/.upgrade.lock}"
# TODO(project): resolve INSTALL_ROOT from explicit configuration or the stable 'current' symlink; never guess it.
INSTALL_ROOT="${INSTALL_ROOT:?set the install root explicitly or resolve it from the current symlink}"
NEW_VERSION="$(tr -d '[:space:]' < "$SCRIPT_DIR/VERSION")"
[ -n "$NEW_VERSION" ] || die "VERSION is empty"
[ -d "$INSTALL_ROOT/releases" ] || die "install root has no releases directory: $INSTALL_ROOT"
if [ -e "$LOCK_FILE" ] && kill -0 "$(cat "$LOCK_FILE" 2>/dev/null)" 2>/dev/null; then die "another upgrade appears active (lock: $LOCK_FILE)"; fi
printf '%s\\n' "$$" > "$LOCK_FILE"
trap 'rm -f -- "$LOCK_FILE"' EXIT
# TODO(project): previous="$(basename "$(readlink -f "$INSTALL_ROOT/current")")"; validate this package's manifest/checksums;
# "$SCRIPT_DIR/backup.sh"; stop the old service; preserve shared config/data; switch the 'current' symlink atomically (ln -sfn);
# run compatible migrations; start and health-check; on failure restore the previous symlink and restart it.
die "upgrade.sh is a template: implement the steps above against the real install layout before use"
"""

PROFILE_FRAGMENTS = {
    "docker": {"build_hint": "docker build -t <confirmed-image-name>:<version> ."},
    "node": {"start_cmd": 'nohup npm --prefix "$SCRIPT_DIR" run start', "start_note": "TODO(project): confirm package.json defines a start script.", "build_hint": "npm ci && npm run build"},
    "jvm": {"start_cmd": 'nohup java -jar "$SCRIPT_DIR/app.jar"', "start_note": "TODO(project): point at the real runnable JAR.", "build_hint": "mvn -DskipTests package or ./gradlew bootJar"},
    "binary": {"start_cmd": 'nohup "$SCRIPT_DIR/app"', "start_note": "TODO(project): point at the real built executable.", "build_hint": "go build -o app ./... or cargo build --release"},
    "generic": {"start_cmd": 'nohup "$SCRIPT_DIR/run"', "start_note": "TODO(project): no service stack was detected; replace this with the real start command.", "build_hint": "the repository's verified build command"},
}

def deployment_profile(root: Path) -> tuple[str, list[str]]:
    notes = []
    if (root / "docker-compose.yml").exists() or (root / "compose.yaml").exists() or (root / "Dockerfile").exists(): return "docker", notes
    if (root / "package.json").exists(): return "node", notes
    if (root / "pom.xml").exists(): return "jvm", notes
    if (root / "pubspec.yaml").exists(): notes.append("flutter/mobile project: service lifecycle scripts may not apply; adapt or consciously drop them"); return "generic", notes
    if (root / "settings.gradle").exists() or (root / "settings.gradle.kts").exists():
        if (root / "app" / "build.gradle").exists() or (root / "app" / "build.gradle.kts").exists(): notes.append("android project: service lifecycle scripts may not apply; adapt or consciously drop them"); return "generic", notes
        return "jvm", notes
    if (root / "go.mod").exists() or (root / "Cargo.toml").exists(): return "binary", notes
    return "generic", notes

def render_script(name: str, profile: str) -> str:
    header = SCRIPT_HEADER.replace("__NAME__", name[:-3])
    fragment = PROFILE_FRAGMENTS.get(profile, PROFILE_FRAGMENTS["generic"])
    if profile == "docker" and name in ("start.sh", "stop.sh"): body = DOCKER_START if name == "start.sh" else DOCKER_STOP
    elif name == "start.sh": body = START_TEMPLATE.replace("__START_NOTE__", fragment["start_note"]).replace("__START_CMD__", fragment["start_cmd"])
    elif name == "stop.sh": body = STOP_TEMPLATE
    elif name == "package.sh": body = PACKAGE_TEMPLATE.replace("__BUILD_HINT__", fragment["build_hint"])
    elif name == "backup.sh": body = BACKUP_TEMPLATE
    elif name == "restore.sh": body = RESTORE_TEMPLATE
    else: body = UPGRADE_TEMPLATE
    return header + "\n" + body

def write_lf(path: Path, text: str):
    with path.open("w", encoding="utf-8", newline="\n") as handle: handle.write(text)

def ensure_scripts(root: Path, profile: str) -> list[str]:
    created = []
    for name in REQUIRED_SCRIPTS:
        path = root / name
        if path.exists(): continue
        write_lf(path, render_script(name, profile))
        created.append(name)
    return created

def scaffold(root: Path, requested_version: str | None) -> dict:
    profile, notes = deployment_profile(root)
    created = ensure_scripts(root, profile)
    existing = [name for name in REQUIRED_SCRIPTS if name not in created]
    version_info = detect_versions(root)
    if version_info["conflict"]: raise ValueError("conflicting project versions: " + ", ".join(f'{i["source"]}={i["version"]}' for i in version_info["candidates"]))
    version_out = {"resolved": version_info["resolved"]}
    if not version_info["resolved"]:
        if requested_version:
            version = requested_version.lstrip("v").strip()
            if not re.fullmatch(r"[A-Za-z0-9._+-]+", version): raise ValueError(f"invalid version: {requested_version!r}")
            write_lf(root / "VERSION", version + "\n")
            version_out = {"resolved": version, "created": str(root / "VERSION")}
        else:
            version_out = {"resolved": None, "note": "no authoritative version source; confirm an initial version with the user, then run scaffold --version <confirmed> or declare it in the primary manifest"}
    elif requested_version and requested_version.lstrip("v") != version_info["resolved"]:
        raise ValueError(f"requested version {requested_version} does not match project version {version_info['resolved']}")
    todo_count = sum((root / name).read_text(encoding="utf-8").count("TODO(project)") for name in REQUIRED_SCRIPTS)
    return {"root": str(root), "profile": profile, "notes": notes, "created": created, "existing": existing, "version": version_out, "todo_markers": todo_count, "warning": "scaffold writes templates only; adapt process manager, database, health check, ownership, and paths to the project before any release"}

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
    created_scripts = []
    if not {path.name for path in selected} >= set(REQUIRED_SCRIPTS):
        profile, _ = deployment_profile(root)
        created_scripts = ensure_scripts(root, profile)
        if created_scripts:
            selected = list(iter_matches(root, includes))
            for script in sorted(set(REQUIRED_SCRIPTS) - {path.name for path in selected}): selected.append((root / script).resolve())
    if not selected:
        raise ValueError("no files matched --include patterns; run the verified release build first (see detect), collect its outputs, or include the scaffolded scripts")
    missing = sorted(set(REQUIRED_SCRIPTS) - {path.name for path in selected})
    if missing: raise ValueError("package is missing required scripts: " + ", ".join(missing))
    for source in selected:
        relative = source.relative_to(root)
        target = staging / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    write_lf(staging / "VERSION", version + "\n")
    manifest_items = [{"file":str(path.relative_to(staging)),"size":path.stat().st_size,"sha256":sha256(path)} for path in sorted(staging.rglob("*")) if path.is_file()]
    (staging / "manifest.json").write_text(json.dumps({"name":name,"version":version,"artifacts":manifest_items},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    archive = destination / f"{package_name}.tar.gz"
    with tarfile.open(archive, "w:gz") as handle: handle.add(staging, arcname=package_name)
    result = {"root":str(root),"version":version,"package_directory":str(staging),"archive":str(archive),"top_level_directory":package_name,"files":len(manifest_items)+1,"size":archive.stat().st_size,"sha256":sha256(archive)}
    if created_scripts:
        result["created_scripts"] = created_scripts
        result["warning"] = "deployment scripts were scaffolded during bundling; resolve their TODO(project) markers against the real project before release"
    return result

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("mode",choices=("detect","version","collect","bundle","audit","scaffold")); ap.add_argument("--root",default=os.getcwd()); ap.add_argument("--artifact",action="append",default=[]); ap.add_argument("--include",action="append",default=[]); ap.add_argument("--name"); ap.add_argument("--version",help="Optional assertion; must match the detected project version. For scaffold on a project without any version source, a user-confirmed initial version recorded as VERSION"); ap.add_argument("--output-dir",default="release"); args=ap.parse_args(); root=git_root(args.root)
    if args.mode=="detect": result=detect(root); code=1 if result["version"]["conflict"] else 0
    elif args.mode=="version":
        try: result={"root":str(root),"version":resolve_version(root,args.version),"evidence":detect_versions(root)["candidates"]}; code=0
        except ValueError as exc: result={"root":str(root),"error":str(exc),"evidence":detect_versions(root)["candidates"]}; code=1
    elif args.mode=="scaffold":
        try: result=scaffold(root,args.version); code=0
        except ValueError as exc: result={"root":str(root),"error":str(exc)}; code=1
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
