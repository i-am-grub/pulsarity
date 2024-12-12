from typing_extensions import override

from ..._base import _BaseManager
from .._orm import _Pilot


class _PilotManager(_BaseManager[_Pilot]):

    @property
    @override
    def _table_class(self) -> type[_Pilot]:
        """
        Property holding the respective class type for the database object

        :return Type[Pilot]: Returns the Pilot class
        """
        return _Pilot
