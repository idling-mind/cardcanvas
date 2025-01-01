from __future__ import annotations

from typing import Any

import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify
from dash_snap_grid import DraggableDiv


def get_title_layout(title: str, subtitle: str | None = None, logo: str | None = None):
    """Returns a layout for the title of the app.

    Args:
        title (str): The title of the app.
        subtitle (str): The subtitle of the app.
        logo (str): URL of the logo.

    Returns:
        dmc.Group: The title layout
    """
    items = []
    title_subtitle = []
    if logo:
        items.append(
            html.Img(src=logo, height=70),
        )
    title_subtitle.append(
        dmc.Title(
            title,
            order=2,
            c="blue",
        )
    )
    if subtitle:
        title_subtitle.append(
            dmc.Text(
                subtitle,
                fw=300,
                fz="s",
                c="grey",
            )
        )
    items.append(
        dmc.Stack(
            title_subtitle,
            gap=0,
        )
    )
    return dmc.Group(
        items,
        p="xs",
    )


def render_card_in_container(card):
    """Renders a card with a menu on the top right corner.

    Args:
        card (Card): The card object (derived from Card).

    Returns:
        dash.html.Div: The card with a menu at the top.
    """
    buttons = html.Div(
        dmc.Menu(
            [
                dmc.MenuTarget(
                    dmc.ActionIcon(
                        DashIconify(icon="material-symbols:more-horiz"),
                        size="xs",
                        radius="xl",
                        variant="light",
                        color="grey",
                    )
                ),
                dmc.MenuDropdown(
                    [
                        dmc.MenuItem(
                            "Settings",
                            id={"type": "card-settings", "index": card.id},
                            className="no-drag",
                        ),
                        dmc.MenuItem(
                            "Delete",
                            id={"type": "card-delete", "index": card.id},
                            className="no-drag",
                        ),
                    ]
                ),
            ],
        ),
        id={"type": "card-menu", "index": card.id},
        className="no-drag card-menu",
    )
    children: list[Any] = [
        dcc.Loading(
            html.Div(
                card.render(),
                id={"type": "card-content", "index": card.id},
                style={"height": "100%"},
            ),
            parent_style={"height": "100%"},
        ),
        buttons,
    ]
    if hasattr(card, "interval"):
        children.append(
            dcc.Interval(
                id={"type": "card-interval", "index": card.id},
                interval=card.interval,
                disabled=False,
            )
        )
    return html.Div(
        children,
        style={"position": "relative", "height": "100%"},
        id=card.id,
    )


def render_menu(menu_map: list[dict]):
    """Renders a menu from a list of dictionaries.

    Args:
        menu_map (list[dict]): A list of dictionaries with the following keys:
            - id (str): The id of the button.
            - label (str): The label of the button.
            - children (list[dict]): A list of dictionaries with the following keys:
                - label (str): The label of the button.
                - id (str): The id of the button.
                - options (dict): A dictionary with the options for the button.
            - options (dict): A dictionary with the options for the button.

    Returns:
        dash_mantine_components.Group: A group of buttons and dropdowns.
    """
    children = []
    button_settings = {
        "size": "xs",
        "radius": "xl",
        "variant": "light",
    }
    for item in menu_map:
        if "children" in item:
            menu_children = []
            menu_children.append(
                dmc.MenuTarget(
                    dmc.Button(
                        item["label"],
                        **button_settings,
                        rightSection=DashIconify(icon="gridicons:dropdown"),
                        **item.get("options", {}),
                    )
                )
            )
            dropdown_children = []
            for child in item["children"]:
                dropdown_children.append(
                    dmc.MenuItem(
                        child["label"], id=child["id"], **child.get("options", {})
                    )
                )
            menu_children.append(dmc.MenuDropdown(dropdown_children))
            menu = dmc.Menu(menu_children, trigger="hover")
            children.append(menu)
        elif item["id"]:
            children.append(
                dmc.Button(
                    item["label"],
                    id=item["id"],
                    **button_settings,
                    **item.get("options", {}),
                )
            )
    return dmc.Group(children)


def render_buttons(button_map):
    """Renders a group of buttons from a list of dictionaries.

    Args:
        button_map (list[dict]): A list of dictionaries with the following keys:
            - id (str): The id of the button.
            - label (str): The label of the button.
            - icon (str): The icon of the button. As accepted by DashIconify.
            - children (list[dict]): A list of dictionaries with the following keys:
                - label (str): The label of the button.
                - id (str): The id of the button.
                - options (dict): A dictionary with the options for the button.
            - options (dict): A dictionary with the options for the button.

    Returns:
        dash_mantine_components.Group: A group of buttons.
    """
    children = []
    button_settings: dict[str, Any] = {
        "size": "compact-s",
        "p": "xs",
        # "radius": "xl",
        # "variant": "light",
    }
    for item in button_map:
        if "children" in item:
            button_group_children = []
            for child in item["children"]:
                extra_settings = {}
                if child.get("icon"):
                    extra_settings["leftSection"] = DashIconify(
                        icon=child["icon"],
                    )
                if child["id"] and child.get("type") == "upload":
                    button_group_children.append(
                        dcc.Upload(
                            id=child["id"],
                            children=dmc.Button(
                                child["label"],
                                **button_settings,
                                **extra_settings,
                                **child.get("options", {}),
                            ),
                        )
                    )
                else:
                    button_group_children.append(
                        dmc.Button(
                            child["label"],
                            id=child["id"],
                            **button_settings,
                            **extra_settings,
                            **child.get("options", {}),
                        )
                    )
            button_group = dmc.ButtonGroup(
                button_group_children, **item.get("options", {})
            )
            children.append(button_group)
        elif item["id"]:
            extra_settings = {}
            if item.get("icon"):
                extra_settings["leftSection"] = DashIconify(
                    icon=item["icon"],
                )
            children.append(
                dmc.Button(
                    item["label"],
                    id=item["id"],
                    **button_settings,
                    **extra_settings,
                    **item.get("options", {}),
                )
            )
    return dmc.Group(children)


def render_card_preview(card_class) -> DraggableDiv:
    """Renders a card preview in the card gallery

    Args:
        card_class (Card): The card class to render.

    Returns:
        DraggableDiv: A draggable div with the card preview
    """
    return DraggableDiv(
        [
            dmc.Card(
                dmc.Group(
                    [
                        dmc.Paper(
                            dmc.ThemeIcon(
                                size="xl",
                                color=card_class.color,
                                variant="filled",
                                children=DashIconify(icon=card_class.icon, width=25,)
                            )
                        ),
                        dmc.Stack(
                            [
                                dmc.Text(card_class.title, fw=500, fz=20, c="#666"),
                                dmc.Text(card_class.description, fz=14, c="#999"),
                            ],
                            gap=0,
                        ),
                    ],
                    wrap="nowrap",
                ),
                style={"cursor": "grab"},
                p="sm",
                bg="#f2f2f2",
            )
        ],
        id=card_class.__name__,
    )
