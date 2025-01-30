import base64
import copy
import json
import logging
from typing import Any
from uuid import uuid4

import dash_mantine_components as dmc
from dash import (
    ALL,
    MATCH,
    Dash,
    Input,
    Output,
    State,
    ctx,
    dcc,
    html,
    no_update,
    _dash_renderer,
)
from dash_snap_grid import ResponsiveGrid
from dash_iconify import DashIconify

from . import ui, helpers
from .card_manager import CardManager
from .settings import DEFAULT_THEME

_dash_renderer._set_react_version("18.2.0")
dmc.add_figure_templates()


class CardCanvas:
    def __init__(
        self, settings: dict[str, Any], dash_options: dict[str, Any] | None = None
    ):
        self.settings = settings
        self.card_manager = CardManager()
        self.dash_options = dash_options or {}

    def run(self):
        self.app.run_server(debug=True)

    @property
    def app(self):
        if not hasattr(self, "_app"):
            self._app = self._create_app(self.settings)
        return self._app

    def _create_app(self, settings: dict[str, Any]) -> Dash:
        title = settings.get("title", "Card Canvas")
        subtitle = settings.get("subtitle", None)
        title_component = settings.get("title_component", None)
        footer_component = settings.get("footer_component", None)
        start_config = settings.get("start_config", {})
        start_card_config = start_config.get("card_config", {})
        start_card_layout = start_config.get("card_layouts", {"lg": []})
        start_global_settings = start_config.get("global_settings", {})
        logo = settings.get("logo", None)
        theme = settings.get("theme", DEFAULT_THEME)

        show_global_settings = settings.get("show_global_settings", True)
        app = Dash(
            __name__,
            **self.dash_options,
            external_stylesheets=[dmc.styles.NOTIFICATIONS, dmc.styles.CHARTS],
            suppress_callback_exceptions=True,
        )
        app.title = f"{title}: {subtitle}" if subtitle else title

        title_layout = dmc.Group(
            [
                title_component
                if title_component
                else ui.get_title_layout(title, subtitle=subtitle, logo=logo),
                dmc.ActionIcon(
                    id="open-main-menu",
                    children=DashIconify(icon="mdi:menu"),
                    variant="outline",
                ),
            ],
            justify="space-between",
            p="xs",
        )

        main_buttons = dmc.Collapse(
            id="main-menu-collapse",
            children=[ui.main_buttons(global_settings=show_global_settings)],
            opened=True,
            style={"position": "sticky", "top": 0, "zIndex": 10},
        )

        stage_layout = dmc.Container(
            fluid=True,
            children=[
                title_layout,
                main_buttons,
                ResponsiveGrid(
                    id="card-grid",
                    children=[],
                    cols={"lg": 18, "md": 12, "sm": 6, "xs": 4, "xxs": 2},
                    rowHeight=settings.get("grid_row_height", 50),
                    compactType=settings.get("grid_compact_type", None),
                    draggableCancel=".no-drag *",
                    isDroppable=True,
                    layouts={"lg": []},
                    width=100,
                ),
            ],
        )

        invisible_controls = html.Div(
            children=[
                dcc.Store(id="cardcanvas-main-store", storage_type="local"),
                dcc.Store(
                    id="cardcanvas-config-store",
                    storage_type="memory",
                ),
                dcc.Store(
                    id="cardcanvas-layout-store",
                    storage_type="memory",
                ),
                dcc.Store(
                    id="cardcanvas-global-store",
                    storage_type="memory",
                ),
                dcc.Store(
                    id="cardcanvas-config-store-current",
                    storage_type="memory",
                ),
                dcc.Store(
                    id="cardcanvas-layout-store-current",
                    storage_type="memory",
                ),
                dcc.Store(
                    id="cardcanvas-global-store-current",
                    storage_type="memory",
                ),
                dcc.Download(id="download-layout-data"),
                dmc.NotificationProvider(),
                html.Div(id="notification-container"),
            ],
        )

        settings_layout = dmc.Drawer(
            id="settings-layout",
            padding="md",
            closeOnClickOutside=False,
            withOverlay=False,
            position="right",
            lockScroll=False,
        )

        main_components = [stage_layout, settings_layout, invisible_controls]
        if footer_component:
            main_components.append(footer_component)

        app.layout = dmc.MantineProvider(
            children=main_components,
            theme=theme,
            id="mantine-provider",
            forceColorScheme="light",
        )

        @app.callback(
            Output("cardcanvas-config-store", "data"),
            Output("cardcanvas-layout-store", "data"),
            Output("cardcanvas-global-store", "data"),
            Input(app.layout, "layout"),
            State("cardcanvas-main-store", "data"),
        )
        def load_layout(layout, main_store):
            if not main_store:
                main_store = {}

            card_config = main_store.get("card_config", start_card_config)
            card_layouts = main_store.get("card_layouts", start_card_layout)
            global_settings = main_store.get("global_settings", {})
            return card_config, card_layouts, global_settings

        @app.callback(
            Output("card-grid", "children"),
            Output("card-grid", "layouts"),
            Output("cardcanvas-config-store-current", "data"),
            Output("cardcanvas-layout-store-current", "data"),
            Output("cardcanvas-global-store-current", "data"),
            Input("cardcanvas-config-store", "data"),
            Input("cardcanvas-layout-store", "data"),
            Input("cardcanvas-global-store", "data"),
            State("cardcanvas-config-store-current", "data"),
            State("cardcanvas-layout-store-current", "data"),
            State("cardcanvas-global-store-current", "data"),
            State("card-grid", "layouts"),
            prevent_initial_call=True,
        )
        def load_cards(
            card_config,
            card_layout_store,
            global_settings,
            current_config,
            current_layout,
            global_settings_current,
            layout,
        ):
            if helpers.compare_dicts(
                card_config, current_config
            ) and helpers.compare_dicts(global_settings, global_settings_current):
                new_children = no_update
            else:
                new_children = self.card_manager.render(
                    card_config,
                    global_settings=global_settings,
                    debug=self.app.server.debug,
                )
            if helpers.compare_dicts(
                card_layout_store, current_layout
            ) and helpers.compare_dicts(layout, current_layout):
                new_layout = no_update
            else:
                new_layout = card_layout_store
            return (
                new_children,
                new_layout,
                card_config,
                card_layout_store,
                global_settings,
            )

        @app.callback(
            Output("cardcanvas-main-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("notification-container", "children"),
            Input("save-layout", "n_clicks"),
            State("card-grid", "layouts"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-global-store", "data"),
            prevent_initial_call=True,
        )
        def save_reset_cards(nclicks, card_layouts, card_config, global_settings):
            if not nclicks:
                return no_update, no_update, no_update
            return (
                {
                    "card_layouts": card_layouts,
                    "card_config": card_config,
                    "global_settings": global_settings,
                },
                # This is required since there may be changes in the layout which
                # are not reflected in the cardcanvas_layout_store
                card_layouts,
                dmc.Notification(
                    title="Layout Saved",
                    message="The layout has been saved",
                    color="teal",
                    action="show",
                ),
            )

        @app.callback(
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-global-store", "data", allow_duplicate=True),
            Output("notification-container", "children", allow_duplicate=True),
            Input("restore-layout", "n_clicks"),
            State("cardcanvas-main-store", "data"),
            prevent_initial_call=True,
        )
        def reset_layouts(nclicks, main_store):
            if not nclicks or not main_store or not isinstance(main_store, dict):
                return no_update, no_update, no_update
            return (
                main_store.get("card_layouts", start_card_layout),
                main_store.get("card_config", start_card_config),
                main_store.get("global_settings", start_global_settings),
                dmc.Notification(
                    title="Layout Reset",
                    message="The layout has been reset to the last saved state",
                    color="orange",
                    action="show",
                ),
            )

        @app.callback(
            Output("settings-layout", "opened"),
            Output("settings-layout", "children"),
            Input("open-global-settings", "n_clicks"),
            State("cardcanvas-global-store", "data"),
            prevent_initial_call=True,
        )
        def open_settings(nclicks, global_settings):
            children = [
                dmc.Title("Global Settings", order=2),
                dmc.Text(
                    "These are the global settings. These apply to all the cards",
                    variant="muted",
                ),
            ]
            if show_global_settings and self.card_manager.global_settings_class:
                global_settings = self.card_manager.global_settings_class(
                    global_settings
                )
                children.extend(
                    [
                        global_settings.render_settings(),
                        dmc.Button("OK", id="global-settings-ok"),
                    ]
                )
            children = [dmc.Stack(children)]
            return True, children

        @app.callback(
            Output("cardcanvas-global-store", "data", allow_duplicate=True),
            Output("settings-layout", "opened", allow_duplicate=True),
            Input("global-settings-ok", "n_clicks"),
            State({"type": "global-settings", "setting": ALL}, "id"),
            State({"type": "global-settings", "setting": ALL}, "value"),
            prevent_initial_call=True,
        )
        def save_global_settings(nclicks, ids, values):
            if not nclicks or not ctx.triggered:
                return no_update, no_update
            global_settings = {}
            for idx, value in zip(ids, values):
                setting = idx.get("setting")
                global_settings[setting] = value
            return global_settings, False

        @app.callback(
            Output("settings-layout", "opened", allow_duplicate=True),
            Output("settings-layout", "children", allow_duplicate=True),
            Input("add-cards", "n_clicks"),
            prevent_initial_call=True,
        )
        def add_cards(nclicks):
            children = [
                dmc.Stack(
                    [
                        dmc.Title("Add Cards", order=2),
                        dmc.Text(
                            "These are the cards you can add to the dashboard."
                            " Drag and drop them on the grid where you want them to be"
                            " displayed. Configure them by clicking on the settings icon.",
                            variant="muted",
                        ),
                        dmc.Stack(
                            [
                                ui.render_card_preview(card_class)
                                for card_class in self.card_manager.card_classes.values()
                            ]
                        ),
                    ]
                )
            ]
            return True, children

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Input("card-grid", "droppedItem"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-layout-store", "data"),
            prevent_initial_call=True,
        )
        def add_new_card(dropped_item, card_config, card_layouts):
            if not dropped_item:
                return no_update, no_update
            card_id = str(uuid4())
            new_layout_item = {
                "i": card_id,
                "x": dropped_item["x"],
                "y": dropped_item["y"],
                "w": dropped_item["w"],
                "h": dropped_item["h"],
            }
            # dropped_item["i"] returns the id of dropped object. In this case, it is the card class.
            card_class = dropped_item["i"]
            card_config[card_id] = {"card_class": card_class, "settings": {}}
            card_class_obj = self.card_manager.card_classes.get(card_class)
            if (
                card_class_obj
                and hasattr(card_class_obj, "grid_settings")
                and isinstance(card_class_obj.grid_settings, dict)
            ):
                new_layout_item.update(card_class_obj.grid_settings)
            if not card_layouts:
                card_layouts = {"lg": []}
            for key in card_layouts.keys():
                card_layouts[key].append(new_layout_item)
            return card_config, card_layouts

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Input({"type": "card-duplicate", "index": ALL}, "n_clicks"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-layout-store", "data"),
            State("card-grid", "layout"),
            prevent_initial_call=True,
        )
        def duplicate_card(nclicks, card_config, card_layouts, card_layout):
            if not card_config:
                return no_update, no_update
            if not any(nclicks) or not ctx.triggered:
                return no_update, no_update
            if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
                return no_update, no_update
            card_id = ctx.triggered_id.get("index")
            new_card_id = str(uuid4())
            new_card_layout = copy.deepcopy(
                next((item for item in card_layout if item["i"] == card_id))
            )
            new_card = copy.deepcopy(card_config.get(card_id, None))
            new_card["id"] = new_card_id
            new_card_layout["i"] = new_card_id
            card_config[new_card_id] = new_card
            for key in card_layouts.keys():
                card_layouts[key].append(new_card_layout)
            return card_config, card_layouts

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Input({"type": "card-delete", "index": ALL}, "n_clicks"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-layout-store", "data"),
            prevent_initial_call=True,
        )
        def delete_card(nclicks, card_config, card_layouts):
            if not card_config:
                return no_update, no_update
            if not any(nclicks) or not ctx.triggered:
                return no_update, no_update
            if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
                return no_update, no_update
            card_id = ctx.triggered_id.get("index")
            card_config.pop(card_id, None)
            for key in card_layouts.keys():
                card_layouts[key] = [
                    item for item in card_layouts[key] if item["i"] != card_id
                ]
            return card_config, card_layouts

        @app.callback(
            Output("settings-layout", "children", allow_duplicate=True),
            Output("settings-layout", "opened", allow_duplicate=True),
            Input({"type": "card-settings", "index": ALL}, "n_clicks"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-global-store", "data"),
            prevent_initial_call=True,
        )
        def open_card_settings(nclicks, card_config, global_settings):
            if not any(nclicks) or not ctx.triggered or not ctx.triggered_id:
                return no_update, no_update
            if not card_config:
                card_config = start_card_config
            card_id = ctx.triggered_id.get("index")
            card_objects = self.card_manager.card_objects(card_config, global_settings)
            if card_id not in card_objects:
                return dmc.Alert(
                    f"Card with id: {card_id} not found", color="red"
                ), True
            card = card_objects[card_id]
            return dmc.Stack(
                [
                    dmc.Stack(
                        [
                            dmc.Text(
                                card.title, fw="600", size="lg", c="primary", mb=0
                            ),
                            dmc.Text(
                                f"Card ID: {card.id}",
                                fw="600",
                                size="sm",
                                c="gray",
                            ),
                        ],
                        gap=2,
                    ),
                    card.render_settings(),
                    dmc.Button(
                        "OK",
                        id="card-settings-ok",
                    ),
                ]
            ), True

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("settings-layout", "opened", allow_duplicate=True),
            Input("card-settings-ok", "n_clicks"),
            State({"type": "card-settings", "id": ALL, "setting": ALL}, "value"),
            State({"type": "card-settings", "id": ALL, "setting": ALL}, "id"),
            State("cardcanvas-config-store", "data"),
            prevent_initial_call=True,
        )
        def save_card_settings(nclicks, values, ids, card_config):
            if not nclicks or not ctx.triggered:
                return no_update, no_update
            for idx, val in zip(ids, values):
                card_id = idx.get("id")
                setting = idx.get("setting")
                if card_id not in card_config:
                    continue
                card_config[card_id]["settings"][setting] = val
            return card_config, False

        @app.callback(
            Output("card-grid", "isDraggable"),
            Output("card-grid", "isResizable"),
            Output({"type": "card-menu", "index": ALL}, "style"),
            Input({"type": "card-menu", "index": ALL}, "id"),
            Input("edit-layout", "checked"),
            prevent_initial_call=True,
        )
        def toggle_edit_mode(ids, checked):
            if checked:
                return True, True, [{"display": "block"}] * len(ids)
            return False, False, [{"display": "none"}] * len(ids)

        @app.callback(
            Output({"type": "card-content", "index": MATCH}, "children"),
            Output({"type": "card-interval", "index": MATCH}, "interval"),
            Input({"type": "card-interval", "index": MATCH}, "n_intervals"),
            State({"type": "card-interval", "index": MATCH}, "interval"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-global-store", "data"),
        )
        def update_card(n_intervals, interval, cards_config, global_settings):
            if not ctx.triggered_id or not cards_config:
                return no_update
            card_objects = self.card_manager.card_objects(cards_config, global_settings)
            card_id = ctx.triggered_id.get("index")
            card = card_objects[card_id]
            for card in card_objects.values():
                card.debug = self.app.server.debug
            return card.render(), card.interval

        @app.callback(
            Output("download-layout-data", "data"),
            Input("download-layout", "n_clicks"),
            State("cardcanvas-main-store", "data"),
            prevent_initial_call=True,
        )
        def download_layout(n_clicks, main_store):
            if not n_clicks or not main_store:
                return no_update
            return dict(
                content=json.dumps(main_store), filename="layout.json", type="json"
            )

        @app.callback(
            Output("cardcanvas-main-store", "data", allow_duplicate=True),
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Input("upload-layout", "contents"),
            prevent_initial_call=True,
        )
        def upload_layout(contents):
            if not contents:
                return no_update
            try:
                content_type, content_string = contents.split(",")
                decoded = base64.b64decode(content_string)
                content = decoded.decode("utf-8")
                data = json.loads(content)
                return (
                    data,
                    data.get("card_config", start_card_config),
                    data.get("card_layouts", start_card_layout),
                )
            except Exception as e:
                logging.error(e)
            return {}

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("cardcanvas-global-store", "data", allow_duplicate=True),
            Output("notification-container", "children", allow_duplicate=True),
            Input("clear-layout", "n_clicks"),
            prevent_initial_call=True,
        )
        def clear_layout(n_clicks):
            if not n_clicks:
                return no_update, no_update, no_update, no_update
            return (
                {},
                {},
                {},
                dmc.Notification(
                    title="Layout Cleared",
                    message=(
                        "The layout has been cleared."
                        " Click on save to save the changes."
                        " Click on restore to restore the layout.",
                    ),
                    color="red",
                    action="show",
                ),
            )

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("notification-container", "children", allow_duplicate=True),
            Input("reset-layout", "n_clicks"),
            prevent_initial_call=True,
        )
        def reset_layout(n_clicks):
            if not n_clicks:
                return no_update, no_update, no_update
            return (
                start_card_config,
                start_card_layout,
                dmc.Notification(
                    title="Layout Reset",
                    message=(
                        "The layout has been reset to default layout."
                        " Click on save to save the changes."
                        " Click on restore to restore the layout.",
                    ),
                    color="red",
                    action="show",
                ),
            )

        @app.callback(
            Output("main-menu-collapse", "opened"),
            Input("open-main-menu", "n_clicks"),
            State("main-menu-collapse", "opened"),
            prevent_initial_call=True,
        )
        def open_main_menu(n_clicks, status):
            return not status

        @app.callback(
            Output("mantine-provider", "forceColorScheme"),
            Input("color-scheme-toggle", "n_clicks"),
            State("mantine-provider", "forceColorScheme"),
            prevent_initial_call=True,
        )
        def switch_theme(_, theme):
            return "dark" if theme == "light" else "light"

        return app
