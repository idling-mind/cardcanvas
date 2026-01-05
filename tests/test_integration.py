
from cardcanvas import CardCanvas, Card
from dash import Dash
import dash_mantine_components as dmc

class IntegrationTestCard(Card):
    def render(self):
        return "Integration Test"

def test_cardcanvas_initialization():
    settings = {
        "title": "Integration Test App",
        "start_config": {},
    }
    canvas = CardCanvas(settings)
    assert canvas.settings == settings
    assert canvas.card_manager is not None

def test_cardcanvas_app_creation():
    settings = {
        "title": "Integration Test App",
        "start_config": {},
    }
    canvas = CardCanvas(settings)
    app = canvas.app
    assert isinstance(app, Dash)
    assert app.title == "Integration Test App"

def test_cardcanvas_with_custom_components():
    title_comp = dmc.Title("Custom Title")
    footer_comp = dmc.Text("Custom Footer")
    
    settings = {
        "title": "Integration Test App",
        "title_component": title_comp,
        "footer_component": footer_comp,
        "start_config": {},
    }
    canvas = CardCanvas(settings)
    app = canvas.app
    
    # We can't easily inspect the layout deeply without rendering, 
    # but we can check if the app was created successfully.
    assert isinstance(app, Dash)

def test_cardcanvas_register_card():
    settings = {
        "title": "Integration Test App",
        "start_config": {},
    }
    canvas = CardCanvas(settings)
    canvas.card_manager.register_card_class(IntegrationTestCard)
    
    assert "IntegrationTestCard" in canvas.card_manager.card_classes
