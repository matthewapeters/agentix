"""
Docstring for tests.test_agentix_config
"""

import os

from agentix.agentix_config import AgentixConfig


def test_agentixconfig_defaults():
    config = AgentixConfig()
    assert config.debug is False
    assert config.list_models is False
    assert config.list_sessions is False
    assert config.list_prompts is False
    assert config.session == "default_session"
    assert config.temperature == 0.7
    assert config.port == 8000
    assert config.with_frontend is False


def test_merge_configs_flat():
    base = {"a": 1, "b": 2}
    override = {"b": 3, "c": 4}
    merged = AgentixConfig.merge_configs(base, override)
    assert merged == {"a": 1, "b": 3, "c": 4}


def test_merge_configs_nested():
    base = {"a": {"x": 1, "y": 2}, "b": 2}
    override = {"a": {"y": 3, "z": 4}, "b": 5}
    merged = AgentixConfig.merge_configs(base, override)
    assert merged == {"a": {"x": 1, "y": 3, "z": 4}, "b": 5}


def test_find_local_config(tmp_path):
    config_name = "agentix_config.toml"
    config_path = tmp_path / config_name
    config_path.write_text("[section]\nkey = 'value'\n")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        found = AgentixConfig.find_local_config(config_name)
        assert found == str(config_path)
    finally:
        os.chdir(old_cwd)


def test_find_local_config_not_found(tmp_path):
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        found = AgentixConfig.find_local_config("nonexistent.toml")
        assert found is None
    finally:
        os.chdir(old_cwd)


def test_load_local_config(tmp_path):
    config_name = "agentix_config.toml"
    config_path = tmp_path / config_name
    config_content = """
    [section]
    key = "value"
    num = 42
    """
    config_path.write_text(config_content)
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        loaded = AgentixConfig.load_local_config(config_name)
        assert "section" in loaded
        assert loaded["section"]["key"] == "value"
        assert loaded["section"]["num"] == 42
    finally:
        os.chdir(old_cwd)


def test_load_local_config_not_found(tmp_path):
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        loaded = AgentixConfig.load_local_config("nonexistent.toml")
        assert loaded == {}
    finally:
        os.chdir(old_cwd)
