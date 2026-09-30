"""Tests for the V11 environment-driven configuration loader."""

from v11.config import Config, load_config


def test_load_config_uses_defaults_when_env_is_empty():
    config = load_config(environ={})

    assert config == Config(
        env="dev",
        metrics_port=9090,
        webhook_url=None,
        log_level="INFO",
    )


def test_load_config_reads_rd_guard_env():
    config = load_config(environ={"RD_GUARD_ENV": "prod"})

    assert config.env == "prod"


def test_load_config_rejects_unknown_env_and_falls_back_to_dev():
    config = load_config(environ={"RD_GUARD_ENV": "not-a-real-env"})

    assert config.env == "dev"


def test_load_config_reads_metrics_port():
    config = load_config(environ={"METRICS_PORT": "9999"})

    assert config.metrics_port == 9999


def test_load_config_falls_back_to_default_port_on_bad_value():
    config = load_config(environ={"METRICS_PORT": "not-a-port"})

    assert config.metrics_port == 9090


def test_load_config_reads_webhook_url():
    config = load_config(
        environ={"RD_GUARD_WEBHOOK_URL": "https://hooks.example.com/alert"}
    )

    assert config.webhook_url == "https://hooks.example.com/alert"


def test_load_config_webhook_url_defaults_to_none_when_unset():
    config = load_config(environ={})

    assert config.webhook_url is None


def test_load_config_webhook_url_is_none_when_blank():
    config = load_config(environ={"RD_GUARD_WEBHOOK_URL": ""})

    assert config.webhook_url is None


def test_load_config_reads_log_level():
    config = load_config(environ={"RD_GUARD_LOG_LEVEL": "debug"})

    assert config.log_level == "DEBUG"


def test_load_config_reads_all_variables_together():
    config = load_config(
        environ={
            "RD_GUARD_ENV": "staging",
            "METRICS_PORT": "9091",
            "RD_GUARD_WEBHOOK_URL": "https://hooks.example.com/alert",
            "RD_GUARD_LOG_LEVEL": "WARNING",
        }
    )

    assert config == Config(
        env="staging",
        metrics_port=9091,
        webhook_url="https://hooks.example.com/alert",
        log_level="WARNING",
    )


def test_load_config_defaults_to_os_environ(monkeypatch):
    monkeypatch.setenv("RD_GUARD_ENV", "prod")
    monkeypatch.setenv("METRICS_PORT", "9092")
    monkeypatch.delenv("RD_GUARD_WEBHOOK_URL", raising=False)
    monkeypatch.setenv("RD_GUARD_LOG_LEVEL", "error")

    config = load_config()

    assert config.env == "prod"
    assert config.metrics_port == 9092
    assert config.webhook_url is None
    assert config.log_level == "ERROR"
