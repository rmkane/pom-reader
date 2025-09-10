#!/usr/bin/env python3
"""Example usage of POM Reader."""

from pathlib import Path

from pom_reader.logging_config import setup_logging
from pom_reader.reader import PomAnalyzer, PomReader


def main() -> None:
    """Demonstrate POM Reader usage."""
    # Initialize logging
    logger = setup_logging(level="INFO")
    logger.info("Starting POM Reader example")

    # Initialize the reader
    reader = PomReader()

    # Parse the example POM file
    pom_file = Path("resources/pom.xml")
    if not pom_file.exists():
        logger.error(f"POM file not found: {pom_file}")
        print(f"POM file not found: {pom_file}")
        return

    logger.info(f"Parsing POM file: {pom_file}")
    print("Parsing POM file...")
    pom = reader.parse_file(pom_file)

    # Basic project information
    print(f"\nProject Information:")
    print(f"  Group ID: {pom.project.group_id}")
    print(f"  Artifact ID: {pom.project.artifact_id}")
    print(f"  Version: {pom.project.version}")
    print(f"  Packaging: {pom.project.packaging}")
    print(f"  Name: {pom.project.name}")
    print(f"  Description: {pom.project.description}")

    # Dependencies
    print(f"\nDependencies ({len(pom.dependencies)}):")
    for dep in pom.dependencies:
        version_str = f" v{dep.version}" if dep.version else ""
        scope_str = f" [{dep.scope}]" if dep.scope != "compile" else ""
        optional_str = " (optional)" if dep.optional else ""
        print(
            f"  {dep.group_id}:{dep.artifact_id}{version_str}{scope_str}{optional_str}"
        )

    # Plugins
    if pom.build and pom.build.plugins:
        print(f"\nPlugins ({len(pom.build.plugins)}):")
        for plugin in pom.build.plugins:
            version_str = f" v{plugin.version}" if plugin.version else ""
            print(f"  {plugin.group_id}:{plugin.artifact_id}{version_str}")

    # Properties
    if pom.properties:
        print(f"\nProperties ({len(pom.properties)}):")
        for prop in pom.properties[:5]:  # Show first 5 properties
            print(f"  {prop.name} = {prop.value}")
        if len(pom.properties) > 5:
            print(f"  ... and {len(pom.properties) - 5} more")

    # Analysis
    print(f"\nAnalysis:")
    analyzer = PomAnalyzer(pom)

    # Dependency summary
    dep_summary = analyzer.get_dependency_summary()
    print(f"  Total dependencies: {dep_summary['total_dependencies']}")
    print(f"  Optional dependencies: {dep_summary['optional_dependencies']}")
    print(f"  Dependencies by scope: {dep_summary['by_scope']}")

    # Spring Boot info
    spring_boot_info = analyzer.get_spring_boot_info()
    if spring_boot_info:
        print(f"  Spring Boot project: Yes")
        print(
            f"  Spring Boot dependencies: {spring_boot_info['spring_boot_dependencies']}"
        )
        print(f"  Has Spring Boot plugin: {spring_boot_info['has_spring_boot_plugin']}")
    else:
        print(f"  Spring Boot project: No")

    # Java version info
    java_info = analyzer.get_java_version_info()
    if java_info and any(java_info.values()):
        print(f"  Java version: {java_info.get('java_version_property', 'N/A')}")
        print(
            f"  Compiler source: {java_info.get('maven_compiler_source_property', 'N/A')}"
        )
        print(
            f"  Compiler target: {java_info.get('maven_compiler_target_property', 'N/A')}"
        )

    # Dependency conflicts
    conflicts = analyzer.find_dependency_conflicts()
    if conflicts:
        print(f"  Dependency conflicts: {len(conflicts)}")
        for conflict in conflicts:
            print(f"    {conflict['coordinates']}: {', '.join(conflict['versions'])}")
    else:
        print(f"  Dependency conflicts: None")

    # Comprehensive analysis
    print(f"\nComprehensive Analysis:")
    analysis = analyzer.get_comprehensive_analysis()
    print(f"  Total plugins: {analysis['plugin_analysis']['total_plugins']}")
    print(f"  Profiles: {analysis['profiles_count']}")
    print(f"  Modules: {analysis['modules_count']}")
    print(f"  Properties: {analysis['properties_count']}")


if __name__ == "__main__":
    main()
