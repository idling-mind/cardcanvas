from cardcanvas import CardCanvas, Card, GlobalSettings
import json
from dash import html
import dash_mantine_components as dmc
import datetime

class Settings(GlobalSettings):
    def render_settings(self):
        return dmc.Stack(
            [
                dmc.Text("Some setting"),
                dmc.Select(
                    id={"type": "global-settings", "setting": "global_setting_1"},
                    value=self.settings.get("global_setting_1", "Option 1"),
                    data=[
                        {"label": "Option 1", "value": "Option 1"},
                        {"label": "Option 2", "value": "Option 2"},
                        {"label": "Option 3", "value": "Option 3"},
                        {"label": "Option 4", "value": "Option 4"},
                    ],
                ),
            ]
        )


settings = {
    "title": "Card Canvas Demo",
    "subtitle": "A Demo application showing the capabilities of CardCanvas",
    "start_config": {},
    "logo": "https://img.icons8.com/?size=80&id=cjlQopC5NR3D&format=png",
    "grid_compact_type": "vertical",
    "grid_row_height": 100,
}


swatches = [
    "#25262b",
    "#868e96",
    "#fa5252",
    "#e64980",
    "#be4bdb",
    "#7950f2",
    "#4c6ef5",
    "#228be6",
    "#15aabf",
    "#12b886",
    "#40c057",
    "#82c91e",
    "#fab005",
    "#fd7e14",
]


class TimeCard(Card):
    title = "Display Time"
    description = "Display current time on the card and update every minute"
    icon = "mdi:clock"
    color = "blue"
    interval = 1000 * 60
    grid_settings = {"w": 6, "minW": 6}

    def render(self):
        return dmc.Card(
            [
                dmc.Title(
                    f"Now time is: {datetime.datetime.now().strftime('%H:%M:%S')}",
                    c=self.settings.get("text-color", "white"),
                    order=2,
                ),
            ],
            style={
                "height": "100%",
                "width": "100%",
                "background": self.settings.get("background-color", "#336699"),
            },
        )

    def render_settings(self):
        return dmc.Stack(
            [
                dmc.Text("Text Color"),
                dmc.ColorPicker(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "text-color",
                    },
                    value=self.settings.get("text-color", "white"),
                    swatches=swatches,
                ),
                dmc.Text("Background Color"),
                dmc.ColorPicker(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "background-color",
                    },
                    value=self.settings.get("background-color", "#336699"),
                    swatches=swatches,
                ),
            ]
        )

class GlobalSettingsCard(Card):
    title = "Global Settings"
    description = "Display the global settings"
    icon = "mdi:settings"
    color = "purple"

    def render(self):
        return dmc.Card(
            [
                dmc.JsonInput(
                    value=json.dumps(self.global_settings, indent=2),
                    minRows=15,
                    maxRows=15,
                    style={"width": "100%", "height": "100%"},
                    resize="vertical",
                    className="no-drag",
                ),
            ],
            h="100%",
            withBorder=True,
        )

    def render_settings(self):
        return dmc.Stack(
            [
                dmc.Text(
                    "This card does not have any settings, it just displays the global settings"
                ),
            ]
        )

class Options(Card):
    title = "List of options"
    description = "Select from a list of options"
    icon = "mdi:form-select"
    color = "green"

    def render(self):
        return dmc.Card(
            [
                dmc.Text(
                    (
                        f"You have selected {','.join(self.settings.get('option', []))}"
                        f" and the global_setting_1 is {self.global_settings.get('global_setting_1', 'not set')}"
                    ),
                ),
            ],
            style={"height": "100%", "width": "100%"},
            withBorder=True,
        )

    def render_settings(self):
        return dmc.Stack(
            [
                dmc.MultiSelect(
                    id={"type": "card-settings", "id": self.id, "setting": "option"},
                    placeholder="Select an option",
                    label="Select an option",
                    value=self.settings.get("option", []),
                    data=[
                        {"label": "Option 1", "value": "option1"},
                        {"label": "Option 2", "value": "option2"},
                        {"label": "Option 3", "value": "option3"},
                    ],
                ),
            ]
        )


class ColorCard(Card):
    title = "Color Card"
    description = "This card just shows a coloured background"
    icon = "mdi:color"
    color = "orange"

    def render(self):
        return dmc.Paper(
            [dmc.Card(bg=self.settings.get("color", "orange"), h="100%")],
            h="100%",
        )

    def render_settings(self):
        return dmc.Stack(
            [
                dmc.ColorPicker(
                    id={"type": "card-settings", "id": self.id, "setting": "color"},
                    value=self.settings.get("color", "grey"),
                    swatches=swatches,
                ),
            ]
        )


canvas = CardCanvas(settings)
canvas.card_manager.register_card_class(TimeCard)
canvas.card_manager.register_card_class(GlobalSettingsCard)
canvas.card_manager.register_card_class(ColorCard)
canvas.card_manager.register_card_class(Options)
canvas.card_manager.register_global_settings_class(Settings)

canvas.app.run_server(debug=True)
