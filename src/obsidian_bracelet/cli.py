from __future__ import annotations
import json
from pathlib import Path
import typer
from rich import print

app = typer.Typer(add_completion=False, no_args_is_help=True, help="Obsidian vault merger")

def main():
    app()

@app.command(help="Scan vaults and build a merge plan (dry-run).")
def plan(
    source: list[Path] = typer.Option(..., "--source", "-s", exists=True, file_okay=False, dir_okay=True, readable=True, help="Path to a source Obsidian vault (repeatable)"),
    target: Path = typer.Option(..., "--target", "-t", file_okay=False, dir_okay=True, help="Directory where the merged vault will be created"),
    ignore_patterns: list[str] = typer.Option([], "--ignore", "-i", help="Regex patterns to ignore files (repeatable)"),
    output: Path = typer.Option("merge-plan.json", "--output", "-o", help="Where to write the plan JSON"),
):
    from .planner import build_plan
    plan = build_plan([Path(p).resolve() for p in source], Path(target).resolve(), ignore_patterns=ignore_patterns)
    output.write_text(json.dumps(plan, indent=2, ensure_ascii=False))
    print(f"[green]Wrote plan:[/green] {output}")

@app.command(help="Apply a merge plan JSON file to the target location.")
def apply(
    plan_file: Path = typer.Argument(..., exists=True),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate apply without changing files"),
):
    from .apply import apply_plan
    import json
    plan = json.loads(Path(plan_file).read_text())
    apply_plan(plan, dry_run=dry_run)

@app.command(help="Launch the GUI to review and apply a plan.")
def gui(
    source: list[Path] = typer.Option(None, "--source", "-s"),
    target: Path = typer.Option(None, "--target", "-t"),
    plan_file: Path = typer.Option(None, "--plan-file", "-p"),
):
    from .gui import main as gui_main
    gui_main(source=source, target=target, plan_file=plan_file)

if __name__ == "__main__":
    main()
