
from cardcanvas.card_manager import CardManager, Card, GlobalSettings
from dash import html

class MockCard(Card):
    def render(self):
        return html.Div("Mock Card Content")

class MockGlobalSettings(GlobalSettings):
    def render_settings(self):
        return html.Div("Mock Global Settings")

def test_register_card_class():
    manager = CardManager()
    manager.register_card_class(MockCard)
    assert "MockCard" in manager.card_classes
    assert manager.card_classes["MockCard"] == MockCard

def test_register_global_settings_class():
    manager = CardManager()
    manager.register_global_settings_class(MockGlobalSettings)
    assert manager.global_settings_class == MockGlobalSettings

def test_card_objects():
    manager = CardManager()
    manager.register_card_class(MockCard)
    
    card_config = {
        "card1": {
            "card_class": "MockCard",
            "settings": {"foo": "bar"}
        }
    }
    global_settings = {"theme": "dark"}
    
    cards = manager.card_objects(card_config, global_settings)
    
    assert "card1" in cards
    assert isinstance(cards["card1"], MockCard)
    assert cards["card1"].id == "card1"
    assert cards["card1"].settings == {"foo": "bar"}
    assert cards["card1"].global_settings == global_settings

def test_card_objects_unknown_class():
    manager = CardManager()
    # MockCard is NOT registered
    
    card_config = {
        "card1": {
            "card_class": "MockCard",
            "settings": {}
        }
    }
    
    cards = manager.card_objects(card_config)
    assert "card1" not in cards

def test_render():
    manager = CardManager()
    manager.register_card_class(MockCard)
    
    card_config = {
        "card1": {
            "card_class": "MockCard",
            "settings": {}
        }
    }
    
    rendered_cards = manager.render(card_config)
    assert len(rendered_cards) == 1
    assert isinstance(rendered_cards[0], html.Div)
    # Check if the ID is set correctly on the container
    assert rendered_cards[0].id == "card1"
