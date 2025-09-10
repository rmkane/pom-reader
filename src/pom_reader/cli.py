"""Command-line interface for POM Reader."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from .logging_config import setup_logging
from .reader import PomAnalyzer, PomReader


@click.group()
@click.version_option()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set the logging level",
)
@click.option(
    "--log-dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    help="Directory for log files (defaults to ~/.local/logs/pom-reader/)",
)
@click.pass_context
def main(ctx: click.Context, log_level: str, log_dir: Path | None) -> None:
    """POM Reader - A modern Python library for parsing and analyzing Maven POM files."""
    # Initialize logging
    logger = setup_logging(level=log_level, log_dir=log_dir)
    logger.info("POM Reader CLI started")

    # Store logger in context for use in commands
    ctx.ensure_object(dict)
    ctx.obj["logger"] = logger


@main.command()
@click.argument("pom_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "tree"]),
    default="table",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def analyze(
    ctx: click.Context, pom_file: Path, output_format: str, verbose: bool
) -> None:
    """Analyze a POM file and show comprehensive information."""
    console = Console()
    logger = ctx.obj["logger"]

    try:
        logger.info(f"Starting analysis of POM file: {pom_file}")

        # Parse the POM file
        reader = PomReader()
        pom = reader.parse_file(pom_file)
        logger.info(
            f"Successfully loaded POM: {pom.project.group_id}:{pom.project.artifact_id}"
        )

        analyzer = PomAnalyzer(pom)

        logger.info(f"Generating analysis in {output_format} format")
        if output_format == "json":
            analysis = analyzer.get_comprehensive_analysis()
            console.print(JSON(json.dumps(analysis, indent=2)))
        elif output_format == "tree":
            _show_tree_view(console, pom, analyzer)
        else:
            _show_table_view(console, pom, analyzer, verbose)

        logger.info("Analysis completed successfully")

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        console.print(f"[red]Error analyzing POM file: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("pom_file", type=click.Path(exists=True, path_type=Path))
@click.option("--tree", is_flag=True, help="Show dependency tree")
@click.option("--scope", help="Filter by dependency scope")
@click.option("--group", help="Filter by group ID")
def dependencies(
    pom_file: Path, tree: bool, scope: str | None, group: str | None
) -> None:
    """Show dependency information."""
    console = Console()

    try:
        reader = PomReader()
        pom = reader.parse_file(pom_file)

        deps = pom.effective_dependencies

        # Apply filters
        if scope:
            deps = [dep for dep in deps if dep.scope == scope]
        if group:
            deps = [dep for dep in deps if dep.group_id == group]

        if tree:
            _show_dependency_tree(console, deps)
        else:
            _show_dependencies_table(console, deps)

    except Exception as e:
        console.print(f"[red]Error analyzing dependencies: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("pom_file", type=click.Path(exists=True, path_type=Path))
@click.option("--group", help="Filter by group ID")
def plugins(pom_file: Path, group: str | None) -> None:
    """Show plugin information."""
    console = Console()

    try:
        reader = PomReader()
        pom = reader.parse_file(pom_file)

        plugins = pom.effective_plugins

        # Apply filter
        if group:
            plugins = [plugin for plugin in plugins if plugin.group_id == group]

        _show_plugins_table(console, plugins)

    except Exception as e:
        console.print(f"[red]Error analyzing plugins: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("pom_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Export format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file (default: stdout)",
)
def export(pom_file: Path, output_format: str, output: Path | None) -> None:
    """Export POM information to JSON or YAML."""
    console = Console()

    try:
        reader = PomReader()
        pom = reader.parse_file(pom_file)
        analyzer = PomAnalyzer(pom)

        analysis = analyzer.get_comprehensive_analysis()

        if output_format == "json":
            content = json.dumps(analysis, indent=2)
        else:  # yaml
            try:
                import yaml  # type: ignore

                content = yaml.dump(analysis, default_flow_style=False)
            except ImportError:
                console.print(
                    "[red]YAML export requires PyYAML. Install with: pip install PyYAML[/red]"
                )
                sys.exit(1)

        if output:
            output.write_text(content)
            console.print(f"[green]Exported to {output}[/green]")
        else:
            console.print(content)

    except Exception as e:
        console.print(f"[red]Error exporting POM: {e}[/red]")
        sys.exit(1)


def _show_table_view(
    console: Console, pom: Any, analyzer: PomAnalyzer, verbose: bool
) -> None:
    """Show analysis in table format."""
    # Project info
    project_info = Panel(
        f"[bold]Project:[/bold] {pom.project.group_id}:{pom.project.artifact_id}\n"
        f"[bold]Version:[/bold] {pom.project.version}\n"
        f"[bold]Packaging:[/bold] {pom.project.packaging}\n"
        f"[bold]Name:[/bold] {pom.project.name or 'N/A'}\n"
        f"[bold]Description:[/bold] {pom.project.description or 'N/A'}",
        title="Project Information",
        border_style="blue",
    )
    console.print(project_info)

    # Dependencies summary
    dep_summary = analyzer.get_dependency_summary()
    dep_table = Table(title="Dependencies Summary")
    dep_table.add_column("Metric", style="cyan")
    dep_table.add_column("Value", style="magenta")

    dep_table.add_row("Total Dependencies", str(dep_summary["total_dependencies"]))
    dep_table.add_row(
        "Optional Dependencies", str(dep_summary["optional_dependencies"])
    )
    dep_table.add_row("With Version", str(dep_summary["dependencies_with_version"]))
    dep_table.add_row(
        "Without Version", str(dep_summary["dependencies_without_version"])
    )

    console.print(dep_table)

    # Dependencies by scope
    if dep_summary["by_scope"]:
        scope_table = Table(title="Dependencies by Scope")
        scope_table.add_column("Scope", style="cyan")
        scope_table.add_column("Count", style="magenta")

        for scope, count in sorted(dep_summary["by_scope"].items()):
            scope_table.add_row(scope, str(count))

        console.print(scope_table)

    # Plugins summary
    plugin_summary = analyzer.get_plugin_summary()
    plugin_table = Table(title="Plugins Summary")
    plugin_table.add_column("Metric", style="cyan")
    plugin_table.add_column("Value", style="magenta")

    plugin_table.add_row("Total Plugins", str(plugin_summary["total_plugins"]))
    plugin_table.add_row("With Version", str(plugin_summary["plugins_with_version"]))
    plugin_table.add_row(
        "Without Version", str(plugin_summary["plugins_without_version"])
    )
    plugin_table.add_row(
        "With Configuration", str(plugin_summary["plugins_with_configuration"])
    )

    console.print(plugin_table)

    # Spring Boot info
    spring_boot_info = analyzer.get_spring_boot_info()
    if spring_boot_info:
        sb_panel = Panel(
            f"[bold]Spring Boot Project:[/bold] Yes\n"
            f"[bold]Spring Boot Dependencies:[/bold] "
            f"{spring_boot_info['spring_boot_dependencies']}\n"
            f"[bold]Has Spring Boot Plugin:[/bold] {spring_boot_info['has_spring_boot_plugin']}",
            title="Spring Boot Information",
            border_style="green",
        )
        console.print(sb_panel)

    # Java version info
    java_info = analyzer.get_java_version_info()
    if java_info and any(java_info.values()):
        java_panel = Panel(
            f"[bold]Java Version Property:[/bold] "
            f"{java_info.get('java_version_property', 'N/A')}\n"
            f"[bold]Compiler Source:[/bold] "
            f"{java_info.get('maven_compiler_source_property', 'N/A')}\n"
            f"[bold]Compiler Target:[/bold] "
            f"{java_info.get('maven_compiler_target_property', 'N/A')}",
            title="Java Version Information",
            border_style="yellow",
        )
        console.print(java_panel)

    # Dependency conflicts
    conflicts = analyzer.find_dependency_conflicts()
    if conflicts:
        conflict_panel = Panel(
            f"[bold red]Found {len(conflicts)} dependency conflicts![/bold red]\n"
            + "\n".join(
                f"- {conflict['coordinates']}: {', '.join(conflict['versions'])}"
                for conflict in conflicts
            ),
            title="Dependency Conflicts",
            border_style="red",
        )
        console.print(conflict_panel)


def _show_tree_view(console: Console, pom: Any, analyzer: PomAnalyzer) -> None:
    """Show analysis in tree format."""
    tree = Tree(
        f"[bold blue]{pom.project.group_id}:{pom.project.artifact_id}[/bold blue] "
        f"v{pom.project.version}"
    )

    # Dependencies
    deps_branch = tree.add("[bold green]Dependencies[/bold green]")
    for dep in pom.effective_dependencies:
        dep_text = f"{dep.group_id}:{dep.artifact_id}"
        if dep.version:
            dep_text += f" v{dep.version}"
        dep_text += f" [{dep.scope}]"
        deps_branch.add(dep_text)

    # Plugins
    plugins_branch = tree.add("[bold yellow]Plugins[/bold yellow]")
    for plugin in pom.effective_plugins:
        plugin_text = f"{plugin.group_id}:{plugin.artifact_id}"
        if plugin.version:
            plugin_text += f" v{plugin.version}"
        plugins_branch.add(plugin_text)

    # Properties
    if pom.properties:
        props_branch = tree.add("[bold magenta]Properties[/bold magenta]")
        for prop in pom.properties[:10]:  # Show first 10 properties
            props_branch.add(f"{prop.name} = {prop.value}")
        if len(pom.properties) > 10:
            props_branch.add(f"... and {len(pom.properties) - 10} more")

    console.print(tree)


def _show_dependency_tree(console: Console, deps: list) -> None:
    """Show dependencies in tree format."""
    tree = Tree("[bold]Dependencies[/bold]")

    # Group by scope
    by_scope: dict[str, list] = {}
    for dep in deps:
        scope = dep.scope
        if scope not in by_scope:
            by_scope[scope] = []
        by_scope[scope].append(dep)

    for scope, scope_deps in sorted(by_scope.items()):
        scope_branch = tree.add(f"[bold]{scope}[/bold]")
        for dep in sorted(scope_deps, key=lambda d: (d.group_id, d.artifact_id)):
            dep_text = f"{dep.group_id}:{dep.artifact_id}"
            if dep.version:
                dep_text += f" v{dep.version}"
            if dep.optional:
                dep_text += " [optional]"
            scope_branch.add(dep_text)

    console.print(tree)


def _show_dependencies_table(console: Console, deps: list) -> None:
    """Show dependencies in table format."""
    table = Table(title="Dependencies")
    table.add_column("Group ID", style="cyan")
    table.add_column("Artifact ID", style="magenta")
    table.add_column("Version", style="green")
    table.add_column("Scope", style="yellow")
    table.add_column("Type", style="blue")
    table.add_column("Optional", style="red")

    for dep in sorted(deps, key=lambda d: (d.group_id, d.artifact_id)):
        table.add_row(
            dep.group_id,
            dep.artifact_id,
            dep.version or "N/A",
            dep.scope,
            dep.type,
            "Yes" if dep.optional else "No",
        )

    console.print(table)


def _show_plugins_table(console: Console, plugins: list) -> None:
    """Show plugins in table format."""
    table = Table(title="Plugins")
    table.add_column("Group ID", style="cyan")
    table.add_column("Artifact ID", style="magenta")
    table.add_column("Version", style="green")
    table.add_column("Extensions", style="yellow")
    table.add_column("Inherited", style="blue")
    table.add_column("Config", style="red")

    for plugin in sorted(plugins, key=lambda p: (p.group_id, p.artifact_id)):
        table.add_row(
            plugin.group_id,
            plugin.artifact_id,
            plugin.version or "N/A",
            "Yes" if plugin.extensions else "No",
            "Yes" if plugin.inherited else "No",
            "Yes" if plugin.configuration else "No",
        )

    console.print(table)


def cli() -> None:
    """Entry point for the CLI."""
    main()  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    # This module is run directly, invoke the Click CLI
    cli()
