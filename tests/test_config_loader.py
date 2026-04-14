"""config_loader 단위 테스트."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from tempfile import TemporaryDirectory

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *_a, **_k: None))
sys.modules.setdefault(
    "collectors",
    types.SimpleNamespace(
        ais_collector=types.SimpleNamespace(collect=None),
        adsb_collector=types.SimpleNamespace(collect=None),
        news_collector=types.SimpleNamespace(collect=None),
        social_collector=types.SimpleNamespace(collect=None),
    ),
)
sys.modules.setdefault("feedparser", types.ModuleType("feedparser"))

from src.kaven import config_loader  # noqa: E402


_TEMP: list[TemporaryDirectory] = []


def _write_config(data: dict, monkeypatch) -> Path:
    tmp = TemporaryDirectory()
    _TEMP.append(tmp)
    path = Path(tmp.name) / "config.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("KAVEN_CONFIG", str(path))
    return path


# ── defaults ──


def test_load_config_without_file_uses_defaults(monkeypatch):
    """KAVEN_CONFIG 미설정 & 파일 없으면 기본값 반환."""
    monkeypatch.delenv("KAVEN_CONFIG", raising=False)
    # 기본 경로에도 파일이 없도록 임시 경로로 설정
    monkeypatch.setenv("KAVEN_CONFIG", "/nonexistent/path/config.json")
    cfg = config_loader.load_config()
    assert "ais_zones" in cfg
    assert len(cfg["ais_zones"]) == len(config_loader.DEFAULT_AIS_ZONES)
    assert cfg["adsb_zones"] == config_loader.DEFAULT_ADSB_ZONES


def test_load_config_with_custom_file(monkeypatch):
    """KAVEN_CONFIG이 가리키는 JSON 파일이 있으면 로드."""
    _write_config({
        "ais_zones": [
            {"id": "custom", "name": "커스텀 해협", "enabled": True,
             "lat_min": 0, "lat_max": 1, "lon_min": 0, "lon_max": 1, "baseline_ships": 10},
        ],
    }, monkeypatch)
    cfg = config_loader.load_config()
    assert len(cfg["ais_zones"]) == 1
    assert cfg["ais_zones"][0]["id"] == "custom"
    # 다른 섹션은 기본값 사용
    assert cfg["adsb_zones"] == config_loader.DEFAULT_ADSB_ZONES


# ── enabled filtering ──


def test_enabled_items_filters_false():
    """enabled=False 항목 제외."""
    items = [
        {"id": "a", "enabled": True},
        {"id": "b", "enabled": False},
        {"id": "c"},  # enabled 미지정 → True 간주
    ]
    result = config_loader.enabled_items(items)
    ids = [x["id"] for x in result]
    assert "a" in ids
    assert "b" not in ids
    assert "c" in ids


def test_get_ais_zones_filters_disabled(monkeypatch):
    """get_ais_zones(only_enabled=True)는 비활성화 항목 제외."""
    _write_config({
        "ais_zones": [
            {"id": "active1",   "name": "활성1", "enabled": True,
             "lat_min": 0, "lat_max": 1, "lon_min": 0, "lon_max": 1},
            {"id": "inactive", "name": "비활성", "enabled": False,
             "lat_min": 0, "lat_max": 1, "lon_min": 0, "lon_max": 1},
            {"id": "active2",  "name": "활성2", "enabled": True,
             "lat_min": 0, "lat_max": 1, "lon_min": 0, "lon_max": 1},
        ],
    }, monkeypatch)
    zones = config_loader.get_ais_zones(only_enabled=True)
    assert len(zones) == 2
    assert [z["id"] for z in zones] == ["active1", "active2"]


def test_get_ais_zones_all_when_not_filtered(monkeypatch):
    """only_enabled=False면 전체 반환."""
    _write_config({
        "ais_zones": [
            {"id": "a", "name": "A", "enabled": True,
             "lat_min": 0, "lat_max": 1, "lon_min": 0, "lon_max": 1},
            {"id": "b", "name": "B", "enabled": False,
             "lat_min": 0, "lat_max": 1, "lon_min": 0, "lon_max": 1},
        ],
    }, monkeypatch)
    assert len(config_loader.get_ais_zones(only_enabled=False)) == 2
    assert len(config_loader.get_ais_zones(only_enabled=True)) == 1


def test_get_news_feeds_filters_disabled(monkeypatch):
    _write_config({
        "news_feeds": [
            {"id": "a", "name": "A", "enabled": True, "url": "http://a"},
            {"id": "b", "name": "B", "enabled": False, "url": "http://b"},
        ],
    }, monkeypatch)
    feeds = config_loader.get_news_feeds(only_enabled=True)
    assert len(feeds) == 1
    assert feeds[0]["id"] == "a"


def test_get_social_keywords_all_disabled_returns_empty(monkeypatch):
    """전부 비활성이면 빈 리스트."""
    _write_config({
        "social_keywords": [
            {"id": "a", "query": "A", "enabled": False},
            {"id": "b", "query": "B", "enabled": False},
        ],
    }, monkeypatch)
    assert config_loader.get_social_keywords(only_enabled=True) == []


# ── fault tolerance ──


def test_malformed_json_falls_back_to_defaults(monkeypatch):
    """잘못된 JSON이면 warning 후 기본값 반환."""
    tmp = TemporaryDirectory()
    _TEMP.append(tmp)
    path = Path(tmp.name) / "config.json"
    path.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setenv("KAVEN_CONFIG", str(path))

    cfg = config_loader.load_config()
    # 기본값이 그대로 반환되어야 함 (예외 발생 X)
    assert cfg["ais_zones"] == config_loader.DEFAULT_AIS_ZONES
