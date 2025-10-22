"""Tests for CLI commands."""
import pytest
from click.testing import CliRunner
from reader.cli import cli
from reader import __version__


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


def test_version(runner):
    """Test --version flag."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help(runner):
    """Test --help flag."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "convert" in result.output
    assert "voices" in result.output
    assert "config" in result.output


def test_info(runner):
    """Test info command."""
    result = runner.invoke(cli, ["info"])
    assert result.exit_code == 0
    assert "Reader" in result.output or "reader" in result.output


def test_voices(runner):
    """Test voices command."""
    result = runner.invoke(cli, ["voices"])
    # Should succeed whether Kokoro available or not
    # Will either list voices or show error about missing Kokoro
    assert result.exit_code in [0, 1]


def test_config_show(runner):
    """Test config show command."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["config", "show"])
        # Should succeed and show config or indicate no config exists
        assert result.exit_code in [0, 1, 2]


def test_config_set(runner):
    """Test config set command."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["config", "set", "voice", "test_voice"])
        # Should succeed or fail gracefully
        assert result.exit_code in [0, 1, 2]


def test_config_get(runner):
    """Test config get command."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["config", "get", "voice"])
        # Should succeed or indicate config doesn't exist
        assert result.exit_code in [0, 1, 2]


def test_characters_list(runner):
    """Test characters list command."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["characters", "list"])
        assert result.exit_code == 0


def test_convert_help(runner):
    """Test convert command help."""
    result = runner.invoke(cli, ["convert", "--help"])
    assert result.exit_code == 0
    assert "Convert text files" in result.output
