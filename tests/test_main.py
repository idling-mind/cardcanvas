from dash import Dash
from dash_dash import DashDash, Card


class TestCard(Card):
    def render(self):
        return "Hello, World!"


def test_main():
    settings = {
        "title": "My Dash App",
        "start_config": {},
    }
    dashboard = DashDash(settings)
    dashboard.card_manager.register_card_class(TestCard)
    assert dashboard.card_manager.card_classes == {"TestCard": TestCard}
    assert isinstance(dashboard.app, Dash)
