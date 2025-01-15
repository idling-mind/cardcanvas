from cardcanvas import CardCanvas, Card
import dash_mantine_components as dmc
import pandas as pd

data = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv"
)

settings = {
    "title": "CardCanvas Demo",
    "subtitle": "A Demo application showing the capabilities of CardCanvas",
    "start_config": {},
    "logo": "https://img.icons8.com/?size=80&id=cjlQopC5NR3D&format=png",
    "grid_compact_type": "vertical",
    "grid_row_height": 100,
}


class BarChartCard(Card):
    title = "Bar Chart"
    description = "A simple bar chart"
    icon = "mdi:file-document-edit"

    def render(self):
        title = self.settings.get("title", "Bar Chart")
        countries = self.settings.get("countries", ["United States", "China", "India"])
        groupbycol = self.settings.get("dataKey", "country")
        colorcol = self.settings.get("colorby", "continent")
        fields = self.settings.get("fields", ["pop"])
        aggfuncs = self.settings.get("aggfuncs", ["sum"])

        grouped_data = (
            data.groupby("country")
            .agg({"pop": "max", "gdpPercap": "mean"})
            .reset_index()
        ).to_dict("records")

        return dmc.Card(
            [
                dmc.Title(self.settings.get("text", "Hello CardCanvas"), c="blue"),
                dmc.BarChart(
                    h="100%",
                    data=grouped_data,
                    dataKey="country",
                    series=[
                        {"name": "pop", "color": "blue.6"},
                        {"name": "gdpPercap", "color": "green.6"},
                    ],
                ),
            ],
            style={"height": "100%", "width": "100%"},
        )


canvas = CardCanvas(settings)
canvas.card_manager.register_card_class(BarChartCard)

canvas.app.run_server(debug=True)
