"""Tests for POM parser."""

from pathlib import Path

import pytest

from pom_reader.parser import PomParser


class TestPomParser:
    """Test POM parser functionality."""

    def test_parse_simple_pom(self) -> None:
        """Test parsing a simple POM file."""
        simple_pom = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-app</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
</project>"""

        parser = PomParser()
        pom = parser.parse_string(simple_pom)

        assert pom.project.group_id == "com.example"
        assert pom.project.artifact_id == "test-app"
        assert pom.project.version == "1.0.0"
        assert pom.project.packaging == "jar"

    def test_parse_pom_with_dependencies(self) -> None:
        """Test parsing a POM with dependencies."""
        pom_with_deps = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-app</artifactId>
    <version>1.0.0</version>

    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-core</artifactId>
            <version>5.3.0</version>
        </dependency>
        <dependency>
            <groupId>org.junit</groupId>
            <artifactId>junit</artifactId>
            <version>5.7.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>"""

        parser = PomParser()
        pom = parser.parse_string(pom_with_deps)

        assert len(pom.dependencies) == 2

        spring_dep = pom.dependencies[0]
        assert spring_dep.group_id == "org.springframework"
        assert spring_dep.artifact_id == "spring-core"
        assert spring_dep.version == "5.3.0"
        assert spring_dep.scope == "compile"  # default

        junit_dep = pom.dependencies[1]
        assert junit_dep.group_id == "org.junit"
        assert junit_dep.artifact_id == "junit"
        assert junit_dep.version == "5.7.0"
        assert junit_dep.scope == "test"

    def test_parse_pom_with_properties(self) -> None:
        """Test parsing a POM with properties."""
        pom_with_props = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-app</artifactId>
    <version>1.0.0</version>

    <properties>
        <java.version>11</java.version>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
</project>"""

        parser = PomParser()
        pom = parser.parse_string(pom_with_props)

        assert len(pom.properties) == 3

        java_version = next(
            (p for p in pom.properties if p.name == "java.version"), None
        )
        assert java_version is not None
        assert java_version.value == "11"

        compiler_source = next(
            (p for p in pom.properties if p.name == "maven.compiler.source"), None
        )
        assert compiler_source is not None
        assert compiler_source.value == "11"

    def test_parse_pom_with_plugins(self) -> None:
        """Test parsing a POM with plugins."""
        pom_with_plugins = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-app</artifactId>
    <version>1.0.0</version>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.8.1</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>"""

        parser = PomParser()
        pom = parser.parse_string(pom_with_plugins)

        assert pom.build is not None
        assert len(pom.build.plugins) == 1

        plugin = pom.build.plugins[0]
        assert plugin.group_id == "org.apache.maven.plugins"
        assert plugin.artifact_id == "maven-compiler-plugin"
        assert plugin.version == "3.8.1"
        assert plugin.configuration["source"] == "11"
        assert plugin.configuration["target"] == "11"

    def test_parse_pom_with_parent(self) -> None:
        """Test parsing a POM with parent."""
        pom_with_parent = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.5.0</version>
        <relativePath/>
    </parent>
    <groupId>com.example</groupId>
    <artifactId>test-app</artifactId>
    <version>1.0.0</version>
</project>"""

        parser = PomParser()
        pom = parser.parse_string(pom_with_parent)

        assert pom.project.parent is not None
        assert pom.project.parent.group_id == "org.springframework.boot"
        assert pom.project.parent.artifact_id == "spring-boot-starter-parent"
        assert pom.project.parent.version == "2.5.0"
        assert pom.project.parent.relative_path == ""

    def test_parse_invalid_xml(self) -> None:
        """Test parsing invalid XML raises error."""
        parser = PomParser()

        with pytest.raises(ValueError, match="Invalid XML"):
            parser.parse_string("invalid xml content")

    def test_parse_missing_required_fields(self) -> None:
        """Test parsing POM with missing required fields raises error."""
        parser = PomParser()

        incomplete_pom = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <!-- Missing artifactId and version -->
</project>"""

        with pytest.raises(ValueError, match="Required element"):
            parser.parse_string(incomplete_pom)

    def test_parse_file_not_found(self) -> None:
        """Test parsing non-existent file raises error."""
        parser = PomParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent.xml")

    def test_parse_existing_pom_file(self) -> None:
        """Test parsing the actual POM file in the project."""
        parser = PomParser()
        pom_file = Path(__file__).parent.parent / "resources" / "pom.xml"

        if pom_file.exists():
            pom = parser.parse_file(pom_file)
            assert pom.project.group_id == "org.example.spring"
            assert pom.project.artifact_id == "elasticsearch"
            assert pom.project.version == "0.1.0-SNAPSHOT"
            assert len(pom.dependencies) > 0
