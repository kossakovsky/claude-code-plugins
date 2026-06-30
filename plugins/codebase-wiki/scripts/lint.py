#!/usr/bin/env python3
"""
lint.py — wiki health-check rules for the Entity→Concept architecture.

Usage:
  python scripts/lint.py [--wiki wiki/]

Exit code: 0 if no errors, 1 if any [ERROR] found.

Output format per finding:
  [LEVEL] rule_name  detail
"""
import argparse
import re
import sys
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
PROVENANCE_RE = re.compile(r"\^\[.+?\]")


def _read_wiki_pages(wiki_root: Path):
    """Yield all .md files under wiki_root."""
    return list(wiki_root.rglob("*.md"))


def _strip_frontmatter(text: str) -> tuple:
    """Return (body, frontmatter_dict). frontmatter_dict may be empty."""
    if not text.startswith("---"):
        return text, {}
    end = text.find("\n---", 3)
    if end == -1:
        return text, {}
    fm_text = text[3:end]
    body = text[end + 4:]
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return body, fm


def check_broken_wikilinks(wiki_root: Path) -> list:
    """[ERROR] Any [[page]] whose file doesn't exist.

    Wikilink resolution (new architecture):
    - [[repos/<name>/entities/<slug>]] → wiki/repos/<name>/entities/<slug>.md
    - [[repos/<name>/overview]]        → wiki/repos/<name>/overview.md
    - [[concepts/<slug>]]              → wiki/concepts/<slug>.md
    - [[views/<filename>]]             → wiki/views/<filename>.md
    - [[insights/<filename>]]          → wiki/insights/<filename>.md
    """
    errors = []
    pages = _read_wiki_pages(wiki_root)

    # Build resolvable targets relative to wiki/
    wiki_strs = {
        str(p.relative_to(wiki_root).with_suffix("")).lower().replace("\\", "/")
        for p in pages
    }

    def _resolves(target: str, page_rel: str) -> bool:
        """Check if a wikilink target resolves to any known wiki page.

        Tries resolution strategies in order:
        1. Exact match against all relative paths
        2. Relative to the page's own directory
        3. Prepend 'repos/' (for shorthand like [[nanobot/overview]])
        4. Prepend 'concepts/' (for shorthand like [[some-concept]])
        5. Suffix match: for targets like [[entities/xxx]], find
           any page whose path ends with /entities/xxx
        """
        t = target.lower().replace("\\", "/")

        # Strategy 1: exact match
        if t in wiki_strs:
            return True

        # Strategy 2: relative to page's directory
        page_dir = "/".join(page_rel.split("/")[:-1]) if "/" in page_rel else ""
        if page_dir:
            candidate = f"{page_dir}/{t}"
            if candidate in wiki_strs:
                return True

        # Strategy 3: prepend repos/ (e.g. [[nanobot/overview]] -> repos/nanobot/overview)
        candidate = f"repos/{t}"
        if candidate in wiki_strs:
            return True

        # Strategy 4: prepend concepts/
        candidate = f"concepts/{t}"
        if candidate in wiki_strs:
            return True

        # Strategy 5: suffix match — for [[entities/xxx]] or [[repos/r/xxx]]
        # Build a suffix index lazily
        if not hasattr(_resolves, "suffix_index"):
            suffix_index = {}
            for w in wiki_strs:
                parts = w.split("/")
                # Index by last 2, 3, 4 segments
                for n in (2, 3):
                    if len(parts) >= n:
                        key = "/".join(parts[-n:])
                        suffix_index.setdefault(key, set()).add(w)
            _resolves.suffix_index = suffix_index

        if t in _resolves.suffix_index:
            return True

        return False

    for page in pages:
        page_rel = str(page.relative_to(wiki_root))
        content = page.read_text(errors="replace")
        for m in WIKILINK_RE.finditer(content):
            target = m.group(1).strip()
            # Skip pipeline intermediate paths (seeds/, evolve-signals/)
            # — these are project-level artifacts, not wiki pages
            if target.lower().split("/")[0] in {"seeds", "evolve-signals"}:
                continue
            if not _resolves(target, page_rel):
                errors.append({
                    "level": "ERROR",
                    "rule": "check_broken_wikilinks",
                    "file": page_rel,
                    "detail": f"[[{target}]] — target file not found",
                })
    return errors


def check_orphan_pages(wiki_root: Path) -> list:
    """[WARN] Pages not referenced by any other wiki page (excluding maintenance files)."""
    maintenance_files = {"hot.md", "log.md", "index.md"}
    pages = [p for p in _read_wiki_pages(wiki_root)
             if p.name not in maintenance_files]

    # Build set of all link targets mentioned anywhere with resolution
    linked = set()
    for page in pages:
        content = page.read_text(errors="replace")
        for m in WIKILINK_RE.finditer(content):
            target = m.group(1).strip().lower().replace("\\", "/")
            linked.add(target)
            # Also try common resolutions (same as check_broken_wikilinks)
            page_rel = str(page.relative_to(wiki_root))
            page_dir = "/".join(page_rel.split("/")[:-1]) if "/" in page_rel else ""
            if page_dir:
                linked.add(f"{page_dir}/{target}")
            linked.add(f"repos/{target}")
            linked.add(f"concepts/{target}")

    # Build suffix index for cross-repo entity resolution (for wikilinks like [[entities/x]])
    suffix_index = {}
    for p in pages:
        rel = str(p.relative_to(wiki_root).with_suffix("")).replace("\\", "/")
        parts = rel.split("/")
        for n in (2, 3):
            if len(parts) >= n:
                key = "/".join(parts[-n:])
                suffix_index.setdefault(key, set()).add(rel)

    # Build aliases for each page (how it can be referenced)
    def _page_aliases(rel: str) -> set:
        parts = rel.split("/")
        aliases = {rel}
        if len(parts) >= 3 and parts[0] == "repos":
            aliases.add("/".join(parts[1:]))        # r/overview
        if len(parts) >= 4 and parts[2] == "entities":
            aliases.add("/".join(parts[2:]))         # entities/x
        return {a.lower() for a in aliases}

    def _is_linked(rel: str) -> bool:
        """Check if any alias of this page appears in linked set."""
        for alias in _page_aliases(rel):
            if alias in linked:
                return True
            # Check suffix-index entries for this alias
            parts = alias.split("/")
            for n in (2, 3):
                if len(parts) >= n:
                    key = "/".join(parts[-n:])
                    if key in suffix_index:
                        if any(suffix_alias in linked for suffix_alias in suffix_index[key]):
                            return True
        return False

    # Also scan index.md wikilinks into the linked set (even though index.md
    # itself is excluded from the pages list)
    index = wiki_root / "index.md"
    if index.exists():
        for m in WIKILINK_RE.finditer(index.read_text(errors="replace")):
            target = m.group(1).strip().lower().replace("\\", "/")
            linked.add(target)
            linked.add(f"repos/{target}")
            linked.add(f"concepts/{target}")

    warnings = []
    index_content = index.read_text(errors="replace") if index.exists() else ""
    exclude_dirs = {"seeds", "evolve-signals"}

    for page in pages:
        if page == index:
            continue
        # Skip pipeline intermediates
        if any(d in page.parts for d in exclude_dirs):
            continue
        rel = str(page.relative_to(wiki_root).with_suffix("")).replace("\\", "/")
        if not _is_linked(rel) and rel.lower() not in index_content.lower():
            warnings.append({
                "level": "WARN",
                "rule": "check_orphan_pages",
                "file": str(page.relative_to(wiki_root)),
                "detail": rel,
            })
    return warnings


def check_missing_provenance(wiki_root: Path) -> list:
    """[WARN] Entity/Concept pages with no ^[...] provenance references.

    Checks entity pages (wiki/repos/*/entities/*.md) and
    concept pages (wiki/concepts/*.md). Skips redirect pages.
    """
    warnings = []
    for page in _read_wiki_pages(wiki_root):
        body, fm = _strip_frontmatter(page.read_text(errors="replace"))
        page_type = fm.get("type", "")

        # Only check entity and concept pages
        if page_type not in ("entity", "concept"):
            continue

        # Skip redirect pages
        if fm.get("redirect_to"):
            continue

        if not PROVENANCE_RE.search(body):
            warnings.append({
                "level": "WARN",
                "rule": "check_missing_provenance",
                "file": str(page.relative_to(wiki_root)),
                "detail": "no ^[file:line] provenance references found",
            })
    return warnings


def check_concept_repos_consistency(wiki_root: Path) -> list:
    """[ERROR/WARN] Concept pages: frontmatter repos: must match body content.

    Three checks:
    1. [ERROR] Body repo section (### <name>) not in frontmatter repos: →
       Concept page discusses a repo but frontmatter doesn't list it.
       Causes Obsidian Graph isolation — the repo's entities can't link back.
    2. [WARN] Frontmatter repo not in body wikilinks ([[repos/X/entities/Y]]): →
       Frontmatter claims coverage but body has no source evidence from that repo.
    3. [WARN] Body wikilink repo not in frontmatter: →
       Body links to an entity whose repo isn't declared in frontmatter.
    """
    errors = []
    warnings = []
    concepts_root = wiki_root / "concepts"
    if not concepts_root.exists():
        return []

    # Build known repo names from wiki/repos/ directories
    repos_root = wiki_root / "repos"
    known_repos = set()
    if repos_root.exists():
        for d in repos_root.iterdir():
            if d.is_dir():
                known_repos.add(d.name)

    for page in concepts_root.rglob("*.md"):
        body, fm = _strip_frontmatter(page.read_text(errors="replace"))
        if fm.get("type") != "concept" or fm.get("redirect_to"):
            continue

        page_rel = str(page.relative_to(wiki_root))

        # Parse frontmatter repos: field (supports both [a, b] and [a,b])
        repos_raw = fm.get("repos", "")
        front_repos = set()
        if repos_raw:
            # Strip brackets and split
            cleaned = repos_raw.strip().lstrip("[").rstrip("]")
            for r in cleaned.split(","):
                r = r.strip()
                if r:
                    front_repos.add(r)

        # Extract wikilink repos: [[repos/<repo>/entities/<slug>]]
        wiki_repos = set()
        for m in WIKILINK_RE.finditer(body):
            target = m.group(1).strip()
            parts = target.split("/")
            if len(parts) >= 3 and parts[0] == "repos" and parts[2] == "entities":
                wiki_repos.add(parts[1])

        # Extract section-header repos: ### <name> where name is a known repo
        section_repos = set()
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("### ") or stripped.startswith("#### "):
                header_text = stripped.lstrip("#").strip()
                # Check if this header names a known repo
                if header_text in known_repos:
                    section_repos.add(header_text)

        # Check 1: [ERROR] section repo not in frontmatter
        missing_from_front = section_repos - front_repos
        if missing_from_front:
            errors.append({
                "level": "ERROR",
                "rule": "check_concept_repos_consistency",
                "file": page_rel,
                "detail": f"body has ### section(s) for {sorted(missing_from_front)} "
                          f"but frontmatter repos: lists {sorted(front_repos)}. "
                          f"Add missing repos to frontmatter or add wikilinks to entity pages.",
            })

        # Check 2: [WARN] frontmatter repo has no wikilink in body
        missing_wikilinks = front_repos - wiki_repos
        if missing_wikilinks:
            warnings.append({
                "level": "WARN",
                "rule": "check_concept_repos_consistency",
                "file": page_rel,
                "detail": f"frontmatter repos: {sorted(front_repos)} but no "
                          f"[[repos/X/entities/Y]] wikilink found for {sorted(missing_wikilinks)}. "
                          f"Body should link to entity pages for each listed repo.",
            })

        # Check 3: [WARN] wikilink repo not in frontmatter
        missing_from_wiki = wiki_repos - front_repos
        if missing_from_wiki:
            warnings.append({
                "level": "WARN",
                "rule": "check_concept_repos_consistency",
                "file": page_rel,
                "detail": f"body has wikilinks to {sorted(missing_from_wiki)} entities "
                          f"but frontmatter repos: lists {sorted(front_repos)}. "
                          f"Add repos to frontmatter for complete coverage.",
            })

    return errors + warnings


def check_views_freshness(wiki_root: Path) -> list:
    """[INFO] views/ pages older than any of their source pages.

    sources frontmatter must be a single-line JSON array, e.g.:
      sources: ["wiki/concepts/memory-backend.md","wiki/repos/nanobot/entities/memory.md"]
    """
    import json as _json
    infos = []
    views_root = wiki_root / "views"
    if not views_root.exists():
        return []
    for view_page in views_root.rglob("*.md"):
        _, fm = _strip_frontmatter(view_page.read_text(errors="replace"))
        generated = fm.get("generated")
        if not generated:
            continue
        sources_raw = fm.get("sources", "[]").strip()
        try:
            source_paths = _json.loads(sources_raw)
        except (_json.JSONDecodeError, TypeError):
            continue
        for src_rel in source_paths:
            src = wiki_root.parent / src_rel
            if src.exists():
                _, src_fm = _strip_frontmatter(src.read_text(errors="replace"))
                src_gen = src_fm.get("generated", "")
                if src_gen > generated:
                    infos.append({
                        "level": "INFO",
                        "rule": "check_views_freshness",
                        "file": str(view_page.relative_to(wiki_root)),
                        "detail": f"source {src.name} (generated {src_gen}) is newer than this view ({generated})",
                    })
    return infos


def check_pipeline_file_placement(wiki_root: Path) -> list:
    """[ERROR] Pipeline intermediate files (seeds/, evolve-signals/) misplaced under wiki/.

    Pipeline intermediates belong at project root (alongside wiki/), not under wiki/repos/<name>/.
    If found under wiki/, it means an ingest subagent wrote to the wrong path.

    Checks both directories and individual files.
    """
    errors = []
    project_root = wiki_root.parent

    # Check for misplaced directories under wiki/repos/<name>/
    for repo_dir in (wiki_root / "repos").iterdir() if (wiki_root / "repos").exists() else []:
        if not repo_dir.is_dir():
            continue
        for bad_dir in ("seeds", "evolve-signals"):
            misplaced = repo_dir / bad_dir
            if misplaced.exists():
                files_inside = list(misplaced.rglob("*.md"))
                errors.append({
                    "level": "ERROR",
                    "rule": "check_pipeline_file_placement",
                    "file": str(misplaced.relative_to(wiki_root)),
                    "detail": f"pipeline directory '{bad_dir}/' misplaced under wiki/repos/. "
                              f"Should be at project root: {bad_dir}/. "
                              f"({len(files_inside)} files inside: {', '.join(f.name for f in files_inside)})",
                })

    # Also check for individual pipeline files directly under wiki/repos/ (without a subdirectory)
    for bad_dir in ("seeds", "evolve-signals"):
        misplaced_in_wiki = wiki_root / bad_dir
        if misplaced_in_wiki.exists():
            errors.append({
                "level": "ERROR",
                "rule": "check_pipeline_file_placement",
                "file": str(misplaced_in_wiki.relative_to(project_root)),
                "detail": f"pipeline directory '{bad_dir}/' misplaced under wiki/. "
                          f"Should be at project root: {bad_dir}/.",
            })

    return errors


def run_all(wiki_root: Path) -> list:
    findings = []
    findings += check_broken_wikilinks(wiki_root)
    findings += check_pipeline_file_placement(wiki_root)
    findings += check_orphan_pages(wiki_root)
    findings += check_concept_repos_consistency(wiki_root)
    findings += check_missing_provenance(wiki_root)
    findings += check_views_freshness(wiki_root)
    return findings


def main():
    parser = argparse.ArgumentParser(description="Lint codebase wiki health.")
    parser.add_argument("--wiki", default="wiki", help="Path to wiki/ root")
    args = parser.parse_args()

    wiki_root = Path(args.wiki)

    findings = run_all(wiki_root)

    has_error = False
    for f in findings:
        print(f"[{f['level']}] {f['rule']}  {f['file']} — {f['detail']}")
        if f["level"] == "ERROR":
            has_error = True

    if not findings:
        print("✓ No issues found.")

    sys.exit(1 if has_error else 0)


if __name__ == "__main__":
    main()
