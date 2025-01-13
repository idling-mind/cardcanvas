from __future__ import annotations

from typing import Any

import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify
from dash_snap_grid import DraggableDiv


def button_with_tooltip(id, icon, title, tooltip, **button_settings):
    return dmc.Tooltip(
        dmc.Button(
            id=id,
            leftSection=DashIconify(icon=icon),
            children=title,
            **button_settings,
        ),
        label=tooltip,
    )


def icon_with_tooltip(id, icon, title, tooltip, **button_settings):
    return dmc.ActionIcon(
        children=dmc.Tooltip(
            children=DashIconify(icon=icon, width=20, style={"margin": "5px"}),
            label=tooltip,
        ),
        id=id,
        **button_settings,
    )


def main_buttons():
    button_settings = {
        "size": "compact-s",
        "p": 4,
        "variant": "light",
    }
    return dmc.Group(
        [
            icon_with_tooltip(
                id="add-cards",
                icon="mdi:plus",
                title="Add Cards",
                tooltip="Add new cards to the layout",
                **button_settings,
            ),
            dmc.ActionIconGroup(
                children=[
                    dcc.Upload(
                        id="upload-layout",
                        children=icon_with_tooltip(
                            id="upload-layout-button",
                            icon="mdi:upload",
                            title="Upload Layout",
                            tooltip="Upload a JSON file to load a layout.",
                            **button_settings,
                        ),
                    ),
                    icon_with_tooltip(
                        id="download-layout",
                        icon="mdi:download",
                        title="Download Layout",
                        tooltip="Download the current layout as a JSON file.",
                        **button_settings,
                    ),
                    icon_with_tooltip(
                        id="save-layout",
                        icon="mdi:content-save",
                        title="Save Layout",
                        tooltip="Save the current layout to the browser's local storage.",
                        **button_settings,
                    ),
                    icon_with_tooltip(
                        id="restore-layout",
                        icon="mdi:restore-clock",
                        title="Reset Layout",
                        tooltip="Restore the layout to last saved layout.",
                        **button_settings,
                    ),
                    icon_with_tooltip(
                        id="reset-layout",
                        icon="mdi:restore",
                        title="Reset Layout",
                        tooltip="Reset the layout to the default layout.",
                        color="yellow",
                        **button_settings,
                    ),
                    icon_with_tooltip(
                        id="clear-layout",
                        icon="mdi:delete",
                        title="Clear Layout",
                        tooltip="Clear all cards from the layout.",
                        color="red",
                        **button_settings,
                    ),
                ]
            ),
            dmc.Switch(
                "Editable Layout",
                id="edit-layout",
                size="xs",
                checked=False,
                persistence=True,
            ),
            dmc.ActionIcon(
                [
                    dmc.Paper(
                        DashIconify(icon="radix-icons:sun", width=25), darkHidden=True
                    ),
                    dmc.Paper(
                        DashIconify(icon="radix-icons:moon", width=25), lightHidden=True
                    ),
                ],
                variant="transparent",
                color="yellow",
                id="color-scheme-toggle",
                size="lg",
                ms="auto",
            ),
        ],
        id="toolbar",
        p="xs",
    )


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
    title_subtitle.append(dmc.Title(title, order=2, c="blue"))
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
    return dmc.Group(items)


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
                                children=DashIconify(
                                    icon=card_class.icon,
                                    width=25,
                                ),
                            )
                        ),
                        dmc.Stack(
                            [
                                dmc.Text(card_class.title, fw=500, fz=20, c="grey.4"),
                                dmc.Text(card_class.description, fz=14, c="grey"),
                            ],
                            gap=0,
                        ),
                    ],
                    wrap="nowrap",
                ),
                style={"cursor": "grab"},
                p="sm",
                shadow="xs",
                withBorder=True,
            )
        ],
        id=card_class.__name__,
    )


def footer():
    return dmc.Group(
        [
            dmc.Text(
                "Made with ",
                fw=300,
                fz="md",
                c="grey",
            ),
            dcc.Link(
                dmc.Image(src="/assets/logo.svg", style={"height": 30}),
                href="https://github.com/idling-mind/cardcanvas",
                target="_blank",
            ),
        ],
        gap="xs",
        justify="center",
        p="xl",
    )
