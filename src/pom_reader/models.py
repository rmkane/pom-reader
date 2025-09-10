"""Data models for POM file representation with full type safety."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Property:
    """Represents a Maven property."""

    name: str
    value: str


@dataclass(frozen=True)
class Parent:
    """Represents a parent POM reference."""

    group_id: str
    artifact_id: str
    version: str
    relative_path: str | None = None


@dataclass(frozen=True)
class Dependency:
    """Represents a Maven dependency."""

    group_id: str
    artifact_id: str
    version: str | None = None
    type: str = "jar"
    classifier: str | None = None
    scope: str = "compile"
    optional: bool = False
    exclusions: list[Dependency] = field(default_factory=list)


@dataclass(frozen=True)
class Plugin:
    """Represents a Maven plugin."""

    group_id: str
    artifact_id: str
    version: str | None = None
    extensions: bool = False
    inherited: bool = True
    configuration: dict[str, Any] = field(default_factory=dict)
    executions: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class Build:
    """Represents the build section of a POM."""

    source_directory: str | None = None
    test_source_directory: str | None = None
    output_directory: str | None = None
    test_output_directory: str | None = None
    final_name: str | None = None
    directory: str | None = None
    filters: list[str] = field(default_factory=list)
    resources: list[dict[str, Any]] = field(default_factory=list)
    test_resources: list[dict[str, Any]] = field(default_factory=list)
    plugins: list[Plugin] = field(default_factory=list)
    plugin_management: dict[str, Any] | None = None


@dataclass(frozen=True)
class Profile:
    """Represents a Maven profile."""

    id: str
    activation: dict[str, Any] | None = None
    properties: list[Property] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    plugins: list[Plugin] = field(default_factory=list)
    build: Build | None = None


@dataclass(frozen=True)
class Project:
    """Represents the main project information in a POM."""

    group_id: str
    artifact_id: str
    version: str
    packaging: str = "jar"
    name: str | None = None
    description: str | None = None
    url: str | None = None
    inception_year: str | None = None
    organization: dict[str, str] | None = None
    licenses: list[dict[str, str]] = field(default_factory=list)
    developers: list[dict[str, str]] = field(default_factory=list)
    contributors: list[dict[str, str]] = field(default_factory=list)
    mailing_lists: list[dict[str, str]] = field(default_factory=list)
    scm: dict[str, str] | None = None
    issue_management: dict[str, str] | None = None
    ci_management: dict[str, str] | None = None
    distribution_management: dict[str, Any] | None = None
    parent: Parent | None = None


@dataclass(frozen=True)
class PomFile:
    """Complete representation of a POM file."""

    project: Project
    dependencies: list[Dependency] = field(default_factory=list)
    dependency_management: list[Dependency] = field(default_factory=list)
    properties: list[Property] = field(default_factory=list)
    build: Build | None = None
    profiles: list[Profile] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)

    @property
    def effective_dependencies(self) -> list[Dependency]:
        """Get all dependencies including those from profiles."""
        deps = list(self.dependencies)
        for profile in self.profiles:
            deps.extend(profile.dependencies)
        return deps

    @property
    def effective_plugins(self) -> list[Plugin]:
        """Get all plugins including those from build and profiles."""
        plugins = []
        if self.build:
            plugins.extend(self.build.plugins)
        for profile in self.profiles:
            plugins.extend(profile.plugins)
        return plugins

    def get_dependency_by_coordinates(
        self, group_id: str, artifact_id: str, scope: str | None = None
    ) -> Dependency | None:
        """Find a dependency by its coordinates."""
        for dep in self.effective_dependencies:
            if dep.group_id == group_id and dep.artifact_id == artifact_id:
                if scope is None or dep.scope == scope:
                    return dep
        return None

    def get_plugin_by_coordinates(
        self, group_id: str, artifact_id: str
    ) -> Plugin | None:
        """Find a plugin by its coordinates."""
        for plugin in self.effective_plugins:
            if plugin.group_id == group_id and plugin.artifact_id == artifact_id:
                return plugin
        return None

    def get_property(self, name: str) -> str | None:
        """Get a property value by name."""
        for prop in self.properties:
            if prop.name == name:
                return prop.value
        return None
