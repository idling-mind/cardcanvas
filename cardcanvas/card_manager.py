from __future__ import annotations
import logging
import traceback

from abc import ABC, abstractmethod
from typing import Any, Type

import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify


class Card(ABC):
    """Class to represent a card on the dashboard. This is an abstract class.

    This is the parent class for all cards on the dashboard. The following methods
    must be implemented in the child classes:
    - render: Render the card.
    - render_settings: Render the settings for the card.

    The following attributes should be set in the child classes. These are
    used to display the card on in the card gallery:
    - title: The title of the card.
    - description: The description of the card.
    - icon: The icon for the card.
    """

    title: str = "Test Card"
    description: str = "This is a sample card."
    icon = "mdi:file-document-edit"
    color: str = "blue"
    interval: int | None = None
    grid_settings: dict[str, int] | None = None
    debug = False  # Set this to True to display full error traceback on card

    def __init__(
        self,
        card_id,
        global_settings: dict[str, str] | None = None,
        card_settings: dict[str, str] | None = None,
    ):
        """Initialize the card.

        Args:
            card_id: The id of the card.
            global_settings: The global settings for the dashboard.
            card_settings: The settings for the card.
                These settings will be saved in a global store and will be passed
                into the CardManager which inturn passes it onto the card before
                it gets rendered.
        """
        self.id = card_id
        self.global_settings = global_settings or {}
        self.settings = card_settings or {}

    @abstractmethod
    def render(self):
        """Render the card.

        This method should return a Dash component that represents the card in
        the dashboard.
        """
        pass

    def render_container(self):
        """Renders a card with a menu on the top right corner.

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
                                id={"type": "card-settings", "index": self.id},
                                className="no-drag",
                                leftSection=DashIconify(icon="mdi:cog-outline"),
                            ),
                            dmc.MenuItem(
                                "Duplicate",
                                id={"type": "card-duplicate", "index": self.id},
                                className="no-drag",
                                leftSection=DashIconify(icon="mdi:content-copy"),
                            ),
                            dmc.MenuItem(
                                "Delete",
                                id={"type": "card-delete", "index": self.id},
                                className="no-drag",
                                leftSection=DashIconify(icon="mdi:trash-can-outline"),
                                c="red",
                            ),
                        ]
                    ),
                ],
            ),
            id={"type": "card-menu", "index": self.id},
            className="no-drag card-menu",
        )
        try:
            card_content = self.render()
        except Exception as e:
            logging.error(f"Error rendering card {self.id}: {str(e)}")
            logging.error(traceback.format_exc())
            if self.debug:
                card_content = html.Div(
                    html.Pre(
                        f"Error rendering card: {str(e)}\n{traceback.format_exc()}",
                    ),
                    style={
                        "color": "red",
                        "width": "100%",
                        "height": "100%",
                        "overflow": "auto",
                    },
                )
            else:
                card_content = dmc.Alert(
                    dmc.Text(f"Error rendering card: {str(e)}", ff="Consolas"),
                    color="red",
                    title="Error",
                    h="100%",
                )
        children: list[Any] = [
            dcc.Loading(
                html.Div(
                    id={"type": "card-content", "index": self.id},
                    style={"height": "100%"},
                    children=card_content,
                ),
                parent_style={"height": "100%"},
            ),
            buttons,
        ]
        if self.interval:
            children.append(
                dcc.Interval(
                    id={"type": "card-interval", "index": self.id},
                    interval=self.interval,
                )
            )

        return html.Div(
            children,
            style={"position": "relative", "height": "100%"},
            id=self.id,
        )

    def render_settings(self):
        """Render the settings for the card.

        This method should return a Dash component that represents the settings
        for the card in the settings modal. The settings drawer is displayed when
        the user clicks on the settings icon for the card.

        Each control in the settings modal should be a dash input field which has
        a value prop. The control should have an id that matches with
        the following template.
        `id={"type": "card-settings", "id": self.id, "setting": "control-id"}`
        Here `control-id` is the id of the control in the settings drawer.
        This control-id will be the key in the settings dictionary that is passed
        to the card's render method.

        Note: The control's value property is used to update the settings dictionary.
        Right now, no other property name is supported.
        """
        return dmc.Text("Settings not implemented yet.")

class GlobalSettings(ABC):
    """Class to represent the global settings for the dashboard. This is an abstract class.

    This is the parent class for all global settings on the dashboard. The following methods
    must be implemented in the child classes:
    - render: Render the global settings.

    The following attributes should be set in the child classes. These are
    used to display the global settings on in the card gallery:
    - title: The title of the global settings.
    - description: The description of the global settings.
    - icon: The icon for the global settings.
    """

    title: str = "Global Settings"
    description: str = "These settings apply to all cards on the dashboard."
    icon = "mdi:cog"

    def __init__(self, settings: dict[str, str] | None = None) -> None:
        """Initialize the global settings.

        Args:
            global_settings: The global settings for the dashboard.
        """
        self.settings: dict[str, str] = settings or {}

    @abstractmethod
    def render_settings(self):
        """Render the global settings.

        This method should return a Dash component that represents the global settings in
        the dashboard.
        """
        pass

class CardManager:
    """Class to manage the cards on the dashboard."""

    def __init__(self) -> None:
        self.card_classes: dict[str, Type[Card]] = {}
        self.global_settings_class: Type[GlobalSettings] | None = None

    def card_objects(
        self,
        card_config: dict[str, dict[str, Any]],
        global_settings: dict[str, str] | None = None,
    ) -> dict[str, Card]:
        card_config = card_config or {}
        global_settings = global_settings or {}
        cards: dict[str, Card] = {}
        for card_id, card_settings in card_config.items():
            card_class = card_settings.get("card_class")
            if not card_class or card_class not in self.card_classes:
                continue
            card = self.card_classes[card_class](
                card_id, global_settings, card_settings.get("settings", {})
            )
            cards[card_id] = card
        return cards

    def render(
        self,
        card_config: dict[str, dict[str, Any]],
        global_settings: dict[str, str] | None = None,
        debug=False,
    ) -> list[html.Div]:
        cards = self.card_objects(card_config, global_settings)
        for card in cards.values():
            card.debug = debug
        return [card.render_container() for card in cards.values()]

    def register_card_class(self, card_class: Type[Card]) -> None:
        """Register a card class with the card manager.

        Args:
            card_class: The class of the card to be registered.
        """
        self.card_classes[card_class.__name__] = card_class

    def register_global_settings_class(
        self, global_settings_class: Type[GlobalSettings]
    ) -> None:
        """Register a global settings class with the card manager.

        Args:
            global_settings_class: The class of the global settings to be registered.
        """
        self.global_settings_class = global_settings_class
