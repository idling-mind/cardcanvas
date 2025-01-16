from pathlib import Path
import json
from cardcanvas import CardCanvas, Card
from dash import (
    html,
    dcc,
    callback,
    Input,
    State,
    Output,
    MATCH,
    ALL,
    Patch,
    callback_context,
    no_update,
)
import dash_mantine_components as dmc
import plotly.express as px
import plotly.io as pio
import pandas as pd
from dash_iconify import DashIconify

settings = {
    "title": "Card Canvas Charts Demo",
    "subtitle": "A Demo application showing the capabilities of CardCanvas with charts",
    "start_config": {},
    "grid_compact_type": "vertical",
    "grid_row_height": 120,
}

data = pd.read_csv(
    "https://raw.githubusercontent.com/datasciencedojo/datasets/refs/heads/master/titanic.csv"
)
data["Survived"] = data["Survived"].apply(lambda x: "Survived" if x == 1 else "Died")

class HistogramCard(Card):
    title = "Histogram"
    description = "This card shows a histogram of a given dataset"
    icon = "mdi:file-document-edit"
    grid_settings = {"w": 4, "h": 2, "minW": 4, "minH": 2}

    def render(self):
        column = self.settings.get("column", "Age")
        color = self.settings.get("color", None)
        nbins = self.settings.get("bins", 20)
        title = self.settings.get("title", "Histogram")
        description = self.settings.get("description", f"Histogram of {column}")

        figure = px.histogram(
            data,
            x=column,
            color=color,
            nbins=nbins,
            template="mantine_light",
        )
        figure.update_layout(margin=dict(l=0, r=0, t=15, b=0))
        return dmc.Card(
            [
                dmc.Text(
                    title, fz="30px", fw=600, c="blue"
                ),
                dmc.Text(
                    description,
                    fw=600,
                    c="dimmed",
                ),
                dcc.Graph(
                    figure=figure,
                    id={"type": "card-control", "sub-type": "figure", "id": self.id},
                    className="no-drag",
                    responsive=True,
                    style={"height": "100%"},
                ),
            ],
            style={"height": "100%"},
            withBorder=True,
            shadow="xs",
        )

    def render_settings(self):
        column = self.settings.get("column", "Age")
        color = self.settings.get("color", None)
        nbins = self.settings.get("bins", 20)
        title = self.settings.get("title", "Histogram")
        description = self.settings.get("description", "Histogram description")
        return dmc.Stack(
            [
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "column",
                    },
                    label="Column",
                    value=column,
                    searchable=True,
                    # numeric columns in data
                    data=[
                        {"label": column, "value": column}
                        for column in data.select_dtypes(include="number").columns
                    ],
                ),
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "color",
                    },
                    label="Color",
                    value=color,
                    searchable=True,
                    data=[
                        {"label": i, "value": i}
                        for i in data.select_dtypes(exclude="number").columns
                    ],
                ),
                dmc.NumberInput(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "bins",
                    },
                    label="Bins",
                    value=nbins,
                    min=1,
                ),
                dmc.TextInput(
                    id={"type": "card-settings", "id": self.id, "setting": "title"},
                    label="Title",
                    value=title,
                ),
                dmc.TextInput(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "description",
                    },
                    label="Description",
                    value=description,
                ),
            ]
        )


def generate_filter(column: pd.Series, input_id, default_value=None):
    """Creating a filter based on the column type and it's unique values
    Used in heatmap card to filter the data based on the column values
    """
    column = column.dropna()
    card_id = input_id["id"]
    filter_type = input_id["setting"]
    if column.unique().shape[0] == 0:
        return dmc.Text("No data to filter", fz="14px", fw=600, c="red")
    elif column.unique().shape[0] == 1:
        return dmc.Text("Only one value, no need to filter", fz="14px", fw=600)
    if column.dtype in ["object", "string", "bool", "category"] or len(column.unique()) < 5:
        sorted_unique = sorted(column.unique().tolist())
        if len(sorted_unique) > 100:
            return dmc.Text(
                "Too many unique values to show filter", fz="14px", fw=600, c="red"
            )
        return [
            dmc.Text("Filter", fz="14px", fw=600),
            dmc.ScrollArea(
                dmc.CheckboxGroup(
                    id={
                        "type": "card-settings",
                        "id": card_id,
                        "setting": f"{filter_type}-filter",
                    },
                    value=default_value or sorted_unique,
                    children=dmc.Stack(
                        [dmc.Checkbox(label=str(x), value=str(x)) for x in sorted_unique]
                    ),
                ),
                h=250,
            ),
        ]
    return [
        dmc.Text("Filter", fz="14px", fw=600),
        dmc.RangeSlider(
            id={
                "type": "card-settings",
                "id": card_id,
                "setting": f"{filter_type}-filter",
            },
            value=default_value or [column.min(), column.max()],
            min=column.min(),
            max=column.max(),
            minRange=(column.max() - column.min()) / 100,
        ),
    ]


class HeatMap(Card):
    title = "Heatmap"
    description = "This card shows a heatmap of a given dataset"
    icon = "mdi:file-document-edit"
    grid_settings = {"w": 4, "h": 2, "minW": 4, "minH": 2}

    def render(self):
        x = self.settings.get("x", "Age")
        x_filter = self.settings.get("x-filter", None)
        y = self.settings.get("y", "Fare")
        y_filter = self.settings.get("y-filter", None)
        nbinsx = self.settings.get("nbinsx", 20)
        nbinsy = self.settings.get("nbinsy", 20)
        title = self.settings.get("title", "Heatmap")
        description = self.settings.get("description", f"Heatmap of {x} vs {y}")

        filtered_data = data.loc[:, [x, y]]
        if x_filter is not None:
            if filtered_data[x].dtype in ["object", "string", "bool", "category"]:
                filtered_data = filtered_data[filtered_data[x].isin(x_filter)]
            else:
                filtered_data = filtered_data[
                    (filtered_data[x] >= x_filter[0])
                    & (filtered_data[x] <= x_filter[1])
                ]
        if y_filter is not None:
            if filtered_data[y].dtype in ["object", "string", "bool", "category"]:
                filtered_data = filtered_data[filtered_data[y].isin(y_filter)]
            else:
                filtered_data = filtered_data[
                    (filtered_data[y] >= y_filter[0])
                    & (filtered_data[y] <= y_filter[1])
                ]
        figure = px.density_heatmap(
            filtered_data,
            x=x,
            y=y,
            nbinsx=nbinsx,
            nbinsy=nbinsy,
            template="mantine_light",
        )
        figure.update_layout(margin=dict(l=0, r=0, t=15, b=0))
        return dmc.Card(
            [
                dmc.Text(
                    title, fz="30px", fw=600, c="blue"
                ),
                dmc.Text(
                    description,
                    fw=600,
                    c="dimmed",
                ),
                dcc.Graph(
                    figure=figure,
                    id={"type": "card-control", "sub-type": "figure", "id": self.id},
                    className="no-drag",
                    responsive=True,
                    style={"height": "100%"},
                ),
            ],
            style={"height": "100%"},
            withBorder=True,
            shadow="xs",
        )

    def render_settings(self):
        x = self.settings.get("x", "Age")
        y = self.settings.get("y", "Fare")
        x_filter = self.settings.get("x-filter", None)
        y_filter = self.settings.get("y-filter", None)
        nbinsx = self.settings.get("nbinsx", 20)
        nbinsy = self.settings.get("nbinsy", 20)
        title = self.settings.get("title", "Heatmap")
        description = self.settings.get("description", "Heatmap description")

        return dmc.Stack(
            [
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "x",
                    },
                    label="X",
                    value=x,
                    searchable=True,
                    # numeric columns in data
                    data=[
                        {"label": column, "value": column} for column in data.columns
                    ],
                ),
                html.Div(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "container": "x-filter",
                    },
                    children=generate_filter(
                        data[x],
                        {"type": "card-settings", "id": self.id, "setting": "x"},
                        default_value=x_filter,
                    ),
                ),
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "y",
                    },
                    label="Y",
                    value=y,
                    searchable=True,
                    data=[{"label": i, "value": i} for i in data.columns],
                ),
                html.Div(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "container": "y-filter",
                    },
                    children=generate_filter(
                        data[y],
                        {"type": "card-settings", "id": self.id, "setting": "y"},
                        default_value=y_filter,
                    ),
                ),
                dmc.NumberInput(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "nbinsx",
                    },
                    label="Number of bins in x direction",
                    value=nbinsx,
                    min=5,
                ),
                dmc.NumberInput(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "nbinsy",
                    },
                    label="Number of bins in y direction",
                    value=nbinsy,
                    min=5,
                ),
                dmc.TextInput(
                    id={"type": "card-settings", "id": self.id, "setting": "title"},
                    label="Title",
                    value=title,
                ),
                dmc.TextInput(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "description",
                    },
                    label="Description",
                    value=description,
                ),
            ]
        )

    @callback(
        Output(
            {"type": "card-settings", "id": MATCH, "container": "x-filter"}, "children"
        ),
        Input({"type": "card-settings", "id": MATCH, "setting": "x"}, "value"),
    )
    def update_filter_x(value):
        """If the column is categorical, show a dropdown to filter the data
        else if data is numeric, show a slider to filter the data"""
        column = data[value]
        # get the input id
        ctx = callback_context
        if not ctx.triggered_id:
            return no_update
        input_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
        return generate_filter(column, input_id)

    @callback(
        Output(
            {"type": "card-settings", "id": MATCH, "container": "y-filter"}, "children"
        ),
        Input({"type": "card-settings", "id": MATCH, "setting": "y"}, "value"),
    )
    def update_filter_y(value):
        column = data[value]
        ctx = callback_context
        if not ctx.triggered_id:
            return no_update
        input_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
        return generate_filter(column, input_id)


class ViolinCard(Card):
    title = "Violin"
    description = "This card shows a violin plot of a given dataset"
    icon = "mdi:file-document-edit"
    grid_settings = {"w": 4, "h": 2, "minW": 4, "minH": 2}

    def render(self):
        x = self.settings.get("x", "Pclass")
        y = self.settings.get("y", "Age")
        title = self.settings.get("title", "Violin plot")
        description = self.settings.get("description", f"Violin plot of {y} by {x}")
        fig = px.violin(
            data,
            x=x,
            y=y,
            template="mantine_light",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=15, b=0))
        fig.update_xaxes(
            categoryorder="array",
            categoryarray=data[x].unique(),
        )
        return dmc.Card(
            [
                dmc.Text(
                    title,
                    fz="30px",
                    fw=600,
                    c="blue",
                ),
                dmc.Text(
                    description,
                    fw=600,
                    c="dimmed",
                ),
                dcc.Graph(
                    figure=fig,
                    id={"type": "card-control", "sub-type": "figure", "id": self.id},
                    className="no-drag",
                    responsive=True,
                    style={"height": "100%"},
                ),
            ],
            style={"height": "100%"},
            withBorder=True,
            shadow="xs",
        )

    def render_settings(self):
        x = self.settings.get("x", "Pclass")
        y = self.settings.get("y", "Age")
        title = self.settings.get("title", "Violin plot")
        description = self.settings.get("description", "Violin plot description")
        return dmc.Stack(
            [
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "x",
                    },
                    label="X",
                    value=x,
                    searchable=True,
                    data=[
                        {"label": column, "value": column} for column in data.columns
                    ],
                ),
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "y",
                    },
                    label="Y",
                    value=y,
                    searchable=True,
                    # numeric columns in data
                    data=[
                        {"label": column, "value": column}
                        for column in data.select_dtypes(include="number").columns
                    ],
                ),
                dmc.TextInput(
                    id={"type": "card-settings", "id": self.id, "setting": "title"},
                    label="Title",
                    value=title,
                ),
                dmc.TextInput(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "description",
                    },
                    label="Description",
                    value=description,
                ),
            ]
        )


class HightlightCard(Card):
    title = "Highlight"
    description = "This card shows a highlight of a given dataset"
    icon = "mdi:file-document-edit"

    def render(self):
        column = self.settings.get("column", "Age")
        aggregation = self.settings.get("aggregation", "count")
        filter_value = self.settings.get("column-filter", None)
        filtered_data = data
        if filter_value is not None:
            if filtered_data[column].dtype in ["object", "string", "bool", "category"]:
                filtered_data = filtered_data[filtered_data[column].isin(filter_value)]
            else:
                filter_value = [float(x) for x in filter_value]
                filtered_data = filtered_data[
                    (filtered_data[column] >= filter_value[0])
                    & (filtered_data[column] <= filter_value[1])
                ]
        highlight_value = filtered_data[column].agg(aggregation)
        if isinstance(highlight_value, float):
            highlight_value = round(highlight_value, 2)
        icon = self.settings.get("icon", "mdi:star")
        suffix = self.settings.get("suffix", "Suffix")
        return (
            dmc.Card(
                [
                    dmc.Group(
                        children=[
                            dmc.Text(
                                suffix,
                                c="dimmed",
                                fz="14px",
                                fw=400,
                            )
                        ],
                        # justify="flex-end",
                    ),
                    dmc.Group(
                        children=[
                            dmc.Text(highlight_value, fz="40px", fw=600, c="blue"),
                            dmc.ThemeIcon(
                                DashIconify(icon=icon, width=50),
                                size=50,
                                radius="xl",
                                variant="light",
                            ),
                        ],
                        justify="space-between",
                        wrap="nowrap",
                    ),
                ],
                style={"height": "100%"},
                withBorder=True,
                shadow="xs",
            ),
        )

    def render_settings(self):
        column = self.settings.get("column", "Age")
        column_filter = self.settings.get("column-filter", None)
        aggregation = self.settings.get("aggregation", "count")
        suffix = self.settings.get("suffix", "Suffix")
        icon = self.settings.get("icon", "mdi:star")
        print(column_filter)
        return dmc.Stack(
            [
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "column",
                    },
                    label="Column",
                    value=column,
                    searchable=True,
                    data=[
                        {"label": column, "value": column} for column in data.columns
                    ],
                ),
                html.Div(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "container": "column-filter",
                    },
                    children=generate_filter(
                        data[column],
                        {"type": "card-settings", "id": self.id, "setting": "column"},
                        default_value=column_filter,
                    ),
                ),
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "aggregation",
                    },
                    label="Aggregation",
                    value=aggregation,
                    searchable=True,
                    data=[
                        {"label": "Count", "value": "count"},
                        {"label": "Mean", "value": "mean"},
                        {"label": "Sum", "value": "sum"},
                        {"label": "Min", "value": "min"},
                        {"label": "Max", "value": "max"},
                    ],
                ),
                dmc.TextInput(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "suffix",
                    },
                    label="Suffix",
                    value=suffix,
                ),
                dmc.TextInput(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "icon",
                    },
                    label="Icon",
                    value=icon,
                ),
                html.A(
                    "Icon list",
                    href="https://icon-sets.iconify.design/mdi/?keyword=mdi",
                    target="_blank",
                ),
            ]
        )
    @callback(
        Output(
            {"type": "card-settings", "id": MATCH, "container": "column-filter"}, "children"
        ),
        Input({"type": "card-settings", "id": MATCH, "setting": "column"}, "value"),
    )
    def update_filter_x(value):
        """If the column is categorical, show a dropdown to filter the data
        else if data is numeric, show a slider to filter the data"""
        column = data[value]
        # get the input id
        ctx = callback_context
        if not ctx.triggered_id:
            return no_update
        input_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
        return generate_filter(column, input_id)


@callback(
    Output({"type": "card-control", "sub-type": "figure", "id": ALL}, "figure"),
    Input("mantine-provider", "forceColorScheme"),
    State({"type": "card-control", "sub-type": "figure", "id": ALL}, "id"),
)
def update_color_scheme(color_scheme, figure_ids):
    template = (
        pio.templates["mantine_light"]
        if color_scheme == "light"
        else pio.templates["mantine_dark"]
    )
    patched_figures = []
    for _ in figure_ids:
        patched_figure = Patch()
        patched_figure["layout"]["template"] = template
        patched_figures.append(patched_figure)
    return patched_figures


canvas = CardCanvas(settings)
canvas.card_manager.register_card_class(HistogramCard)
canvas.card_manager.register_card_class(HeatMap)
canvas.card_manager.register_card_class(ViolinCard)
canvas.card_manager.register_card_class(HightlightCard)
server = canvas.app.server

if __name__ == "__main__":
    canvas.app.run_server(debug=True)
