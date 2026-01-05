
from cardcanvas import ui
import dash_mantine_components as dmc
from dash import dcc

def test_button_with_tooltip():
    btn = ui.button_with_tooltip("btn-id", "mdi:home", "Home", "Go Home", variant="filled")
    
    assert isinstance(btn, dmc.Tooltip)
    assert btn.label == "Go Home"
    
    inner_btn = btn.children
    assert isinstance(inner_btn, dmc.Button)
    assert inner_btn.id == "btn-id"
    assert inner_btn.children == "Home"
    assert inner_btn.variant == "filled"

def test_icon_with_tooltip():
    icon_btn = ui.icon_with_tooltip("icon-id", "mdi:cog", "Settings", "Open Settings", color="red")
    
    assert isinstance(icon_btn, dmc.ActionIcon)
    assert icon_btn.id == "icon-id"
    assert icon_btn.color == "red"
    
    tooltip = icon_btn.children
    assert isinstance(tooltip, dmc.Tooltip)
    assert tooltip.label == "Open Settings"

def test_main_buttons():
    # Test with global settings enabled
    group = ui.main_buttons(global_settings=True)
    
    assert isinstance(group, dmc.Group)
    assert group.id == "toolbar"
    
    # Check children
    children = group.children
    # Should have open-global-settings button
    assert children[0].id == "open-global-settings"
    
    # Test with global settings disabled
    group_no_global = ui.main_buttons(global_settings=False)
    children_no_global = group_no_global.children
    # Should NOT have open-global-settings button
    assert children_no_global[0].id != "open-global-settings"
    assert children_no_global[0].id == "add-cards"
