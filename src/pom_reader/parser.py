"""XML parser for POM files using lxml with full type safety."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lxml import etree

from .logging_config import (
    get_logger,
    log_error_with_context,
    log_function_call,
    log_parsing_result,
)
from .models import (
    Build,
    Dependency,
    Parent,
    Plugin,
    PomFile,
    Profile,
    Project,
    Property,
)


class PomParser:
    """Parser for Maven POM files with comprehensive error handling."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self.logger = get_logger(__name__)
        self.namespaces = {
            "m": "http://maven.apache.org/POM/4.0.0",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }
        self.logger.debug("PomParser initialized with Maven namespace")

    def parse_file(self, file_path: str | Path) -> PomFile:
        """Parse a POM file from the filesystem."""
        path = Path(file_path)
        log_function_call(self.logger, "parse_file", file_path=str(path))

        if not path.exists():
            self.logger.error("POM file not found: %s", path)
            raise FileNotFoundError(f"POM file not found: {path}")

        try:
            self.logger.info("Parsing POM file: %s", path)
            tree = etree.parse(str(path))
            root = tree.getroot()
            self.logger.debug("Successfully parsed XML, root element: %s", root.tag)
            return self._parse_element(root)
        except etree.XMLSyntaxError as e:
            log_error_with_context(self.logger, e, f"parsing XML from {path}")
            raise ValueError(f"Invalid XML in POM file {path}: {e}") from e

    def parse_string(self, xml_content: str) -> PomFile:
        """Parse a POM from XML string content."""
        log_function_call(self.logger, "parse_string", content_length=len(xml_content))

        try:
            self.logger.info("Parsing POM from string content")
            root = etree.fromstring(xml_content.encode("utf-8"))
            self.logger.debug(
                "Successfully parsed XML string, root element: %s", root.tag
            )
            return self._parse_element(root)
        except etree.XMLSyntaxError as e:
            log_error_with_context(self.logger, e, "parsing XML string content")
            raise ValueError(f"Invalid XML content: {e}") from e

    def _parse_element(self, root: etree.Element) -> PomFile:
        """Parse the root element of a POM file."""
        self.logger.debug("Starting POM element parsing")

        # Ensure we're dealing with a project element
        if root.tag != "project" and not root.tag.endswith("}project"):
            self.logger.error("Invalid root element: %s", root.tag)
            raise ValueError("Root element must be 'project'")

        # Parse project information
        self.logger.info("Parsing project information")
        project = self._parse_project(root)

        # Parse dependencies
        self.logger.info("Parsing dependencies")
        dependencies = self._parse_dependencies(root, "dependencies/dependency")
        log_parsing_result(self.logger, "dependency", len(dependencies))

        dependency_management = self._parse_dependencies(
            root, "dependencyManagement/dependencies/dependency"
        )
        log_parsing_result(
            self.logger, "dependency management", len(dependency_management)
        )

        # Parse properties
        self.logger.info("Parsing properties")
        properties = self._parse_properties(root)
        log_parsing_result(self.logger, "property", len(properties))

        # Parse build section
        self.logger.info("Parsing build configuration")
        build = self._parse_build(root)

        # Parse profiles
        self.logger.info("Parsing profiles")
        profiles = self._parse_profiles(root)
        log_parsing_result(self.logger, "profile", len(profiles))

        # Parse modules
        self.logger.info("Parsing modules")
        modules = self._parse_modules(root)
        log_parsing_result(self.logger, "module", len(modules))

        self.logger.info("POM parsing completed successfully")
        return PomFile(
            project=project,
            dependencies=dependencies,
            dependency_management=dependency_management,
            properties=properties,
            build=build,
            profiles=profiles,
            modules=modules,
        )

    def _parse_project(self, root: etree.Element) -> Project:
        """Parse the project section."""
        group_id = self._get_text(root, "groupId", required=True)
        artifact_id = self._get_text(root, "artifactId", required=True)
        version = self._get_text(root, "version", required=True)
        packaging = self._get_text(root, "packaging", default="jar")

        name = self._get_text(root, "name")
        description = self._get_text(root, "description")
        url = self._get_text(root, "url")
        inception_year = self._get_text(root, "inceptionYear")

        # Parse parent
        parent_elem = root.find("m:parent", self.namespaces)

        parent = None
        if parent_elem is not None:
            parent_group_id = self._get_text(parent_elem, "groupId", required=True)
            parent_artifact_id = self._get_text(
                parent_elem, "artifactId", required=True
            )
            parent_version = self._get_text(parent_elem, "version", required=True)
            parent_relative_path = self._get_text(parent_elem, "relativePath")

            if parent_group_id and parent_artifact_id and parent_version:
                parent = Parent(
                    group_id=parent_group_id,
                    artifact_id=parent_artifact_id,
                    version=parent_version,
                    relative_path=parent_relative_path,
                )

        # Parse organization
        org_elem = root.find("m:organization", self.namespaces)

        organization = None
        if org_elem is not None:
            org_name = self._get_text(org_elem, "name", default="") or ""
            org_url = self._get_text(org_elem, "url", default="") or ""
            organization = {
                "name": org_name,
                "url": org_url,
            }

        # Parse licenses
        licenses = []
        license_elems = root.findall("m:licenses/m:license", self.namespaces)

        for license_elem in license_elems:
            license_info = {
                "name": self._get_text(license_elem, "name", default="") or "",
                "url": self._get_text(license_elem, "url", default="") or "",
                "distribution": self._get_text(license_elem, "distribution", default="")
                or "",
                "comments": self._get_text(license_elem, "comments", default="") or "",
            }
            licenses.append(license_info)

        # Parse developers
        developers: list[dict[str, str]] = []
        dev_elems = root.findall("m:developers/m:developer", self.namespaces)

        for dev_elem in dev_elems:
            dev_info: dict[str, str] = {
                "id": self._get_text(dev_elem, "id", default="") or "",
                "name": self._get_text(dev_elem, "name", default="") or "",
                "email": self._get_text(dev_elem, "email", default="") or "",
                "url": self._get_text(dev_elem, "url", default="") or "",
                "organization": self._get_text(dev_elem, "organization", default="")
                or "",
                "organization_url": self._get_text(
                    dev_elem, "organizationUrl", default=""
                )
                or "",
                "roles": str(
                    ", ".join(
                        [
                            str(role.text or "")
                            for role in dev_elem.findall("roles/role")
                            if role.text
                        ]
                    )
                ),
                "timezone": self._get_text(dev_elem, "timezone", default="") or "",
                "properties": str(
                    self._parse_properties_dict(dev_elem.find("properties")) or {}
                ),
            }
            developers.append(dev_info)

        # Parse SCM
        scm_elem = root.find("m:scm", self.namespaces)

        scm = None
        if scm_elem is not None:
            scm = {
                "connection": self._get_text(scm_elem, "connection", default="") or "",
                "developer_connection": self._get_text(
                    scm_elem, "developerConnection", default=""
                )
                or "",
                "url": self._get_text(scm_elem, "url", default="") or "",
                "tag": self._get_text(scm_elem, "tag", default="") or "",
            }

        # Ensure required fields are not None
        if not group_id or not artifact_id or not version or not packaging:
            raise ValueError(
                "Required project fields (group_id, artifact_id, version, packaging) cannot be None"
            )

        return Project(
            group_id=group_id,
            artifact_id=artifact_id,
            version=version,
            packaging=packaging,
            name=name,
            description=description,
            url=url,
            inception_year=inception_year,
            organization=organization,
            licenses=licenses,
            developers=developers,
            scm=scm,
            parent=parent,
        )

    def _parse_dependencies(
        self,
        root: etree.Element,
        xpath: str,  # pylint: disable=unused-argument
    ) -> list[Dependency]:
        """Parse dependencies from the given xpath."""
        dependencies = []
        # Always use namespace for Maven POM elements
        dep_elems = root.findall("m:dependencies/m:dependency", self.namespaces)

        for dep_elem in dep_elems:
            if dep_elem is None:
                continue

            group_id = self._get_text(dep_elem, "groupId", required=True)
            artifact_id = self._get_text(dep_elem, "artifactId", required=True)

            # Skip if required fields are missing
            if not group_id or not artifact_id:
                continue

            version = self._get_text(dep_elem, "version")
            type_ = self._get_text(dep_elem, "type", default="jar") or "jar"
            classifier = self._get_text(dep_elem, "classifier")
            scope = self._get_text(dep_elem, "scope", default="compile") or "compile"
            optional_text = self._get_text(dep_elem, "optional", default="false")
            optional = bool(optional_text and optional_text.lower() == "true")

            # Parse exclusions
            exclusions = []
            for excl_elem in dep_elem.findall("exclusions/exclusion"):
                excl_group_id = self._get_text(excl_elem, "groupId", required=True)
                excl_artifact_id = self._get_text(
                    excl_elem, "artifactId", required=True
                )
                if excl_group_id and excl_artifact_id:
                    exclusion = Dependency(
                        group_id=excl_group_id,
                        artifact_id=excl_artifact_id,
                    )
                    exclusions.append(exclusion)

            dependency = Dependency(
                group_id=group_id,
                artifact_id=artifact_id,
                version=version,
                type=type_,
                classifier=classifier,
                scope=scope,
                optional=optional,
                exclusions=exclusions,
            )
            dependencies.append(dependency)

        return dependencies

    def _parse_properties(self, root: etree.Element) -> list[Property]:
        """Parse properties from the POM."""
        properties = []
        # Always use namespace for Maven POM elements
        props_elem = root.find("m:properties", self.namespaces)

        if props_elem is not None:
            for child in props_elem:
                if child.text is not None:
                    # Remove namespace from tag name
                    tag_name = (
                        str(child.tag).rsplit("}", maxsplit=1)[-1]
                        if "}" in str(child.tag)
                        else str(child.tag)
                    )
                    properties.append(Property(name=tag_name, value=child.text.strip()))
        return properties

    def _parse_build(self, root: etree.Element) -> Build | None:
        """Parse the build section."""
        # Always use namespace for Maven POM elements
        build_elem = root.find("m:build", self.namespaces)

        if build_elem is None:
            return None

        source_directory = self._get_text(build_elem, "sourceDirectory")
        test_source_directory = self._get_text(build_elem, "testSourceDirectory")
        output_directory = self._get_text(build_elem, "outputDirectory")
        test_output_directory = self._get_text(build_elem, "testOutputDirectory")
        final_name = self._get_text(build_elem, "finalName")
        directory = self._get_text(build_elem, "directory")

        # Parse filters
        filters = []
        for filter_elem in build_elem.findall("filters/filter"):
            if filter_elem.text:
                filters.append(filter_elem.text.strip())

        # Parse resources
        resources = self._parse_resources(build_elem, "resources/resource")
        test_resources = self._parse_resources(build_elem, "testResources/testResource")

        # Parse plugins
        plugins = self._parse_plugins(build_elem, "plugins/plugin")

        return Build(
            source_directory=source_directory,
            test_source_directory=test_source_directory,
            output_directory=output_directory,
            test_output_directory=test_output_directory,
            final_name=final_name,
            directory=directory,
            filters=filters,
            resources=resources,
            test_resources=test_resources,
            plugins=plugins,
        )

    def _parse_plugins(
        self,
        root: etree.Element,
        xpath: str,  # pylint: disable=unused-argument
    ) -> list[Plugin]:
        """Parse plugins from the given xpath."""
        plugins = []
        # Always use namespace for Maven POM elements
        plugin_elems = root.findall("m:plugins/m:plugin", self.namespaces)

        for plugin_elem in plugin_elems:
            if plugin_elem is None:
                continue

            group_id = (
                self._get_text(
                    plugin_elem, "groupId", default="org.apache.maven.plugins"
                )
                or "org.apache.maven.plugins"
            )
            artifact_id = self._get_text(plugin_elem, "artifactId", required=True)

            # Skip if required fields are missing
            if not artifact_id:
                continue

            version = self._get_text(plugin_elem, "version")
            extensions_text = self._get_text(plugin_elem, "extensions", default="false")
            extensions = bool(extensions_text and extensions_text.lower() == "true")
            inherited_text = self._get_text(plugin_elem, "inherited", default="true")
            inherited = bool(inherited_text and inherited_text.lower() == "true")

            # Parse configuration
            config_elem = plugin_elem.find("m:configuration", self.namespaces)
            configuration = (
                self._parse_configuration(config_elem)
                if config_elem is not None
                else {}
            )

            # Parse executions
            executions = []
            for exec_elem in plugin_elem.findall("executions/execution"):
                execution = {
                    "id": self._get_text(exec_elem, "id"),
                    "phase": self._get_text(exec_elem, "phase"),
                    "goals": [
                        goal.text
                        for goal in exec_elem.findall("goals/goal")
                        if goal.text
                    ],
                    "configuration": self._parse_configuration(
                        exec_elem.find("configuration")
                    ),
                }
                executions.append(execution)

            plugin = Plugin(
                group_id=group_id,
                artifact_id=artifact_id,
                version=version,
                extensions=extensions,
                inherited=inherited,
                configuration=configuration,
                executions=executions,
            )
            plugins.append(plugin)

        return plugins

    def _parse_profiles(self, root: etree.Element) -> list[Profile]:
        """Parse profiles from the POM."""
        profiles = []
        # Always use namespace for Maven POM elements
        profile_elems = root.findall("m:profiles/m:profile", self.namespaces)

        for profile_elem in profile_elems:
            if profile_elem is None:
                continue

            profile_id = self._get_text(profile_elem, "id", required=True)

            # Skip if required fields are missing
            if not profile_id:
                continue

            # Parse activation
            activation_elem = profile_elem.find("activation")
            activation = None
            if activation_elem is not None:
                active_by_default_text = self._get_text(
                    activation_elem, "activeByDefault", default="false"
                )
                activation = {
                    "active_by_default": bool(
                        active_by_default_text
                        and active_by_default_text.lower() == "true"
                    ),
                    "jdk": self._get_text(activation_elem, "jdk"),
                    "os": self._parse_activation_os(activation_elem.find("os")),
                    "property": self._parse_activation_property(
                        activation_elem.find("property")
                    ),
                    "file": self._parse_activation_file(activation_elem.find("file")),
                }

            # Parse profile-specific elements
            properties = self._parse_properties(profile_elem)
            dependencies = self._parse_dependencies(
                profile_elem, "dependencies/dependency"
            )
            plugins = self._parse_plugins(profile_elem, "build/plugins/plugin")

            # Parse profile build
            build_elem = profile_elem.find("build")
            build = None
            if build_elem is not None:
                build = Build(
                    source_directory=self._get_text(build_elem, "sourceDirectory"),
                    test_source_directory=self._get_text(
                        build_elem, "testSourceDirectory"
                    ),
                    output_directory=self._get_text(build_elem, "outputDirectory"),
                    test_output_directory=self._get_text(
                        build_elem, "testOutputDirectory"
                    ),
                    final_name=self._get_text(build_elem, "finalName"),
                    directory=self._get_text(build_elem, "directory"),
                    filters=[
                        f.text or ""
                        for f in build_elem.findall("filters/filter")
                        if f.text
                    ],
                    resources=self._parse_resources(build_elem, "resources/resource"),
                    test_resources=self._parse_resources(
                        build_elem, "testResources/testResource"
                    ),
                    plugins=plugins,
                )

            profile = Profile(
                id=profile_id,
                activation=activation,
                properties=properties,
                dependencies=dependencies,
                plugins=plugins,
                build=build,
            )
            profiles.append(profile)

        return profiles

    def _parse_modules(self, root: etree.Element) -> list[str]:
        """Parse modules from the POM."""
        modules = []
        # Always use namespace for Maven POM elements
        module_elems = root.findall("m:modules/m:module", self.namespaces)

        for module_elem in module_elems:
            if module_elem.text:
                modules.append(module_elem.text.strip())
        return modules

    def _parse_resources(self, root: etree.Element, xpath: str) -> list[dict[str, Any]]:
        """Parse resources from the given xpath."""
        resources = []
        # Always use namespace for Maven POM elements
        # Convert xpath to handle namespace properly
        ns_xpath = xpath.replace("resources/resource", "m:resources/m:resource")
        resource_elems = root.findall(ns_xpath, self.namespaces)
        if not resource_elems:
            resource_elems = root.findall(xpath)

        for resource_elem in resource_elems:
            if resource_elem is None:
                continue

            resource = {
                "target_path": self._get_text(resource_elem, "targetPath"),
                "filtering": bool(
                    (
                        filtering_text := self._get_text(
                            resource_elem, "filtering", default="false"
                        )
                    )
                    and filtering_text.lower() == "true"
                ),
                "directory": self._get_text(resource_elem, "directory"),
                "includes": [
                    inc.text
                    for inc in resource_elem.findall("includes/include")
                    if inc.text
                ],
                "excludes": [
                    exc.text
                    for exc in resource_elem.findall("excludes/exclude")
                    if exc.text
                ],
            }
            resources.append(resource)
        return resources

    def _parse_configuration(self, config_elem: etree.Element | None) -> dict[str, Any]:
        """Parse plugin configuration into a dictionary."""
        if config_elem is None:
            return {}

        config = {}
        for child in config_elem:
            # Remove namespace from tag name
            tag_name = (
                str(child.tag).rsplit("}", maxsplit=1)[-1]
                if "}" in str(child.tag)
                else str(child.tag)
            )

            if child.text is not None:
                config[tag_name] = child.text.strip()
            elif len(child) > 0:
                # Handle nested configuration
                config[tag_name] = self._parse_configuration(child)
            else:
                config[tag_name] = None

        return config

    def _parse_activation_os(
        self, os_elem: etree.Element | None
    ) -> dict[str, str] | None:
        """Parse OS activation criteria."""
        if os_elem is None:
            return None

        return {
            "name": self._get_text(os_elem, "name") or "",
            "family": self._get_text(os_elem, "family") or "",
            "arch": self._get_text(os_elem, "arch") or "",
            "version": self._get_text(os_elem, "version") or "",
        }

    def _parse_activation_property(
        self, prop_elem: etree.Element | None
    ) -> dict[str, str] | None:
        """Parse property activation criteria."""
        if prop_elem is None:
            return None

        return {
            "name": self._get_text(prop_elem, "name") or "",
            "value": self._get_text(prop_elem, "value") or "",
        }

    def _parse_activation_file(
        self, file_elem: etree.Element | None
    ) -> dict[str, str] | None:
        """Parse file activation criteria."""
        if file_elem is None:
            return None

        return {
            "missing": self._get_text(file_elem, "missing") or "",
            "exists": self._get_text(file_elem, "exists") or "",
        }

    def _parse_properties_dict(
        self, props_elem: etree.Element | None
    ) -> dict[str, str]:
        """Parse properties into a dictionary."""
        if props_elem is None:
            return {}

        props: dict[str, str] = {}
        for child in props_elem:
            if child.text is not None:
                props[str(child.tag)] = str(child.text.strip())
        return props

    def _get_text(
        self,
        element: etree.Element,
        xpath: str,
        default: str | None = None,
        required: bool = False,
    ) -> str:
        """Get text content from an element with error handling."""
        # Always use namespace for Maven POM elements
        found = element.find(f"m:{xpath}", self.namespaces)

        if found is not None:
            if found.text is not None:
                return str(found.text.strip())
            # Element exists but has no text content (like <relativePath/>)
            return ""

        if required:
            raise ValueError(f"Required element '{xpath}' not found in {element.tag}")

        return str(default) if default is not None else ""
