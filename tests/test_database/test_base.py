import pytest
from pydantic import BaseModel

from pulsarity.database.base import _PulsarityBase


@pytest.mark.asyncio
async def test_pydaantic_model():
    assert issubclass(_PulsarityBase.generate_pydaantic_model(), BaseModel)


@pytest.mark.asyncio
async def test_pydaantic_queryset():
    assert issubclass(_PulsarityBase.generate_pydaantic_queryset(), BaseModel)
