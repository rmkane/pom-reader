"""Main POM reader class with analysis capabilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import Dependency, PomFile
from .parser import PomParser


class PomReader:
    """Main class for reading and analyzing POM files."""

    def __init__(self) -> None:
        """Initialize the POM reader."""
        self.parser = PomParser()

    def parse_file(self, file_path: str | Path) -> PomFile:
        """Parse a POM file from the filesystem."""
        return self.parser.parse_file(file_path)

    def parse_string(self, xml_content: str) -> PomFile:
        """Parse a POM from XML string content."""
        return self.parser.parse_string(xml_content)


class PomAnalyzer:
    """Analyzer for POM files with various analysis capabilities."""

    def __init__(self, pom: PomFile) -> None:
        """Initialize the analyzer with a POM file."""
        self.pom = pom

    def get_dependency_summary(self) -> dict[str, Any]:
        """Get a summary of all dependencies."""
        deps = self.pom.effective_dependencies

        summary: dict[str, Any] = {
            "total_dependencies": len(deps),
            "by_scope": {},
            "by_group": {},
            "optional_dependencies": 0,
            "dependencies_with_version": 0,
            "dependencies_without_version": 0,
        }

        for dep in deps:
            # Count by scope
            scope = dep.scope
            summary["by_scope"][scope] = summary["by_scope"].get(scope, 0) + 1

            # Count by group
            group = dep.group_id
            summary["by_group"][group] = summary["by_group"].get(group, 0) + 1

            # Count optional
            if dep.optional:
                summary["optional_dependencies"] += 1

            # Count version status
            if dep.version:
                summary["dependencies_with_version"] += 1
            else:
                summary["dependencies_without_version"] += 1

        return summary

    def get_plugin_summary(self) -> dict[str, Any]:
        """Get a summary of all plugins."""
        plugins = self.pom.effective_plugins

        summary: dict[str, Any] = {
            "total_plugins": len(plugins),
            "by_group": {},
            "plugins_with_version": 0,
            "plugins_without_version": 0,
            "plugins_with_configuration": 0,
            "plugins_with_executions": 0,
        }

        for plugin in plugins:
            # Count by group
            group = plugin.group_id
            summary["by_group"][group] = summary["by_group"].get(group, 0) + 1

            # Count version status
            if plugin.version:
                summary["plugins_with_version"] += 1
            else:
                summary["plugins_without_version"] += 1

            # Count configuration
            if plugin.configuration:
                summary["plugins_with_configuration"] += 1

            # Count executions
            if plugin.executions:
                summary["plugins_with_executions"] += 1

        return summary

    def find_dependency_conflicts(self) -> list[dict[str, Any]]:
        """Find potential dependency conflicts."""
        conflicts = []
        deps = self.pom.effective_dependencies

        # Group dependencies by coordinates (group:artifact)
        dep_groups: dict[str, list[Dependency]] = {}
        for dep in deps:
            key = f"{dep.group_id}:{dep.artifact_id}"
            if key not in dep_groups:
                dep_groups[key] = []
            dep_groups[key].append(dep)

        # Find groups with multiple versions
        for key, group_deps in dep_groups.items():
            versions = {dep.version for dep in group_deps if dep.version}
            if len(versions) > 1:
                conflicts.append(
                    {
                        "coordinates": key,
                        "versions": list(versions),
                        "dependencies": group_deps,
                    }
                )

        return conflicts

    def get_spring_boot_info(self) -> dict[str, Any] | None:
        """Get Spring Boot specific information if this is a Spring Boot project."""
        spring_boot_deps = [
            dep
            for dep in self.pom.effective_dependencies
            if dep.group_id == "org.springframework.boot"
        ]

        if not spring_boot_deps:
            return None

        spring_boot_plugin = self.pom.get_plugin_by_coordinates(
            "org.springframework.boot", "spring-boot-maven-plugin"
        )

        return {
            "is_spring_boot_project": True,
            "spring_boot_dependencies": len(spring_boot_deps),
            "has_spring_boot_plugin": spring_boot_plugin is not None,
            "spring_boot_dependencies_list": [
                {
                    "artifact_id": dep.artifact_id,
                    "version": dep.version,
                    "scope": dep.scope,
                }
                for dep in spring_boot_deps
            ],
        }

    def get_java_version_info(self) -> dict[str, str] | None:
        """Get Java version information from properties and plugins."""
        java_version = self.pom.get_property("java.version")
        maven_compiler_source = self.pom.get_property("maven.compiler.source")
        maven_compiler_target = self.pom.get_property("maven.compiler.target")

        # Check maven-compiler-plugin configuration
        compiler_plugin = self.pom.get_plugin_by_coordinates(
            "org.apache.maven.plugins", "maven-compiler-plugin"
        )

        compiler_source = None
        compiler_target = None
        if compiler_plugin and compiler_plugin.configuration:
            compiler_source = compiler_plugin.configuration.get("source")
            compiler_target = compiler_plugin.configuration.get("target")

        return {
            "java_version_property": java_version or "",
            "maven_compiler_source_property": maven_compiler_source or "",
            "maven_compiler_target_property": maven_compiler_target or "",
            "compiler_plugin_source": compiler_source or "",
            "compiler_plugin_target": compiler_target or "",
        }

    def get_security_info(self) -> dict[str, Any]:
        """Get security-related information from the POM."""
        security_deps = []
        security_plugins = []

        # Look for common security dependencies
        security_keywords = [
            "security",
            "auth",
            "jwt",
            "oauth",
            "spring-security",
            "shiro",
        ]
        for dep in self.pom.effective_dependencies:
            for keyword in security_keywords:
                if (
                    keyword.lower() in dep.artifact_id.lower()
                    or keyword.lower() in dep.group_id.lower()
                ):
                    security_deps.append(dep)
                    break

        # Look for security plugins
        security_plugin_keywords = ["security", "owasp", "spotbugs", "findbugs"]
        for plugin in self.pom.effective_plugins:
            for keyword in security_plugin_keywords:
                if keyword.lower() in plugin.artifact_id.lower():
                    security_plugins.append(plugin)
                    break

        return {
            "security_dependencies": len(security_deps),
            "security_plugins": len(security_plugins),
            "security_dependencies_list": [
                {
                    "group_id": dep.group_id,
                    "artifact_id": dep.artifact_id,
                    "version": dep.version,
                    "scope": dep.scope,
                }
                for dep in security_deps
            ],
            "security_plugins_list": [
                {
                    "group_id": plugin.group_id,
                    "artifact_id": plugin.artifact_id,
                    "version": plugin.version,
                }
                for plugin in security_plugins
            ],
        }

    def get_build_info(self) -> dict[str, Any]:
        """Get build-related information."""
        if not self.pom.build:
            return {"has_build_section": False}

        build = self.pom.build
        return {
            "has_build_section": True,
            "source_directory": build.source_directory,
            "test_source_directory": build.test_source_directory,
            "output_directory": build.output_directory,
            "test_output_directory": build.test_output_directory,
            "final_name": build.final_name,
            "directory": build.directory,
            "filters_count": len(build.filters),
            "resources_count": len(build.resources),
            "test_resources_count": len(build.test_resources),
            "plugins_count": len(build.plugins),
        }

    def get_comprehensive_analysis(self) -> dict[str, Any]:
        """Get a comprehensive analysis of the POM file."""
        return {
            "project_info": {
                "group_id": self.pom.project.group_id,
                "artifact_id": self.pom.project.artifact_id,
                "version": self.pom.project.version,
                "packaging": self.pom.project.packaging,
                "name": self.pom.project.name,
                "description": self.pom.project.description,
                "url": self.pom.project.url,
                "has_parent": self.pom.project.parent is not None,
            },
            "dependency_analysis": self.get_dependency_summary(),
            "plugin_analysis": self.get_plugin_summary(),
            "dependency_conflicts": self.find_dependency_conflicts(),
            "spring_boot_info": self.get_spring_boot_info(),
            "java_version_info": self.get_java_version_info(),
            "security_info": self.get_security_info(),
            "build_info": self.get_build_info(),
            "profiles_count": len(self.pom.profiles),
            "modules_count": len(self.pom.modules),
            "properties_count": len(self.pom.properties),
        }
