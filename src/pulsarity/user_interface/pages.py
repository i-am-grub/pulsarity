"""
User Interface Pages
"""

import itertools
import re
from abc import ABC
from dataclasses import InitVar, dataclass, field
from functools import partial
from typing import TYPE_CHECKING, ClassVar

from pulsarity import ctx
from pulsarity._protobuf import ui_pb2

if TYPE_CHECKING:
    from pulsarity.database.permission import SystemDefaultPerms


@dataclass(frozen=True, slots=True)
class UIPage(ABC):
    """
    Abstract class for user interface runtime pages
    """

    _registered_names: ClassVar[set[str]] = {"/", "/reset-password"}

    _store: ClassVar[dict[int, UIPage]]

    uid: int = field(init=False)

    name: str

    def __post_init__(self) -> None:
        self._store[self.uid] = self

        if not bool(re.fullmatch(r"[A-Za-z0-9\-._~]+", self.name)):
            msg = (
                "Invalid UI page name (must only contain letters, digits, "
                f"hyphens, periods, underscores, or tildes: {self.name}"
            )
            raise ValueError(msg)

        lower = self.name.lower()

        if lower in self._registered_names:
            msg = f"A UI page has already been registered with the name: {lower}"
            raise ValueError(msg)

        self._registered_names.add(lower)


@dataclass(frozen=True, slots=True)
class UIMainPage(UIPage):
    """
    Representation of a page in the user interface
    """

    _store: ClassVar[dict[int, UIMainPage]] = {}

    _counter: ClassVar = itertools.count()
    uid: int = field(default_factory=partial(next, _counter), init=False)

    page_key: str
    permission: SystemDefaultPerms | str | None = field(default=None, kw_only=True)

    @classmethod
    def store_to_message(cls) -> ui_pb2.UIMainPages:
        """
        Convert the store data to message
        """
        scopes = ctx.user_permsissions_ctx.get()
        pages = (
            ui_pb2.UIMainPage(element_id=page.uid, name=page.page_key)
            for page in cls._store.values()
            if page.permission is None or page.permission in scopes
        )
        return ui_pb2.UIMainPages(pages=pages)


@dataclass(frozen=True, slots=True)
class UISubPage(UIPage):
    """
    Representation of a sub page in the user interface
    """

    _store: ClassVar[dict[int, UISubPage]] = {}

    _counter: ClassVar = itertools.count()
    uid: int = field(default_factory=partial(next, _counter), init=False)

    parent: InitVar[UIMainPage | str]
    page_key: str
    permission: SystemDefaultPerms | str | None = field(default=None, kw_only=True)
    parent_name: str = field(init=False)

    def __post_init__(self, parent: UIMainPage | str) -> None:
        super().__post_init__()

        if isinstance(parent, UIMainPage):
            parent = parent.page_key

        object.__setattr__(self, "parent_name", parent)

    @classmethod
    def store_to_message(cls) -> ui_pb2.UISubPages:
        """
        Convert the store data to message
        """
        scopes = ctx.user_permsissions_ctx.get()
        pages = (
            ui_pb2.UISubPage(
                element_id=page.uid, parent_name=page.parent_name, name=page.page_key
            )
            for page in cls._store.values()
            if page.permission is None or page.permission in scopes
        )
        return ui_pb2.UISubPages(sub_pages=pages)
