"""
User Interface Pages
"""

import itertools
import logging
import re
from abc import ABC
from dataclasses import InitVar, dataclass, field
from functools import partial
from typing import TYPE_CHECKING, ClassVar, Self

from pulsarity._core import ctx
from pulsarity._core._protobuf import ui_pb2

if TYPE_CHECKING:
    from pulsarity._core.database.permission import SystemDefaultPerms

_default_names = {"/", "/reset-password"}

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class UIPage(ABC):
    """
    Abstract class for user interface runtime pages
    """

    _registered_names: ClassVar[set[str]] = _default_names.copy()

    _store: ClassVar[list[Self]]

    uid: int = field(init=False)

    name: str

    permission: SystemDefaultPerms | str | None = field(default=None, kw_only=True)
    auto_register: InitVar[bool] = field(default=False, kw_only=True)

    def __post_init__(self, auto_register: bool) -> None:
        if not bool(re.fullmatch(r"[A-Za-z0-9\-._~]+", self.name)):
            msg = (
                "Invalid UI page name (must only contain letters, digits, "
                f"hyphens, periods, underscores, or tildes: {self.name}"
            )
            raise ValueError(msg)

        if auto_register:
            self.register()

    @property
    def registered(self) -> bool:
        """
        The page's registration status
        """
        return self in self._store

    @classmethod
    def is_name_registered(cls, page: UIPage | str) -> bool:
        """
        Check if a name is registered to a page
        """

        if isinstance(page, UIPage):
            page = page.name

        return page in cls._registered_names

    def register(self) -> None:
        """
        Registers a page to be shown in the user interface.
        """
        if self in self._store:
            msg = f"Page {self.name} is already registered for use."
            raise RuntimeError(msg)

        lower = self.name.lower()

        if lower in self._registered_names:
            msg = f"A UI page has already been registered with the name: {lower}"
            raise ValueError(msg)

        self._registered_names.add(lower)
        self._store.append(self)  # type: ignore

    def unregister(self) -> None:
        """
        Unregisteres a page to be shown in the user interface.
        """
        if self not in self._store:
            msg = f"Page {self.name} is not registered for use."
            raise RuntimeError(msg)

        lower = self.name.lower()

        self._registered_names.remove(lower)
        self._store.remove(self)

    @classmethod
    def _reset_pages(cls) -> None:
        """
        UNIT TESTING ONLY: Resets all page names
        """
        cls._registered_names = _default_names.copy()

    @classmethod
    def _clear_registered(cls) -> None:
        """
        UNIT TESTING ONLY: Clears all registered pages in cls store
        """
        cls._store.clear()


@dataclass(frozen=True, slots=True)
class UIMainPage(UIPage):
    """
    Representation of a page in the user interface
    """

    _store: ClassVar = []

    _counter: ClassVar = itertools.count()
    uid: int = field(default_factory=partial(next, _counter), init=False)

    @classmethod
    def store_to_message(cls) -> ui_pb2.UIMainPages:
        """
        Convert the store data to message
        """
        scopes = ctx.user_permsissions_ctx.get()
        pages = (
            ui_pb2.UIMainPage(element_id=page.uid, name=page.name)
            for page in cls._store
            if page.permission is None or page.permission in scopes
        )
        return ui_pb2.UIMainPages(pages=pages)


@dataclass(frozen=True, slots=True)
class UISubPage(UIPage):
    """
    Representation of a sub page in the user interface
    """

    _store: ClassVar = []

    _counter: ClassVar = itertools.count()
    uid: int = field(default_factory=partial(next, _counter), init=False)

    parent: InitVar[UIMainPage | str]

    parent_name: str = field(init=False)

    def __post_init__(self, auto_register: bool, parent: UIPage | str) -> None:  # type: ignore
        if isinstance(parent, UIPage):
            parent = parent.name

        if parent not in self._registered_names:
            msg = f"UIPage with name {parent} does not exist"
            raise RuntimeError(msg)

        object.__setattr__(self, "parent_name", parent)

        super().__post_init__(auto_register)

    @classmethod
    def store_to_message(cls) -> ui_pb2.UISubPages:
        """
        Convert the store data to message
        """
        scopes = ctx.user_permsissions_ctx.get()
        pages = (
            ui_pb2.UISubPage(
                element_id=page.uid, parent_name=page.parent_name, name=page.name
            )
            for page in cls._store
            if page.permission is None or page.permission in scopes
        )
        return ui_pb2.UISubPages(pages=pages)
