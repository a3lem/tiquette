"""Behavioral tests for monorepo store targeting: --dir and `ls -r`.

# spec: ticket-store
# spec: ticket-query
# spec: ticket-relationships
# spec: id-resolution

Unlike the other CLI tests, these do not set TICKETS_DIR at a single store.
They build a throwaway monorepo tree and invoke `tq` with `cwd` set to a
directory inside it, so walk-up and `-r` discovery operate on the tree. The
`tq` console script is invoked directly (its shebang points at the project
venv) so `cwd` is free to be the temp tree rather than the project root.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

_PROJECT = Path(__file__).resolve().parents[1]


def _tq_bin() -> str:
    out = subprocess.run(
        ["uv", "run", "python", "-c",
         "import sys, os; print(os.path.join(os.path.dirname(sys.executable), 'tq'))"],
        capture_output=True, text=True, cwd=str(_PROJECT),
    )
    return out.stdout.strip()


TQ = _tq_bin()


def run(*args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Invoke tq in `cwd` with TICKETS_DIR removed (unless supplied in `env`)."""
    run_env = os.environ.copy()
    run_env.pop("TICKETS_DIR", None)
    if env:
        run_env.update(env)
    return subprocess.run(
        [TQ, *args], capture_output=True, text=True, cwd=str(cwd), env=run_env
    )


@pytest.fixture
def monorepo(tmp_path: Path) -> Path:
    """A tree with packages/api and packages/web project dirs (no stores yet)."""
    (tmp_path / "packages" / "api").mkdir(parents=True)
    (tmp_path / "packages" / "web").mkdir(parents=True)
    return tmp_path


def _create(root: Path, dir_: str | None, title: str, *extra: str) -> str:
    args = (["--dir", dir_] if dir_ is not None else []) + ["create", title, *extra]
    r = run(*args, cwd=root)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


# ── ticket-store: Store targeting with --dir ─────────────────────────


class TestDirTargeting:
    # spec: ticket-store requirement=store-targeting-with-dir scenario=--dir-targets-a-sibling-store-for-listing
    def test_dir_targets_sibling_store(self, monorepo: Path) -> None:
        api = _create(monorepo, "packages/api", "API work")
        web = _create(monorepo, "packages/web", "Web work")
        r = run("--dir", "packages/api", "ls", cwd=monorepo)
        assert r.returncode == 0, r.stderr
        assert api in r.stdout
        assert web not in r.stdout

    # spec: ticket-store requirement=store-targeting-with-dir scenario=--dir-create-initializes-the-store-at-the-path
    def test_dir_create_initializes_store(self, monorepo: Path) -> None:
        tid = _create(monorepo, "packages/api", "First")
        assert (monorepo / "packages" / "api" / ".tickets" / f"{tid}.md").is_file()

    # spec: ticket-store requirement=store-targeting-with-dir scenario=--dir-create-derives-the-id-prefix-from-the-path
    def test_dir_create_derives_prefix(self, monorepo: Path) -> None:
        tid = _create(monorepo, "packages/api", "First")
        assert re.match(r"^api-[a-f0-9]{4}$", tid), tid

    # spec: ticket-store requirement=store-targeting-with-dir scenario=--dir-prevails-over-tickets_dir-when-both-are-set
    def test_dir_prevails_over_tickets_dir(self, monorepo: Path) -> None:
        other = monorepo / "other" / ".tickets"
        other.mkdir(parents=True)
        oth = _create(monorepo, "other", "Other")  # writes other/.tickets
        api = _create(monorepo, "packages/api", "API")
        r = run("--dir", "packages/api", "ls", cwd=monorepo,
                env={"TICKETS_DIR": str(other)})
        assert api in r.stdout
        assert oth not in r.stdout

    # spec: ticket-store requirement=store-targeting-with-dir scenario=--dir-with-a-missing-store-errors-on-a-read-command
    def test_dir_missing_store_errors_on_read(self, monorepo: Path) -> None:
        r = run("--dir", "packages/api", "ls", cwd=monorepo)
        assert r.returncode != 0
        assert "tickets" in r.stderr.lower()


# ── ticket-store: Directory walking precedence ───────────────────────


class TestDirectoryWalkingPrecedence:
    # spec: ticket-store requirement=directory-walking scenario=tickets_dir-takes-priority-over-walk-up
    def test_tickets_dir_beats_walk_up(self, monorepo: Path) -> None:
        # A store exists at the root (walk-up target from a nested cwd)...
        _create(monorepo, ".", "root ticket")
        # ...and TICKETS_DIR points elsewhere.
        env_store = monorepo / "packages" / "api" / ".tickets"
        env_store.mkdir(parents=True)
        api = _create(monorepo, "packages/api", "api ticket")
        nested = monorepo / "packages" / "web"  # cwd where walk-up would hit root
        r = run("ls", cwd=nested, env={"TICKETS_DIR": str(env_store)})
        assert api in r.stdout  # env store wins over walk-up


# ── ticket-store: Recursive store discovery ──────────────────────────


class TestRecursiveDiscovery:
    # spec: ticket-store requirement=recursive-store-discovery scenario=discovers-nested-stores-under-the-root
    def test_discovers_nested_stores(self, monorepo: Path) -> None:
        api = _create(monorepo, "packages/api", "API")
        web = _create(monorepo, "packages/web", "Web")
        r = run("ls", "-r", cwd=monorepo)
        assert r.returncode == 0, r.stderr
        assert api in r.stdout
        assert web in r.stdout

    # spec: ticket-store requirement=recursive-store-discovery scenario=includes-the-roots-own-store
    def test_includes_root_store(self, monorepo: Path) -> None:
        root = _create(monorepo, ".", "root")
        api = _create(monorepo, "packages/api", "API")
        r = run("ls", "-r", cwd=monorepo)
        assert root in r.stdout
        assert api in r.stdout

    # spec: ticket-store requirement=recursive-store-discovery scenario=skips-vcs-and-dependency-directories
    def test_skips_vcs_and_dependency_dirs(self, monorepo: Path) -> None:
        (monorepo / "node_modules" / "pkg").mkdir(parents=True)
        (monorepo / ".git").mkdir()
        dep = _create(monorepo, "node_modules/pkg", "noise")
        git = _create(monorepo, ".git", "gitnoise")
        api = _create(monorepo, "packages/api", "API")
        r = run("ls", "-r", cwd=monorepo)
        assert api in r.stdout
        assert dep not in r.stdout
        assert git not in r.stdout

    # spec: ticket-store requirement=recursive-store-discovery scenario=recursive-mode-does-not-walk-up-from-the-root
    def test_recursive_does_not_walk_up(self, monorepo: Path) -> None:
        # Store lives at the root; cwd is a nested dir with nothing at/below it.
        root = _create(monorepo, ".", "root only")
        nested = monorepo / "packages" / "web"  # empty dir, no store below
        r = run("ls", "-r", cwd=nested)
        assert r.returncode == 0, r.stderr
        assert root not in r.stdout
        assert r.stdout.strip() == ""

    # spec: ticket-store requirement=recursive-store-discovery scenario=a-stores-archive-is-not-treated-as-a-separate-store
    def test_archive_not_a_separate_store(self, monorepo: Path) -> None:
        api = _create(monorepo, "packages/api", "API")
        run("--dir", "packages/api", "close", api, cwd=monorepo)
        run("--dir", "packages/api", "archive", cwd=monorepo)
        r = run("ls", "-r", "--all", cwd=monorepo)
        assert r.stdout.count("packages/api") == 1


# ── ticket-query: Recursive listing across stores ────────────────────


class TestRecursiveListing:
    # spec: ticket-query requirement=recursive-listing-across-stores scenario=recursive-listing-groups-output-by-store
    def test_groups_by_store(self, monorepo: Path) -> None:
        api = _create(monorepo, "packages/api", "API work")
        web = _create(monorepo, "packages/web", "Web work")
        r = run("ls", "-r", cwd=monorepo)
        out = r.stdout
        assert out.index("packages/api") < out.index(api)
        assert out.index("packages/web") < out.index(web)

    # spec: ticket-query requirement=recursive-listing-across-stores scenario=recursive-listing-orders-stores-lexicographically
    def test_orders_stores_lexicographically(self, monorepo: Path) -> None:
        _create(monorepo, "packages/web", "Web")
        _create(monorepo, "packages/api", "API")
        r = run("ls", "-r", cwd=monorepo)
        assert r.stdout.index("packages/api") < r.stdout.index("packages/web")

    # spec: ticket-query requirement=recursive-listing-across-stores scenario=recursive-listing-omits-stores-with-no-matching-tickets
    def test_omits_empty_stores(self, monorepo: Path) -> None:
        api = _create(monorepo, "packages/api", "API open")
        web = _create(monorepo, "packages/web", "Web closed")
        run("--dir", "packages/web", "close", web, cwd=monorepo)
        r = run("ls", "-r", "--status", "open", cwd=monorepo)
        assert api in r.stdout
        assert "packages/web" not in r.stdout

    # spec: ticket-query requirement=recursive-listing-across-stores scenario=filters-apply-within-each-store
    def test_filters_apply_within_each_store(self, monorepo: Path) -> None:
        a1 = _create(monorepo, "packages/api", "urgent one", "--tag", "urgent")
        a2 = _create(monorepo, "packages/api", "later one", "--tag", "later")
        w1 = _create(monorepo, "packages/web", "urgent web", "--tag", "urgent")
        r = run("ls", "-r", "--tag", "urgent", cwd=monorepo)
        assert a1 in r.stdout
        assert w1 in r.stdout
        assert a2 not in r.stdout

    # spec: ticket-query requirement=recursive-listing-across-stores scenario=source-axis-applies-within-each-store
    def test_source_axis_within_each_store(self, monorepo: Path) -> None:
        api = _create(monorepo, "packages/api", "API to archive")
        run("--dir", "packages/api", "close", api, cwd=monorepo)
        run("--dir", "packages/api", "archive", cwd=monorepo)
        web = _create(monorepo, "packages/web", "Web active")
        r = run("ls", "-r", "--archived", cwd=monorepo)
        assert api in r.stdout
        assert web not in r.stdout

    # spec: ticket-query requirement=recursive-listing-across-stores scenario=recursive-jsonl-emits-a-flat-stream-tagged-with-store
    def test_jsonl_flat_with_store_field(self, monorepo: Path) -> None:
        api = _create(monorepo, "packages/api", "API")
        web = _create(monorepo, "packages/web", "Web")
        r = run("ls", "-r", "--jsonl", cwd=monorepo)
        rows = [json.loads(line) for line in r.stdout.splitlines() if line.strip()]
        by_id = {row["id"]: row for row in rows}
        assert by_id[api]["store"] == "packages/api"
        assert by_id[web]["store"] == "packages/web"

    # spec: ticket-query requirement=recursive-listing-across-stores scenario=recursive-listing-includes-the-root-store-as-.
    def test_root_store_heading_is_dot(self, monorepo: Path) -> None:
        root = _create(monorepo, ".", "root ticket")
        _create(monorepo, "packages/api", "API")
        r = run("ls", "-r", cwd=monorepo)
        lines = r.stdout.splitlines()
        assert "." in lines
        assert lines.index(".") < lines.index(next(l for l in lines if root in l))

    # spec: ticket-query requirement=recursive-listing-across-stores scenario=-r-and---parent-are-mutually-exclusive
    def test_r_and_parent_exclusive(self, monorepo: Path) -> None:
        r = run("ls", "-r", "--parent", "epic-001", cwd=monorepo)
        assert r.returncode != 0

    # spec: ticket-query requirement=recursive-listing-across-stores scenario=-r-and---dep-are-mutually-exclusive
    def test_r_and_dep_exclusive(self, monorepo: Path) -> None:
        r = run("ls", "-r", "--dep", "task-001", cwd=monorepo)
        assert r.returncode != 0


# ── ticket-relationships: Relationships are store-local ──────────────


class TestStoreLocalRelationships:
    # spec: ticket-relationships requirement=relationships-are-store-local scenario=cross-store-dependency-target-is-rejected
    def test_cross_store_dep_rejected(self, monorepo: Path) -> None:
        api = _create(monorepo, "packages/api", "API")
        web = _create(monorepo, "packages/web", "Web")
        r = run("--dir", "packages/web", "edit", web, "--dep", api, cwd=monorepo)
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()
        info = run("--dir", "packages/web", "info", web, cwd=monorepo)
        assert api not in info.stdout

    # spec: ticket-relationships requirement=relationships-are-store-local scenario=cross-store-parent-target-is-rejected
    def test_cross_store_parent_rejected(self, monorepo: Path) -> None:
        api = _create(monorepo, "packages/api", "API")
        web = _create(monorepo, "packages/web", "Web")
        r = run("--dir", "packages/web", "edit", web, "--parent", api, cwd=monorepo)
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    # spec: ticket-relationships requirement=relationships-are-store-local scenario=within-store-relationships-are-unaffected
    def test_within_store_relationship_works(self, monorepo: Path) -> None:
        a = _create(monorepo, "packages/web", "Web A")
        b = _create(monorepo, "packages/web", "Web B")
        r = run("--dir", "packages/web", "edit", a, "--dep", b, cwd=monorepo)
        assert r.returncode == 0, r.stderr
        info = run("--dir", "packages/web", "info", a, cwd=monorepo)
        assert b in info.stdout


# ── id-resolution: Resolution is scoped to a single store ────────────


class TestSingleStoreResolution:
    # spec: id-resolution requirement=resolution-is-scoped-to-a-single-store scenario=resolution-stays-within-the-targeted-store
    def test_resolution_scoped_to_store(self, monorepo: Path) -> None:
        # Force a shared suffix by seeding raw files with colliding IDs.
        api_store = monorepo / "packages" / "api" / ".tickets"
        web_store = monorepo / "packages" / "web" / ".tickets"
        api_store.mkdir(parents=True)
        web_store.mkdir(parents=True)
        _write_raw(api_store, "api-1a2b", "API one")
        _write_raw(web_store, "web-1a2b", "Web one")
        r = run("--dir", "packages/api", "show", "1a2b", cwd=monorepo)
        assert r.returncode == 0, r.stderr
        assert "id: api-1a2b" in r.stdout
        assert "web-1a2b" not in r.stdout

    # spec: id-resolution requirement=resolution-is-scoped-to-a-single-store scenario=a-partial-matching-only-another-store-is-not-found
    def test_partial_only_in_other_store_not_found(self, monorepo: Path) -> None:
        _create(monorepo, "packages/api", "API")
        web = _create(monorepo, "packages/web", "Web")
        suffix = web.split("-", 1)[1]
        r = run("--dir", "packages/api", "show", suffix, cwd=monorepo)
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()


def _write_raw(store_dir: Path, tid: str, title: str) -> None:
    """Write a minimal valid ticket file directly, bypassing ID generation."""
    (store_dir / f"{tid}.md").write_text(
        f"---\nid: {tid}\nstatus: open\ntype: task\npriority: 2\n"
        f"deps: []\nlinks: []\ntags: []\ncreated: 2026-07-23T00:00Z\n---\n# {title}\n"
    )
