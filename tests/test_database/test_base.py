import pytest
from pydantic import BaseModel

from pulsarity.database.base import _PHDataBase


@pytest.mark.asyncio
async def test_pydaantic_model():
    assert issubclass(_PHDataBase.generate_pydaantic_model(), BaseModel)


@pytest.mark.asyncio
async def test_pydaantic_queryset():
    assert issubclass(_PHDataBase.generate_pydaantic_queryset(), BaseModel)
