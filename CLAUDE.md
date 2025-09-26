# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project called "reader" managed with Poetry for dependency management and packaging.

## Development Commands

### Poetry Commands
- `poetry install` - Install all dependencies and create virtual environment
- `poetry add <package>` - Add a new dependency
- `poetry add --group dev <package>` - Add a development dependency
- `poetry remove <package>` - Remove a dependency
- `poetry run <command>` - Run command in Poetry virtual environment
- `poetry shell` - Activate Poetry virtual environment
- `poetry lock` - Update poetry.lock file
- `poetry show` - List installed packages

### Testing and Code Quality
- `poetry run pytest` - Run tests
- `poetry run black .` - Format code
- `poetry run flake8` - Lint code

## Architecture and Structure

- Dependencies managed via `pyproject.toml`
- Virtual environment managed by Poetry
- Development dependencies isolated in dev group
- Source code in `reader/` package directory

## Getting Started

1. Install dependencies: `poetry install`
2. Add new dependencies: `poetry add <package>`
3. Run commands in environment: `poetry run <command>`
4. Always commit `poetry.lock` for reproducible builds

## Important Notes

- Never manually edit `poetry.lock` - let Poetry manage it
- Use `poetry add` instead of pip install
- Prefer virtual environment managed by Poetry over manual venv creation
- Specify version constraints when adding dependencies for stability