"""Tests for POM data models."""

import pytest

from pom_reader.models import Dependency, Plugin, PomFile, Project, Property


class TestProperty:
    """Test Property model."""

    def test_property_creation(self) -> None:
        """Test creating a property."""
        prop = Property(name="java.version", value="11")
        assert prop.name == "java.version"
        assert prop.value == "11"

    def test_property_immutable(self) -> None:
        """Test that Property is immutable."""
        prop = Property(name="test", value="value")
        with pytest.raises(AttributeError):
            prop.name = "new_name"  # type: ignore


class TestDependency:
    """Test Dependency model."""

    def test_dependency_creation(self) -> None:
        """Test creating a dependency."""
        dep = Dependency(
            group_id="org.springframework", artifact_id="spring-core", version="5.3.0"
        )
        assert dep.group_id == "org.springframework"
        assert dep.artifact_id == "spring-core"
        assert dep.version == "5.3.0"
        assert dep.type == "jar"  # default
        assert dep.scope == "compile"  # default
        assert dep.optional is False  # default

    def test_dependency_with_all_fields(self) -> None:
        """Test creating a dependency with all fields."""
        exclusion = Dependency(group_id="org.example", artifact_id="excluded")
        dep = Dependency(
            group_id="org.springframework",
            artifact_id="spring-core",
            version="5.3.0",
            type="jar",
            classifier="sources",
            scope="test",
            optional=True,
            exclusions=[exclusion],
        )
        assert dep.classifier == "sources"
        assert dep.scope == "test"
        assert dep.optional is True
        assert len(dep.exclusions) == 1
        assert dep.exclusions[0].group_id == "org.example"


class TestPlugin:
    """Test Plugin model."""

    def test_plugin_creation(self) -> None:
        """Test creating a plugin."""
        plugin = Plugin(
            group_id="org.apache.maven.plugins",
            artifact_id="maven-compiler-plugin",
            version="3.8.1",
        )
        assert plugin.group_id == "org.apache.maven.plugins"
        assert plugin.artifact_id == "maven-compiler-plugin"
        assert plugin.version == "3.8.1"
        assert plugin.extensions is False  # default
        assert plugin.inherited is True  # default


class TestProject:
    """Test Project model."""

    def test_project_creation(self) -> None:
        """Test creating a project."""
        project = Project(group_id="com.example", artifact_id="my-app", version="1.0.0")
        assert project.group_id == "com.example"
        assert project.artifact_id == "my-app"
        assert project.version == "1.0.0"
        assert project.packaging == "jar"  # default


class TestPomFile:
    """Test PomFile model."""

    def test_pom_file_creation(self) -> None:
        """Test creating a POM file."""
        project = Project(group_id="com.example", artifact_id="my-app", version="1.0.0")
        pom = PomFile(project=project)
        assert pom.project == project
        assert len(pom.dependencies) == 0
        assert len(pom.properties) == 0

    def test_effective_dependencies(self) -> None:
        """Test effective dependencies include profile dependencies."""
        project = Project(group_id="com.example", artifact_id="my-app", version="1.0.0")

        main_dep = Dependency(
            group_id="org.springframework", artifact_id="spring-core", version="5.3.0"
        )

        profile_dep = Dependency(
            group_id="org.junit", artifact_id="junit", version="5.7.0"
        )

        from pom_reader.models import Profile

        profile = Profile(id="test", dependencies=[profile_dep])

        pom = PomFile(project=project, dependencies=[main_dep], profiles=[profile])

        effective_deps = pom.effective_dependencies
        assert len(effective_deps) == 2
        assert main_dep in effective_deps
        assert profile_dep in effective_deps

    def test_get_dependency_by_coordinates(self) -> None:
        """Test finding dependency by coordinates."""
        project = Project(group_id="com.example", artifact_id="my-app", version="1.0.0")

        dep1 = Dependency(
            group_id="org.springframework",
            artifact_id="spring-core",
            version="5.3.0",
            scope="compile",
        )

        dep2 = Dependency(
            group_id="org.springframework",
            artifact_id="spring-core",
            version="5.3.0",
            scope="test",
        )

        pom = PomFile(project=project, dependencies=[dep1, dep2])

        # Find without scope
        found = pom.get_dependency_by_coordinates("org.springframework", "spring-core")
        assert found is not None
        assert found.scope == "compile"  # Should return first match

        # Find with specific scope
        found = pom.get_dependency_by_coordinates(
            "org.springframework", "spring-core", "test"
        )
        assert found is not None
        assert found.scope == "test"

        # Find non-existent
        found = pom.get_dependency_by_coordinates("org.nonexistent", "nonexistent")
        assert found is None

    def test_get_property(self) -> None:
        """Test getting property by name."""
        project = Project(group_id="com.example", artifact_id="my-app", version="1.0.0")

        prop1 = Property(name="java.version", value="11")
        prop2 = Property(name="maven.compiler.source", value="11")

        pom = PomFile(project=project, properties=[prop1, prop2])

        assert pom.get_property("java.version") == "11"
        assert pom.get_property("maven.compiler.source") == "11"
        assert pom.get_property("nonexistent") is None
