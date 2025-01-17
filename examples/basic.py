from cardcanvas import CardCanvas, Card
import dash_mantine_components as dmc

settings = {
    "title": "CardCanvas Demo",
    "subtitle": "A Demo application showing the capabilities of CardCanvas",
    "start_config": {},
    "logo": "https://img.icons8.com/?size=80&id=cjlQopC5NR3D&format=png",
    "grid_compact_type": "vertical",
    "grid_row_height": 100,
}


class TextCard(Card):
    title = "White text with a background color"
    description = "Testing out CardCanvas"
    icon = "mdi:file-document-edit"

    def render(self):
        return dmc.Card(
            dmc.Title(
                self.settings.get("text", "Hello CardCanvas"),
                c="white",
            ),
            bg=self.settings.get("color", "blue"),
            style={"height": "100%", "width": "100%"},
        )

    def render_settings(self):
        return dmc.Stack(
            [
                dmc.TextInput(
                    id={"type": "card-settings", "id": self.id, "setting": "text"},
                    value=self.settings.get("text", "Hello CardCanvas"),
                ),
                dmc.ColorPicker(
                    id={"type": "card-settings", "id": self.id, "setting": "color"},
                    value=self.settings.get("color", "grey"),
                ),
            ]
        )


canvas = CardCanvas(settings)
canvas.card_manager.register_card_class(TextCard)

canvas.app.run_server(debug=True)
