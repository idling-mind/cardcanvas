
from cardcanvas.card_manager import Card
from dash import html
import dash_mantine_components as dmc

class SimpleCard(Card):
    def render(self):
        return html.Div("Simple Content")

class ErrorCard(Card):
    def render(self):
        raise ValueError("Intentional Error")

def test_card_init():
    card = SimpleCard("test_id", {"global": "val"}, {"local": "val"})
    assert card.id == "test_id"
    assert card.global_settings == {"global": "val"}
    assert card.settings == {"local": "val"}

def test_render_container_structure():
    card = SimpleCard("test_id")
    container = card.render_container()
    
    assert isinstance(container, html.Div)
    assert container.id == "test_id"
    
    # Check for children: Loading component and buttons
    assert len(container.children) >= 2
    
    # First child should be Loading component wrapping content
    loading = container.children[0]
    # Depending on implementation, might need to check type strictly or duck typing
    # It is dcc.Loading
    assert hasattr(loading, 'children') 
    
    # Inside loading, there should be the content div
    content_div = loading.children
    assert content_div.id == {"type": "card-content", "index": "test_id"}
    
    # Inside content div, there should be the result of render()
    assert content_div.children.children == "Simple Content"

def test_render_container_error_handling():
    card = ErrorCard("error_id")
    container = card.render_container()
    
    loading = container.children[0]
    content_div = loading.children
    
    # Should contain an Alert because debug is False by default
    alert = content_div.children
    assert isinstance(alert, dmc.Alert)
    assert "Intentional Error" in str(alert.children)

def test_render_container_error_handling_debug():
    card = ErrorCard("error_id")
    card.debug = True
    container = card.render_container()
    
    loading = container.children[0]
    content_div = loading.children
    
    # Should contain a Div with Pre because debug is True
    error_div = content_div.children
    assert isinstance(error_div, html.Div)
    # The first child of the error div is html.Pre
    assert isinstance(error_div.children, html.Pre)
    assert "Intentional Error" in error_div.children.children

def test_render_settings_default():
    card = SimpleCard("test_id")
    settings = card.render_settings()
    assert isinstance(settings, dmc.Text)
    assert "Settings not implemented yet" in settings.children
