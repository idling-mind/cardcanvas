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

from data import nea_data as data

settings = {
    "title": "The National Endowment for the Arts Creative Writing Fellowships",
    "subtitle": "Writers sponsored by NEA fellowships from the organization’s founding in 1965 to 2024",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/3/3b/National_Endowment_for_the_Arts_%28NEA%29_Logo_2018_Square_on_Black.svg",
    "start_config": json.loads((Path(__file__).parent / "layout.json").read_text()),
    "grid_compact_type": "vertical",
    "grid_row_height": 120,
    "show_global_settings": False,
}


class HistogramCard(Card):
    title = "Histogram"
    description = "This card shows a histogram of a given dataset"
    icon = "mdi:file-document-edit"
    grid_settings = {"w": 4, "h": 2, "minW": 4, "minH": 2}
    debug = True

    def render(self):
        column = self.settings.get("column", None)
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
        column = self.settings.get("column", None)
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
                style={"maxHeight": "250px", "overflowY": "auto"},
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
        x = self.settings.get("x", None)
        x_filter = self.settings.get("x-filter", None)
        y = self.settings.get("y", None)
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
        x = self.settings.get("x", None)
        y = self.settings.get("y", None)
        x_filter = self.settings.get("x-filter", None)
        y_filter = self.settings.get("y-filter", None)
        nbinsx = self.settings.get("nbinsx", 20)
        nbinsy = self.settings.get("nbinsy", 20)
        title = self.settings.get("title", "Heatmap")
        description = self.settings.get("description", "Heatmap description")

        x_filter_children = None
        if x is not None:
            x_filter_children = generate_filter(
                data[x],
                {"type": "card-settings", "id": self.id, "setting": "x"},
                default_value=x_filter,
            )
        y_filter_children = None
        if y is not None:
            y_filter_children = generate_filter(
                data[y],
                {"type": "card-settings", "id": self.id, "setting": "y"},
                default_value=y_filter,
            )

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
                    children=x_filter_children,
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
                    children=y_filter_children,
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
        if value is None:
            return no_update
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
        if value is None:
            return no_update
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
        x = self.settings.get("x", None)
        y = self.settings.get("y", None)
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
        x = self.settings.get("x", None)
        y = self.settings.get("y", None)
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


class BarChartCard(Card):
    title = "Bar Chart"
    description = "This card shows a bar chart of a given dataset"
    icon = "mdi:file-document-edit"
    grid_settings = {"w": 4, "h": 2, "minW": 4, "minH": 2}

    def render(self):
        x = self.settings.get("x", None)
        x_filter = self.settings.get("x-filter", None)
        y = self.settings.get("y", None)
        y_filter = self.settings.get("y-filter", None)
        color = self.settings.get("color", None)
        barmode = self.settings.get("barmode", "group")
        aggregation = self.settings.get("aggregation", "count")
        title = self.settings.get("title", "Bar Chart")
        description = self.settings.get("description", f"Bar chart of {y} by {x}")

        # apply filters
        filtered_data = data
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
        if color is None:
            if x and y:
                grouped_data = (
                    filtered_data.groupby(x)[y].agg(aggregation).reset_index()
                )
            else:
                grouped_data = pd.DataFrame()
        else:
            if x and color and y:
                grouped_data = (
                    filtered_data.groupby([x, color])[y].agg(aggregation).reset_index()
                )
            else:
                grouped_data = pd.DataFrame()

        fig = px.bar(
            template="mantine_light",
            data_frame=grouped_data,
            x=x,
            y=y,
            color=color,
            barmode=barmode
        )

        fig.update_layout(margin=dict(l=0, r=0, t=15, b=0))
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
        x = self.settings.get("x", None)
        x_filter = self.settings.get("x-filter", None)
        y = self.settings.get("y", None)
        y_filter = self.settings.get("y-filter", None)
        color = self.settings.get("color", None)
        barmode = self.settings.get("barmode", "group")
        aggregation = self.settings.get("aggregation", "sum")
        title = self.settings.get("title", "Bar Chart")
        description = self.settings.get("description", "Bar chart description")

        x_filter_children = None
        if x is not None:
            x_filter_children = generate_filter(
                data[x],
                {"type": "card-settings", "id": self.id, "setting": "x"},
                default_value=x_filter,
            )

        y_filter_children = None
        if y is not None:
            y_filter_children = generate_filter(
                data[y],
                {"type": "card-settings", "id": self.id, "setting": "y"},
                default_value=y_filter,
            )
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
                html.Div(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "container": "x-filter",
                    },
                    children=x_filter_children,
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
                    data=[
                        {"label": column, "value": column} for column in data.columns
                    ],
                ),
                html.Div(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "container": "y-filter",
                    },
                    children=y_filter_children,
                ),
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "aggregation",
                    },
                    label="Aggregation",
                    value=aggregation,
                    data=[
                        {"label": "Sum", "value": "sum"},
                        {"label": "Mean", "value": "mean"},
                        {"label": "Count", "value": "count"},
                        {"label": "Min", "value": "min"},
                        {"label": "Max", "value": "max"},
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
                        {"label": column, "value": column} for column in data.columns
                    ],
                ),
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "barmode",
                    },
                    label="Bar Mode",
                    value=barmode,
                    data=[
                        {"label": "Grouped", "value": "group"},
                        {"label": "Stacked", "value": "stack"},
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


class TopNBarChartCard(Card):
    title = "Top Bar Chart"
    description = "Show the top n entries for a given column"
    icon = "mdi:file-document-edit"
    grid_settings = {"w": 4, "h": 2, "minW": 4, "minH": 2}

    def render(self):
        column = self.settings.get("column", None)
        column_filter = self.settings.get("column-filter", None)
        n = self.settings.get("n", 10)
        title = self.settings.get("title", "Top N Bar Chart")
        description = self.settings.get("description", f"Top {n} entries of {column}")

        filtered_data = data
        if column_filter is not None:
            if filtered_data[column].dtype in ["object", "string", "bool", "category"]:
                filtered_data = filtered_data[filtered_data[column].isin(column_filter)]
            else:
                column_filter = [float(x) for x in column_filter]
                filtered_data = filtered_data[
                    (filtered_data[column] >= column_filter[0])
                    & (filtered_data[column] <= column_filter[1])
                ]

        top_n = filtered_data[column].value_counts().head(n).reset_index()
        top_n.columns = [column, "count"]
        fig = px.bar(
            top_n,
            x=column,
            y="count",
            template="mantine_light",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=15, b=0))
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
        column = self.settings.get("column", None)
        column_filter = self.settings.get("column-filter", None)
        n = self.settings.get("n", 10)
        title = self.settings.get("title", "Top N Bar Chart")
        description = self.settings.get("description", "Top N Bar Chart description")

        filter_children = None
        if column is not None:
            filter_children = generate_filter(
                data[column],
                {"type": "card-settings", "id": self.id, "setting": "column"},
                default_value=column_filter,
            )

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
                    children=filter_children,
                ),
                dmc.NumberInput(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "n",
                    },
                    label="Number of entries",
                    value=n,
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


class HightlightCard(Card):
    title = "Highlight"
    description = "This card shows a highlight of a given dataset"
    icon = "mdi:file-document-edit"

    def render(self):
        column = self.settings.get("column", None)
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
        column = self.settings.get("column", None)
        column_filter = self.settings.get("column-filter", None)
        aggregation = self.settings.get("aggregation", "count")
        suffix = self.settings.get("suffix", "Suffix")
        icon = self.settings.get("icon", "mdi:star")

        filter_children = None
        if column is not None:
            filter_children = generate_filter(
                data[column],
                {"type": "card-settings", "id": self.id, "setting": "column"},
                default_value=column_filter,
            )
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
                    children=filter_children,
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
                        {"label": "Count-Unique", "value": "nunique"},
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
        if value is None:
            return no_update
        column = data[value]
        # get the input id
        ctx = callback_context
        if not ctx.triggered_id:
            return no_update
        input_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
        return generate_filter(column, input_id)

class MarkdownCard(Card):
    title = "Markdown"
    description = "This card shows a markdown content"
    icon = "mdi:file-document-edit"
    grid_settings = {"w": 4, "h": 2, "minW": 4, "minH": 2}

    def render(self):
        markdown = self.settings.get("markdown", "### Markdown")
        return dmc.Card(
            dmc.ScrollArea(
                [
                    dcc.Markdown(markdown),
                ],
            ),
            style={"height": "100%"},
            withBorder=True,
        )

    def render_settings(self):
        markdown = self.settings.get("markdown", "### Markdown")
        return dmc.Stack(
            [
                dmc.Textarea(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "markdown",
                    },
                    label="Markdown",
                    value=markdown,
                    autosize=True,
                ),
            ]
        )

class MapCard(Card):
    title = "Map"
    description = "This card shows a map of a given dataset"
    icon = "mdi:map"
    grid_settings = {"w": 4, "h": 2, "minW": 4, "minH": 2}

    def render(self):
        location = self.settings.get("location", None)
        location_mode = self.settings.get("location_mode", "country names")
        value = self.settings.get("value", None)
        aggregation = self.settings.get("aggregation", "sum")
        title = self.settings.get("title", "Map")
        description = self.settings.get(
            "description", f"Map of {location} aggregated by {value}"
        )

        if location and value:
            aggregated_data = (
                data.groupby(location)[value].agg(aggregation).reset_index()
            )
        else:
            aggregated_data = pd.DataFrame()

        figure = px.choropleth(
            aggregated_data,
            locations=location,
            locationmode=location_mode,
            color=value,
            hover_name=location,
            color_continuous_scale=px.colors.sequential.Plasma,
            template="mantine_light",
        )

        if location_mode == "USA-states":
            figure.update_geos(fitbounds="locations", visible=False)
        else:
            figure.update_geos(projection_type="natural earth")

        figure.update_layout(margin=dict(l=0, r=0, t=15, b=0))
        return dmc.Card(
            [
                dmc.Text(title, fz="30px", fw=600, c="blue"),
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
        location = self.settings.get("location", None)
        location_mode = self.settings.get("location_mode", "country names")
        value = self.settings.get("value", None)
        aggregation = self.settings.get("aggregation", "sum")
        title = self.settings.get("title", "Map")
        description = self.settings.get("description", "Map description")
        return dmc.Stack(
            [
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "location_mode",
                    },
                    label="Location Mode",
                    value=location_mode,
                    data=[
                        {"label": "Country Names", "value": "country names"},
                        {"label": "ISO-3", "value": "ISO-3"},
                        {"label": "USA-states", "value": "USA-states"},
                    ],
                ),
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "location",
                    },
                    label="Location",
                    value=location,
                    searchable=True,
                    data=[
                        {"label": column, "value": column} for column in data.columns
                    ],
                ),
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "value",
                    },
                    label="Value",
                    value=value,
                    searchable=True,
                    data=[
                        {"label": column, "value": column} for column in data.columns
                    ],
                ),
                dmc.Select(
                    id={
                        "type": "card-settings",
                        "id": self.id,
                        "setting": "aggregation",
                    },
                    label="Aggregation",
                    value=aggregation,
                    data=[
                        {"label": "Sum", "value": "sum"},
                        {"label": "Mean", "value": "mean"},
                        {"label": "Count", "value": "count"},
                        {"label": "Count-Unique", "value": "nunique"},
                        {"label": "Min", "value": "min"},
                        {"label": "Max", "value": "max"},
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
canvas.card_manager.register_card_class(BarChartCard)
canvas.card_manager.register_card_class(MarkdownCard)
canvas.card_manager.register_card_class(TopNBarChartCard)
canvas.card_manager.register_card_class(MapCard)
server = canvas.app.server

if __name__ == "__main__":
    canvas.app.run_server(debug=True)
