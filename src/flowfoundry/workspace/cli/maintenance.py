"""``project maintain`` CLI — Python port of cc-projects-maintain."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    """Parse the legacy maintenance wrapper flags and run maintenance."""
    parser = argparse.ArgumentParser(prog="cc-projects-maintain")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--quick", action="store_true")
    modes.add_argument("--deep", action="store_true")
    modes.add_argument("--report", action="store_true")
    modes.add_argument("--sync-managed", action="store_true")
    modes.add_argument("--purge-quarantine", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return run_maintenance_cli(parser.parse_args(argv))


def run_maintenance_cli(args: argparse.Namespace) -> int:
    """Run project maintenance and return exit code."""
    from ..maintenance.projects import run_maintenance

    dry_run = args.dry_run
    if args.quick:
        mode = "quick"
    elif args.deep:
        mode = "deep"
    elif args.report:
        mode = "report"
    elif args.sync_managed:
        mode = "sync-managed"
    elif args.purge_quarantine:
        mode = "purge-quarantine"
    else:
        mode = "quick"  # default

    # Validate PROJECTS_ROOT
    projects_root = Path.home() / "Projects"
    if not projects_root.exists():
        print("错误: PROJECTS_ROOT 不存在。", file=sys.stderr)
        return 1

    try:
        report = run_maintenance(mode, dry_run)
    except Exception as exc:
        print(f"维护失败: {exc}", file=sys.stderr)
        return 1

    if not isinstance(report, dict):
        return 0

    # Print report (mirrors original cc-projects-maintain output format)
    categories = {
        "A": "生产项目 / 最近有活跃的Git仓库且有清晰命名的项目",
        "B": "近期候选 / 最近活跃但尚未命名的项目",
        "C": "较少使用 / 无git或无近期活跃但可能仍有价值的项目",
        "D": "低价值 / 空目录或仅含临时/缓存文件的目录",
        "E": "需清理 / 可用于隔离或清理的目录",
    }
    classification = report.get("classification", {})
    if classification:
        for cat, label in categories.items():
            items = classification.get(cat, [])
            if items:
                print(f"\n[{cat}] {label}:")
                for item in items:
                    print(f"  {item.get('path', item.get('name', str(item)))}")
                    if item.get("suggestion"):
                        print(f"    → {item['suggestion']}")

    if report.get("duplicates"):
        print(f"\n发现 {len(report['duplicates'])} 组重复项目:")
        for dup_group in report["duplicates"]:
            names = [d.get("name", str(d)) for d in dup_group]
            print(f"  {'  ≈  '.join(names)}")

    if report.get("quarantine"):
        print(f"\n隔离建议 ({len(report['quarantine'])} 项):")
        for q in report["quarantine"]:
            print(f"  {q.get('path', q.get('name', str(q)))}")
            if q.get("reason"):
                print(f"    → {q['reason']}")

    if report.get("renamed"):
        print(f"\n重命名建议 ({len(report['renamed'])} 项):")
        for r in report["renamed"]:
            print(f"  {r.get('from', '?')} → {r.get('to', '?')}")

    if report.get("synced"):
        print(f"\n托管仓库同步: {len(report['synced'])} 个已更新")

    if report.get("error"):
        print(f"\n错误: {report['error']}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
