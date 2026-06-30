# tests/test_lint.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lint import (
    check_broken_wikilinks,
    check_orphan_pages,
    check_missing_provenance,
    check_views_freshness,
)


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ---- check_broken_wikilinks ----

def test_check_broken_wikilinks_entity_missing(tmp_path):
    """[[repos/hermes/entities/memory]] resolves to wiki/repos/hermes/entities/memory.md."""
    write(tmp_path / "wiki/repos/openclaw/entities/agent.md",
          "See also [[repos/hermes/entities/memory]]")
    errors = check_broken_wikilinks(tmp_path / "wiki")
    assert len(errors) == 1
    assert "repos/hermes/entities/memory" in errors[0]["detail"]


def test_check_broken_wikilinks_entity_present(tmp_path):
    write(tmp_path / "wiki/repos/openclaw/entities/agent.md",
          "See also [[repos/hermes/entities/memory]]")
    write(tmp_path / "wiki/repos/hermes/entities/memory.md", "# Memory")
    errors = check_broken_wikilinks(tmp_path / "wiki")
    assert errors == []


def test_check_broken_wikilinks_concept_resolves(tmp_path):
    """[[concepts/memory-backend]] resolves to wiki/concepts/memory-backend.md."""
    write(tmp_path / "wiki/repos/openclaw/entities/memory.md",
          "**关联 Concept**：[[concepts/memory-backend]]")
    write(tmp_path / "wiki/concepts/memory-backend.md", "# Memory Backend")
    errors = check_broken_wikilinks(tmp_path / "wiki")
    assert errors == []


def test_check_broken_wikilinks_concept_missing(tmp_path):
    write(tmp_path / "wiki/repos/openclaw/entities/memory.md",
          "**关联 Concept**：[[concepts/nonexistent]]")
    errors = check_broken_wikilinks(tmp_path / "wiki")
    assert len(errors) == 1
    assert "concepts/nonexistent" in errors[0]["detail"]


def test_check_broken_wikilinks_overview_resolves(tmp_path):
    write(tmp_path / "wiki/concepts/agent-style.md",
          "来源：[[repos/openclaw/overview]]")
    write(tmp_path / "wiki/repos/openclaw/overview.md", "# OpenClaw")
    errors = check_broken_wikilinks(tmp_path / "wiki")
    assert errors == []


# ---- check_orphan_pages ----

def test_check_orphan_pages(tmp_path):
    write(tmp_path / "wiki/index.md", "# Index\n- [[repos/openclaw/overview]]")
    write(tmp_path / "wiki/repos/openclaw/overview.md", "# OpenClaw")
    write(tmp_path / "wiki/repos/openclaw/entities/isolated.md", "# Nobody links me")
    warnings = check_orphan_pages(tmp_path / "wiki")
    orphan_paths = [w["detail"] for w in warnings]
    assert any("isolated" in p for p in orphan_paths)


def test_check_orphan_pages_skip_maintenance(tmp_path):
    """hot.md, log.md, index.md should never be flagged as orphan."""
    write(tmp_path / "wiki/hot.md", "# Hot")
    write(tmp_path / "wiki/log.md", "# Log")
    warnings = check_orphan_pages(tmp_path / "wiki")
    orphan_names = [Path(w["file"]).name for w in warnings]
    assert "hot.md" not in orphan_names
    assert "log.md" not in orphan_names


# ---- check_missing_provenance ----

def test_check_missing_provenance_entity(tmp_path):
    write(tmp_path / "wiki/repos/openclaw/entities/agent.md",
          "---\ntype: entity\nrepo: openclaw\nslug: agent\nproblem: 如何定义Agent\n"
          "generated: 2026-06-25\nsource_files:\n  - src/agent.ts\n---\n"
          "# Agent\n\nOpenClaw uses YAML config to define agents.")
    warnings = check_missing_provenance(tmp_path / "wiki")
    assert len(warnings) == 1
    assert "agent.md" in warnings[0]["file"]


def test_check_missing_provenance_entity_passes(tmp_path):
    write(tmp_path / "wiki/repos/openclaw/entities/agent.md",
          "---\ntype: entity\nrepo: openclaw\nslug: agent\nproblem: 如何定义Agent\n"
          "generated: 2026-06-25\nsource_files:\n  - src/agent.ts\n---\n"
          "# Agent\n\nOpenClaw uses YAML. ^[src/agent.ts:42-58]")
    warnings = check_missing_provenance(tmp_path / "wiki")
    assert warnings == []


def test_check_missing_provenance_concept(tmp_path):
    write(tmp_path / "wiki/concepts/agent-style.md",
          "---\ntype: concept\nconcept: agent-style\nproblem: 如何定义Agent\n"
          "concerns: [声明式便捷性, 编程灵活性]\nrepos: [openclaw]\ngenerated: 2026-06-25\n---\n"
          "# Agent Style\n\n配置驱动提供简单性但灵活性受限。")
    warnings = check_missing_provenance(tmp_path / "wiki")
    assert len(warnings) == 1
    assert "agent-style.md" in warnings[0]["file"]


def test_check_missing_provenance_skips_redirect(tmp_path):
    """Redirect pages should not be checked for provenance."""
    write(tmp_path / "wiki/concepts/old-name.md",
          "---\nredirect_to: new-name\nreason: renamed\ndate: 2026-06-25\n---\n"
          "# Old Name\n> 此页面已合并至 [[new-name]]。")
    warnings = check_missing_provenance(tmp_path / "wiki")
    assert warnings == []


def test_check_missing_provenance_skips_non_entity_concept(tmp_path):
    """Pages without type: entity or type: concept should be skipped."""
    write(tmp_path / "wiki/repos/openclaw/overview.md",
          "---\ntype: overview\nrepo: openclaw\ngenerated: 2026-06-25\n---\n"
          "# OpenClaw\nNo provenance here.")
    warnings = check_missing_provenance(tmp_path / "wiki")
    assert warnings == []


# ---- check_views_freshness ----

def test_check_views_freshness_newer_source(tmp_path):
    import json
    write(tmp_path / "wiki/concepts/agent-style.md",
          "---\ntype: concept\ngenerated: 2026-06-20\n---\n# Agent Style")
    write(tmp_path / "wiki/views/categories/2026-06-15-compare.md",
          f"---\ntype: view\nrepos: [openclaw]\ngenerated: 2026-06-15\n"
          f'sources: {json.dumps(["wiki/concepts/agent-style.md"])}\n---\n# Compare')
    infos = check_views_freshness(tmp_path / "wiki")
    assert len(infos) == 1
    assert "newer" in infos[0]["detail"]


def test_check_views_freshness_fresh(tmp_path):
    import json
    write(tmp_path / "wiki/concepts/agent-style.md",
          "---\ntype: concept\ngenerated: 2026-06-10\n---\n# Agent Style")
    write(tmp_path / "wiki/views/categories/2026-06-15-compare.md",
          f"---\ntype: view\nrepos: [openclaw]\ngenerated: 2026-06-15\n"
          f'sources: {json.dumps(["wiki/concepts/agent-style.md"])}\n---\n# Compare')
    infos = check_views_freshness(tmp_path / "wiki")
    assert infos == []
