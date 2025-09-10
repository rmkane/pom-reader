<!-- omit in toc -->
# POM Reader

A modern Python library for parsing and analyzing Maven POM (Project Object Model) files with full type safety and comprehensive analysis capabilities.

<!-- omit in toc -->
## Table of contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [First Time Setup](#first-time-setup)
  - [Common Commands](#common-commands)
  - [Environment Management](#environment-management)
- [Installation](#installation)
- [Command Line Usage](#command-line-usage)
  - [Python API](#python-api)
- [Development](#development)
  - [Quick Start with Virtual Environment (Recommended)](#quick-start-with-virtual-environment-recommended)
- [Logging](#logging)
  - [Log Directory Structure](#log-directory-structure)
  - [Log Levels](#log-levels)
  - [CLI Logging Options](#cli-logging-options)
  - [Log Format](#log-format)
  - [Quick Reference](#quick-reference)
  - [All Available Commands](#all-available-commands)
- [License](#license)

## Features

- **Type-safe parsing**: Built with Python 3.10+ type hints and dataclasses
- **Comprehensive analysis**: Extract dependencies, plugins, properties, and more
- **Rich CLI interface**: Beautiful command-line interface with colored output
- **Comprehensive logging**: Rolling daily logs with configurable levels and standardized directory structure
- **Dependency analysis**: Analyze dependency trees, versions, and conflicts
- **Plugin inspection**: Examine Maven plugins and their configurations
- **Modern tooling**: Uses lxml for fast XML parsing and Rich for beautiful output

## Getting Started

### First Time Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd pom-reader

# 2. Complete setup (creates virtual environment and installs dependencies)
make setup

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Verify everything works
make test
make run
```

> **Note**: After running `make setup`, you need to activate the virtual environment with `source .venv/bin/activate` before running other commands. The Makefile will automatically detect and use the virtual environment when it's active.
>
> **Alternative**: If you prefer not to use a virtual environment, you can run `make install-dev` instead of `make setup`.

### Common Commands

```bash
# See all available commands
make help

# Check which Python environment is being used
make which-python

# Run the example
make run

# Analyze a POM file
pom-reader analyze resources/pom.xml

# Show dependencies
pom-reader dependencies resources/pom.xml --tree

# Format and test code
make quick

# Clean up
make clean
```

### Environment Management

```bash
# Check virtual environment status
make venv-status

# Check which Python/pip is being used
make which-python

# Activate virtual environment (if not already active)
source .venv/bin/activate

# Deactivate virtual environment
deactivate
```

## Installation

```bash
pip install pom-reader
```

## Command Line Usage

```bash
# Analyze a POM file
pom-reader analyze resources/pom.xml

# Show detailed dependency information
pom-reader dependencies resources/pom.xml --tree

# List all plugins
pom-reader plugins resources/pom.xml

# Export to JSON
pom-reader export resources/pom.xml --format json
```

### Python API

```python
from pom_reader import PomReader
from pom_reader.models import PomFile

# Parse a POM file
reader = PomReader()
pom = reader.parse_file("resources/pom.xml")

# Access project information
print(f"Project: {pom.project.group_id}:{pom.project.artifact_id}")
print(f"Version: {pom.project.version}")

# Analyze dependencies
for dep in pom.dependencies:
    print(f"Dependency: {dep.group_id}:{dep.artifact_id}:{dep.version}")

# Get plugin information
for plugin in pom.plugins:
    print(f"Plugin: {plugin.group_id}:{plugin.artifact_id}")
```

## Development

### Quick Start with Virtual Environment (Recommended)

```bash
# Complete setup with virtual environment
make setup

# Activate the virtual environment
source .venv/bin/activate

# Run tests
make test

# Format code
make format

# Run all checks
make check
```

## Logging

POM Reader includes comprehensive logging with rolling daily logs:

### Log Directory Structure

```none
~/.local/logs/pom-reader/
├── pom-reader.log          # All logs (30 days retention)
└── pom-reader-errors.log   # Error logs only (90 days retention)
```

### Log Levels

- **DEBUG**: Detailed parsing information and function calls
- **INFO**: General operation information (default)
- **WARNING**: Warnings and non-critical issues
- **ERROR**: Errors and exceptions
- **CRITICAL**: Critical errors

### CLI Logging Options

```bash
# Set log level
pom-reader --log-level DEBUG analyze pom.xml

# Custom log directory
pom-reader --log-dir /path/to/logs analyze pom.xml

# Programmatic usage
from pom_reader.logging_config import setup_logging
logger = setup_logging(level="DEBUG")
```

### Log Format

```none
2025-09-09 20:51:08 | INFO | pom-reader.parser | parse_file:50 | Parsing POM file: pom.xml
```

### Quick Reference

| Command             | Description                             |
|---------------------|-----------------------------------------|
| `make help`         | Show all available commands             |
| `make setup`        | Complete setup with virtual environment |
| `make run`          | Run the example script                  |
| `make test`         | Run tests                               |
| `make format`       | Format code (black + isort)             |
| `make lint`         | Lint code (ruff + mypy)                 |
| `make quick`        | Quick dev cycle (format, lint, test)    |
| `make clean`        | Clean build artifacts                   |
| `make venv`         | Create virtual environment              |
| `make venv-status`  | Check virtual environment status        |
| `make which-python` | Show which Python/pip is being used     |

### All Available Commands

Run `make help` to see all available commands, or check the [Makefile](Makefile) for the complete list.

## License

MIT License - see LICENSE file for details.
