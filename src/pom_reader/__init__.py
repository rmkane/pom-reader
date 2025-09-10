"""POM Reader - A modern Python library for parsing and analyzing Maven POM files."""

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
from .reader import PomReader

__version__ = "0.1.0"
__all__ = [
    "PomReader",
    "PomFile",
    "Project",
    "Dependency",
    "Plugin",
    "Parent",
    "Property",
    "Build",
    "Profile",
]
