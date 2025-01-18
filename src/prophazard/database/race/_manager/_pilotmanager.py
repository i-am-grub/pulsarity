"""
`Pilot` management
"""

from typing_extensions import override

from ..._base import _BaseManager
from .._orm import Pilot


class _PilotManager(_BaseManager[Pilot]):

    @property
    @override
    def _table_class(self) -> type[Pilot]:
        """
        Property holding the respective class type for the database object

        :return: Returns the Pilot class
        """
        return Pilot
