from dash import Dash
from cardcanvas import CardCanvas, Card


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
