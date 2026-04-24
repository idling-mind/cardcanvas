import base64
import copy
import json
import logging
import random
import urllib.parse
from typing import Any
from uuid import uuid4

import dash_mantine_components as dmc
from flask import request
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
)
from dash_snap_grid import ResponsiveGrid
from dash_iconify import DashIconify

from . import ui
from .card_manager import CardManager
from .settings import DEFAULT_THEME

dmc.add_figure_templates()

SHARE_QUERY_KEY = "ccs"
SHARE_PAYLOAD_VERSION = 1


def _build_card_share_payload(
    card_id: str,
    card_config: dict[str, Any] | None,
    card_layouts: dict[str, Any] | None,
    global_settings: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not card_config or card_id not in card_config:
        return None
    selected_card = copy.deepcopy(card_config.get(card_id))
    if not isinstance(selected_card, dict) or not selected_card.get("card_class"):
        return None

    selected_layouts: dict[str, list[dict[str, Any]]] = {}
    for breakpoint, layout_items in (card_layouts or {}).items():
        if not isinstance(layout_items, list):
            continue
        selected_items = []
        for item in layout_items:
            if isinstance(item, dict) and item.get("i") == card_id:
                selected_items.append(copy.deepcopy(item))
        if selected_items:
            selected_layouts[breakpoint] = selected_items

    if not selected_layouts:
        selected_layouts = {"lg": []}

    return {
        "v": SHARE_PAYLOAD_VERSION,
        "card_id": card_id,
        "card": selected_card,
        "layouts": selected_layouts,
        "global_settings": copy.deepcopy(global_settings or {}),
    }


def _share_payload_to_search(payload: dict[str, Any]) -> str:
    compact_payload = json.dumps(payload, separators=(",", ":"))
    query = urllib.parse.urlencode({SHARE_QUERY_KEY: compact_payload})
    return f"?{query}"


def _search_to_share_payload(search: str | None) -> dict[str, Any] | None:
    if not search:
        return None
    query = search[1:] if search.startswith("?") else search
    parsed = urllib.parse.parse_qs(query)
    values = parsed.get(SHARE_QUERY_KEY)
    if not values:
        return None
    try:
        payload = json.loads(values[-1])
    except json.JSONDecodeError:
        logging.error("Unable to parse share payload from query string")
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _is_shared_search(search: str | None) -> bool:
    return _share_payload_to_state(_search_to_share_payload(search)) is not None


def _query_string_to_search(query_string: bytes | str | None) -> str | None:
    if not query_string:
        return None
    if isinstance(query_string, bytes):
        raw = query_string.decode("utf-8")
    else:
        raw = query_string
    if not raw:
        return None
    return f"?{raw}"


def _share_payload_to_state(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    if payload.get("v") != SHARE_PAYLOAD_VERSION:
        return None

    card_id = payload.get("card_id")
    card = payload.get("card")
    if not isinstance(card_id, str) or not isinstance(card, dict):
        return None
    if not card.get("card_class"):
        return None

    settings = card.get("settings", {})
    if not isinstance(settings, dict):
        settings = {}

    raw_layouts = payload.get("layouts", {})
    layouts: dict[str, list[dict[str, Any]]] = {}
    if isinstance(raw_layouts, dict):
        for breakpoint, layout_items in raw_layouts.items():
            if not isinstance(layout_items, list):
                continue
            filtered_items = []
            for item in layout_items:
                if isinstance(item, dict) and item.get("i") == card_id:
                    filtered_items.append(item)
            layouts[breakpoint] = filtered_items
    if not layouts:
        layouts = {"lg": []}

    global_settings = payload.get("global_settings", {})
    if not isinstance(global_settings, dict):
        global_settings = {}

    return {
        "card_config": {
            card_id: {
                "card_class": card["card_class"],
                "settings": settings,
            }
        },
        "card_layouts": layouts,
        "global_settings": global_settings,
    }


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

        def is_request_shared_mode() -> bool:
            try:
                return _is_shared_search(_query_string_to_search(request.query_string))
            except RuntimeError:
                # No request context during startup/background operations.
                return False

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

        background_color = settings.get("background_color", "light-dark(#eee, #222)")

        main_buttons = dmc.Collapse(
            id="main-menu-collapse",
            children=[ui.main_buttons(global_settings=show_global_settings)],
            opened=True,
            style={
                "position": "sticky",
                "top": 0,
                "zIndex": 10,
                "backgroundColor": background_color,
            },
        )
        loading_indicator = html.Div(
                dcc.Loading(
                id="cardcanvas-loading-anim",
                children=html.Div(id="cardcanvas-loading-trigger", style={"display": "none"}),
                custom_spinner=html.Span(className="loader")
            ),
        )

        def serve_layout():
            initial_shared_mode = is_request_shared_mode()
            hidden_style = {"display": "none"} if initial_shared_mode else {}

            stage_children = [
                loading_indicator,
                html.Div(
                    title_layout,
                    id="cardcanvas-title-wrapper",
                    style=hidden_style,
                ),
                html.Div(
                    main_buttons,
                    id="cardcanvas-toolbar-wrapper",
                    style=hidden_style,
                ),
                ResponsiveGrid(
                    id="card-grid",
                    children=[],
                    cols=settings.get(
                        "grid_cols",
                        {"xl": 24, "lg": 18, "md": 12, "sm": 6, "xs": 4, "xxs": 2},
                    ),
                    breakpoints=settings.get(
                        "grid_breakpoints",
                        {
                            "xl": 1920,
                            "lg": 1200,
                            "md": 1080,
                            "sm": 768,
                            "xs": 576,
                            "xxs": 480,
                        },
                    ),
                    rowHeight=settings.get("grid_row_height", 50),
                    compactType=settings.get("grid_compact_type", None),
                    draggableCancel=".no-drag *",
                    isDroppable=True,
                    layouts={"lg": []},
                    width=100,
                ),
                html.Div(
                    footer_component,
                    id="cardcanvas-footer-wrapper",
                    style=hidden_style,
                ),
            ]

            stage_layout = dmc.Container(
                id="cardcanvas-stage",
                fluid=True,
                children=stage_children,
                style={
                    "backgroundColor": background_color,
                    "minHeight": "100vh",
                    "display": "none",
                },
            )

            invisible_controls = html.Div(
                children=[
                    dcc.Location(id="cardcanvas-url", refresh=False),
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
                        id="cardcanvas-event-store",
                        storage_type="memory",
                    ),
                    dcc.Download(id="download-layout-data"),
                    dmc.NotificationContainer(id="notification-container"),
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

            return dmc.MantineProvider(
                children=main_components,
                theme=theme,
                id="mantine-provider",
                forceColorScheme="light",
            )

        app.layout = serve_layout

        @app.callback(
            Output("cardcanvas-config-store", "data"),
            Output("cardcanvas-layout-store", "data"),
            Output("cardcanvas-global-store", "data"),
            Output("cardcanvas-event-store", "data"),
            Input("cardcanvas-url", "pathname"),
            Input("cardcanvas-url", "search"),
            State("cardcanvas-main-store", "data"),
        )
        def load_layout(pathname, search, main_store):
            logging.debug("Callback load_layout called")
            if not main_store:
                main_store = {}

            shared_state = _share_payload_to_state(_search_to_share_payload(search))
            if shared_state:
                card_config = shared_state["card_config"]
                card_layouts = shared_state["card_layouts"]
                global_settings = shared_state["global_settings"]
            else:
                card_config = main_store.get("card_config", start_card_config)
                card_layouts = main_store.get("card_layouts", start_card_layout)
                global_settings = main_store.get("global_settings", start_global_settings)
            event = {
                "type": "re-render",
                "data": None,
            }
            return card_config, card_layouts, global_settings, event

        @app.callback(
            Output("cardcanvas-stage", "style"),
            Output("cardcanvas-title-wrapper", "style"),
            Output("cardcanvas-toolbar-wrapper", "style"),
            Output("cardcanvas-footer-wrapper", "style"),
            Input("cardcanvas-url", "search"),
        )
        def toggle_shared_mode_ui(search):
            stage_style = {
                "backgroundColor": background_color,
                "minHeight": "100vh",
                "display": "block",
            }
            if _is_shared_search(search):
                hidden_style = {"display": "none"}
                return stage_style, hidden_style, hidden_style, hidden_style
            visible_style: dict[str, Any] = {}
            return stage_style, visible_style, visible_style, visible_style

        @app.callback(
            Output("card-grid", "children"),
            Output("card-grid", "layouts"),
            Output(
                {"type": "card-content", "index": ALL}, "children", allow_duplicate=True
            ),
            Output("cardcanvas-loading-trigger", "children", allow_duplicate=True),
            Input("cardcanvas-event-store", "data"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-layout-store", "data"),
            State("cardcanvas-global-store", "data"),
            State("card-grid", "layouts"),
            State("card-grid", "children"),
            prevent_initial_call=True,
        )
        def load_cards(
            event,
            card_config_store,
            card_layout_store,
            global_settings,
            current_layout,
            current_children,
        ):
            logging.debug("Callback load_cards called")
            new_children = no_update
            new_layout = no_update
            updated_children = [no_update] * len(ctx.outputs_list[2])
            if event["type"] == "re-render":
                new_children = self.card_manager.render(
                    card_config_store,
                    global_settings=global_settings,
                    debug=self.app.server.debug,
                )
                new_layout = card_layout_store
                updated_children = [no_update] * len(ctx.outputs_list[2])
            elif event["type"] == "add-card":
                card_id = event["data"]["card_id"]
                card_objects = self.card_manager.card_objects(
                    card_config_store, global_settings
                )
                if card_id not in card_objects:
                    return no_update, no_update, no_update, no_update
                card = card_objects[card_id]
                new_child = card.render_container()
                new_children = current_children + [new_child]
                updated_children = [no_update] * len(ctx.outputs_list[2])
                for layout_key in card_layout_store.keys():
                    for layout_item in card_layout_store[layout_key]:
                        if layout_item["i"] == card_id:
                            current_layout[layout_key].append(layout_item)
                new_layout = current_layout
            elif event["type"] == "update-card":
                card_ids = event["data"]["card_ids"]
                card_objects = self.card_manager.card_objects(
                    card_config_store, global_settings
                )
                for idx, output in enumerate(ctx.outputs_list[2]):
                    card_id = output["id"]["index"]
                    if card_id in card_ids and card_id in card_objects:
                        card = card_objects[card_id]
                        updated_children[idx] = card.render()
            elif event["type"] == "delete-card":
                card_id = event["data"]["card_id"]
                new_children = [
                    child
                    for child in current_children
                    if child["props"]["id"] != card_id
                ]
            return (
                new_children,
                new_layout,
                updated_children,
                no_update,
            )

        @app.callback(
            Output("cardcanvas-main-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("notification-container", "sendNotifications"),
            Input("save-layout", "n_clicks"),
            State("card-grid", "layouts"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-global-store", "data"),
            prevent_initial_call=True,
        )
        def save_reset_cards(nclicks, card_layouts, card_config, global_settings):
            logging.debug("Callback save_reset_cards called")
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
                [
                    dict(
                        title="Layout Saved",
                        message="The layout has been saved",
                        color="teal",
                        action="show",
                    )
                ],
            )

        @app.callback(
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-global-store", "data", allow_duplicate=True),
            Output("notification-container", "sendNotifications", allow_duplicate=True),
            Output("cardcanvas-event-store", "data", allow_duplicate=True),
            Input("restore-layout", "n_clicks"),
            State("cardcanvas-main-store", "data"),
            prevent_initial_call=True,
        )
        def reset_layouts(nclicks, main_store):
            logging.debug("Callback reset_layouts called")
            if not nclicks or not main_store or not isinstance(main_store, dict):
                return no_update, no_update, no_update, no_update, no_update
            return (
                main_store.get("card_layouts", start_card_layout),
                main_store.get("card_config", start_card_config),
                main_store.get("global_settings", start_global_settings),
                [
                    dict(
                        title="Layout Reset",
                        message="The layout has been reset to the last saved state",
                        color="orange",
                        action="show",
                    )
                ],
                {
                    "type": "re-render",
                    "data": None,
                },
            )

        @app.callback(
            Output("settings-layout", "opened"),
            Output("settings-layout", "children"),
            Input("open-global-settings", "n_clicks"),
            State("cardcanvas-global-store", "data"),
            prevent_initial_call=True,
        )
        def open_settings(nclicks, global_settings):
            if not nclicks:
                return no_update, no_update
            logging.debug("Callback open_settings called")
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
            Output("cardcanvas-event-store", "data", allow_duplicate=True),
            Input("global-settings-ok", "n_clicks"),
            State({"type": "global-settings", "setting": ALL}, "id"),
            State({"type": "global-settings", "setting": ALL}, "value"),
            State({"type": "global-settings", "setting": ALL}, "checked"),
            prevent_initial_call=True,
        )
        def save_global_settings(nclicks, ids, values, checked_values):
            logging.debug("Callback save_global_settings called")
            if not nclicks or not ctx.triggered:
                return no_update, no_update, no_update
            global_settings = {}
            for idx, value, checked in zip(ids, values, checked_values):
                setting = idx.get("setting")
                if value is None and (checked in [True, False]):
                    value = checked
                global_settings[setting] = value
            event = {
                "type": "re-render",
                "data": None,
            }
            return global_settings, False, event

        @app.callback(
            Output("settings-layout", "opened", allow_duplicate=True),
            Output("settings-layout", "children", allow_duplicate=True),
            Input("add-cards", "n_clicks"),
            prevent_initial_call=True,
        )
        def add_cards(nclicks):
            logging.debug("Callback add_cards called")
            if not nclicks:
                return no_update, no_update
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
                        dmc.TextInput(
                            id="card-search", placeholder="Search cards", debounce=300
                        ),
                        dmc.Stack(
                            [
                                ui.render_card_preview(card_class)
                                for card_class in self.card_manager.card_classes.values()
                            ],
                            id="card-list",
                        ),
                    ]
                )
            ]
            return True, children

        @app.callback(
            Output("card-list", "children"),
            Input("card-search", "value"),
            prevent_initial_call=True,
        )
        def update_card_search(search_value):
            logging.debug("Callback update_card_search called")
            return [
                ui.render_card_preview(card_class)
                for card_class in self.card_manager.card_classes.values()
                if not search_value
                or search_value.lower() in card_class.title.lower()
                or search_value.lower() in card_class.description.lower()
            ]

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("cardcanvas-event-store", "data", allow_duplicate=True),
            Input("card-grid", "droppedItem"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-layout-store", "data"),
            prevent_initial_call=True,
        )
        def add_new_card(dropped_item, card_config, card_layouts):
            logging.debug("Callback add_new_card called")
            if not dropped_item:
                return no_update, no_update, no_update
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
            event = {
                "type": "add-card",
                "data": {"card_id": card_id, "card_class": card_class},
            }
            return card_config, card_layouts, event

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("cardcanvas-event-store", "data", allow_duplicate=True),
            Input({"type": "add-card", "index": ALL}, "n_clicks"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-layout-store", "data"),
            State("card-grid", "col"),
            prevent_initial_call=True,
        )
        def add_new_card_action_icon(nclicks, card_config, card_layouts, col_count):
            logging.debug("Callback add_new_card_action_icon called")
            if not nclicks or not any(nclicks) or not ctx.triggered:
                return no_update, no_update, no_update
            if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
                return no_update, no_update, no_update
            card_id = str(uuid4())
            new_layout_item = {
                "i": card_id,
                "x": random.randint(0, col_count - 1),
                "y": 10000,
                "w": 1,
                "h": 1,
            }
            card_class = ctx.triggered_id["index"]
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
            event = {
                "type": "add-card",
                "data": {"card_id": card_id, "card_class": card_class},
            }
            return card_config, card_layouts, event

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("cardcanvas-event-store", "data", allow_duplicate=True),
            Input({"type": "card-duplicate", "index": ALL}, "n_clicks"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-layout-store", "data"),
            State("card-grid", "layout"),
            prevent_initial_call=True,
        )
        def duplicate_card(nclicks, card_config, card_layouts, card_layout):
            logging.debug("Callback duplicate_card called")
            if not card_config:
                return no_update, no_update, no_update
            if not any(nclicks) or not ctx.triggered:
                return no_update, no_update, no_update
            if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
                return no_update, no_update, no_update
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
            event = {
                "type": "add-card",
                "data": {"card_id": new_card_id},
            }
            return card_config, card_layouts, event

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("cardcanvas-event-store", "data", allow_duplicate=True),
            Input({"type": "card-delete", "index": ALL}, "n_clicks"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-layout-store", "data"),
            prevent_initial_call=True,
        )
        def delete_card(nclicks, card_config, card_layouts):
            logging.debug("Callback delete_card called")
            if not card_config:
                return no_update, no_update, no_update
            if not any(nclicks) or not ctx.triggered:
                return no_update, no_update, no_update
            if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
                return no_update, no_update, no_update
            card_id = ctx.triggered_id.get("index")
            card_config.pop(card_id, None)
            for key in card_layouts.keys():
                card_layouts[key] = [
                    item for item in card_layouts[key] if item["i"] != card_id
                ]
            event = {
                "type": "delete-card",
                "data": {"card_id": card_id},
            }
            return card_config, card_layouts, event

        @app.callback(
            Output("cardcanvas-url", "search", allow_duplicate=True),
            Output("notification-container", "sendNotifications", allow_duplicate=True),
            Input({"type": "card-share", "index": ALL}, "n_clicks"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-layout-store", "data"),
            State("cardcanvas-global-store", "data"),
            prevent_initial_call=True,
        )
        def share_card_link(nclicks, card_config, card_layouts, global_settings):
            logging.debug("Callback share_card_link called")
            if not any(nclicks) or not ctx.triggered or not ctx.triggered_id:
                return no_update, no_update
            if not isinstance(ctx.triggered_id, dict):
                return no_update, no_update

            card_id = ctx.triggered_id.get("index")
            payload = _build_card_share_payload(
                card_id=card_id,
                card_config=card_config,
                card_layouts=card_layouts,
                global_settings=global_settings,
            )
            if not payload:
                return no_update, [
                    dict(
                        title="Share Link Failed",
                        message="Unable to build a shareable link for this card.",
                        color="red",
                        action="show",
                    )
                ]
            search = _share_payload_to_search(payload)
            return search, [
                dict(
                    title="Share Link Ready",
                    message=(
                        "The URL now contains the shared card payload. "
                        "Copy the address bar link to share this card."
                    ),
                    color="teal",
                    action="show",
                )
            ]

        @app.callback(
            Output("settings-layout", "children", allow_duplicate=True),
            Output("settings-layout", "opened", allow_duplicate=True),
            Input({"type": "card-settings", "index": ALL}, "n_clicks"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-global-store", "data"),
            prevent_initial_call=True,
        )
        def open_card_settings(nclicks, card_config, global_settings):
            logging.debug("Callback open_card_settings called")
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
                            dmc.Text(card.title, fw="bold", size="lg", c="blue", mb=0),
                            dmc.Text(
                                f"Card ID: {card.id}",
                                fw="bold",
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
            Output("cardcanvas-event-store", "data", allow_duplicate=True),
            Input("card-settings-ok", "n_clicks"),
            State({"type": "card-settings", "id": ALL, "setting": ALL}, "id"),
            State({"type": "card-settings", "id": ALL, "setting": ALL}, "value"),
            State({"type": "card-settings", "id": ALL, "setting": ALL}, "checked"),
            State("cardcanvas-config-store", "data"),
            prevent_initial_call=True,
        )
        def save_card_settings(nclicks, ids, values, checked_values, card_config):
            logging.debug("Callback save_card_settings called")
            if not nclicks or not ctx.triggered:
                return no_update, no_update, no_update
            card_ids = set()
            for idx, value, checked in zip(ids, values, checked_values):
                card_id = idx.get("id")
                setting = idx.get("setting")
                card_ids.add(card_id)
                if card_id not in card_config:
                    continue
                if value is None and (checked in [True, False]):
                    value = checked
                card_config[card_id]["settings"][setting] = value
            event = {
                "type": "update-card",
                "data": {"card_ids": list(card_ids)},
            }
            return card_config, False, event

        @app.callback(
            Output("card-grid", "isDraggable"),
            Output("card-grid", "isResizable"),
            Output({"type": "card-menu", "index": ALL}, "style"),
            Input({"type": "card-menu", "index": ALL}, "id"),
            Input("edit-layout", "checked"),
            prevent_initial_call=True,
        )
        def toggle_edit_mode(ids, checked):
            logging.debug("Callback toggle_edit_mode called")
            if checked:
                return True, True, [{"display": "block"}] * len(ids)
            return False, False, [{"display": "none"}] * len(ids)

        @app.callback(
            Output({"type": "card-content", "index": MATCH}, "children"),
            Input({"type": "card-interval", "index": MATCH}, "n_intervals"),
            State("cardcanvas-config-store", "data"),
            State("cardcanvas-global-store", "data"),
            prevent_initial_call=True,
        )
        def update_card(n_intervals, cards_config, global_settings):
            logging.debug("Callback update_card called")
            if not ctx.triggered_id or not cards_config:
                return no_update
            logging.debug("Updating card by interval:", ctx.triggered_id)
            card_objects = self.card_manager.card_objects(cards_config, global_settings)
            card_id = ctx.triggered_id.get("index")
            card = card_objects[card_id]
            return card.render()

        @app.callback(
            Output("download-layout-data", "data"),
            Input("download-layout", "n_clicks"),
            State("cardcanvas-main-store", "data"),
            prevent_initial_call=True,
        )
        def download_layout(nclicks, main_store):
            logging.debug("Callback download_layout called")
            if not nclicks or not main_store:
                return no_update
            return dict(
                content=json.dumps(main_store), filename="layout.json", type="json"
            )

        @app.callback(
            Output("cardcanvas-main-store", "data", allow_duplicate=True),
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("cardcanvas-event-store", "data", allow_duplicate=True),
            Input("upload-layout", "contents"),
            prevent_initial_call=True,
        )
        def upload_layout(contents):
            if not contents:
                return no_update, no_update, no_update, no_update
            try:
                content_type, content_string = contents.split(",")
                decoded = base64.b64decode(content_string)
                content = decoded.decode("utf-8")
                data = json.loads(content)
                event = {
                    "type": "re-render",
                    "data": None,
                }
                return (
                    data,
                    data.get("card_config", start_card_config),
                    data.get("card_layouts", start_card_layout),
                    event,
                )
            except Exception as e:
                logging.error(e)
            return no_update, no_update, no_update, no_update

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("cardcanvas-global-store", "data", allow_duplicate=True),
            Output("notification-container", "sendNotifications", allow_duplicate=True),
            Output("cardcanvas-event-store", "data", allow_duplicate=True),
            Input("clear-layout", "n_clicks"),
            prevent_initial_call=True,
        )
        def clear_layout(nclicks):
            if not nclicks:
                return no_update, no_update, no_update, no_update, no_update
            return (
                {},
                {},
                {},
                [
                    dict(
                        title="Layout Cleared",
                        message=(
                            "The layout has been cleared."
                            " Click on save to save the changes."
                            " Click on restore to restore the layout.",
                        ),
                        color="red",
                        action="show",
                    )
                ],
                {
                    "type": "re-render",
                    "data": None,
                },
            )

        @app.callback(
            Output("cardcanvas-config-store", "data", allow_duplicate=True),
            Output("cardcanvas-layout-store", "data", allow_duplicate=True),
            Output("notification-container", "sendNotifications", allow_duplicate=True),
            Output("cardcanvas-event-store", "data", allow_duplicate=True),
            Input("reset-layout", "n_clicks"),
            prevent_initial_call=True,
        )
        def reset_layout(nclicks):
            if not nclicks:
                return no_update, no_update, no_update, no_update
            return (
                start_card_config,
                start_card_layout,
                [
                    dict(
                        title="Layout Reset",
                        message=(
                            "The layout has been reset to default layout."
                            " Click on save to save the changes."
                            " Click on restore to restore the layout.",
                        ),
                        color="red",
                        action="show",
                    )
                ],
                {
                    "type": "re-render",
                    "data": None,
                },
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
            Input("color-scheme-toggle", "checked"),
            State("mantine-provider", "forceColorScheme"),
        )
        def switch_theme(toggle, theme):
            logging.debug("Callback switch_theme called")
            return "light" if toggle else "dark"

        return app
