from dash import Dash
from cardcanvas import CardCanvas, Card
from cardcanvas.main import (
    _build_card_share_payload,
    _is_shared_search,
    _search_to_share_payload,
    _share_payload_to_search,
    _share_payload_to_state,
)


class TestCard(Card):
    def render(self):
        return "Hello, World!"


def test_main():
    settings = {
        "title": "My Dash App",
        "start_config": {},
    }
    dashboard = CardCanvas(settings)
    dashboard.card_manager.register_card_class(TestCard)
    assert dashboard.card_manager.card_classes == {"TestCard": TestCard}
    assert isinstance(dashboard.app, Dash)


def test_share_payload_round_trip_state():
    card_config = {
        "card-1": {
            "card_class": "TestCard",
            "settings": {"metric": "sales"},
        },
        "card-2": {
            "card_class": "TestCard",
            "settings": {"metric": "profit"},
        },
    }
    card_layouts = {
        "lg": [
            {"i": "card-1", "x": 0, "y": 0, "w": 6, "h": 4},
            {"i": "card-2", "x": 6, "y": 0, "w": 6, "h": 4},
        ],
        "md": [
            {"i": "card-1", "x": 0, "y": 0, "w": 8, "h": 4},
        ],
    }
    global_settings = {"region": "EU"}

    payload = _build_card_share_payload(
        card_id="card-1",
        card_config=card_config,
        card_layouts=card_layouts,
        global_settings=global_settings,
    )
    assert payload is not None

    search = _share_payload_to_search(payload)
    parsed_payload = _search_to_share_payload(search)
    share_state = _share_payload_to_state(parsed_payload)

    assert share_state is not None
    assert set(share_state["card_config"].keys()) == {"card-1"}
    assert share_state["card_config"]["card-1"]["settings"] == {"metric": "sales"}
    assert share_state["global_settings"] == {"region": "EU"}
    assert share_state["card_layouts"]["lg"] == [
        {"i": "card-1", "x": 0, "y": 0, "w": 6, "h": 4}
    ]
    assert share_state["card_layouts"]["md"] == [
        {"i": "card-1", "x": 0, "y": 0, "w": 8, "h": 4}
    ]


def test_share_payload_invalid_query_returns_none():
    payload = _search_to_share_payload("?ccs=not-json")
    assert payload is None


def test_build_share_payload_for_missing_card_returns_none():
    payload = _build_card_share_payload(
        card_id="missing-card",
        card_config={"card-1": {"card_class": "TestCard", "settings": {}}},
        card_layouts={"lg": []},
        global_settings={},
    )
    assert payload is None


def test_is_shared_search_true_for_valid_payload():
    payload = {
        "v": 1,
        "card_id": "card-1",
        "card": {"card_class": "TestCard", "settings": {}},
        "layouts": {"lg": [{"i": "card-1", "x": 0, "y": 0, "w": 6, "h": 4}]},
        "global_settings": {},
    }
    search = _share_payload_to_search(payload)
    assert _is_shared_search(search)


def test_is_shared_search_false_for_invalid_payload():
    assert not _is_shared_search("?ccs=not-json")
