import pytest
from pydantic import BaseModel

from pulsarity.database._base import PulsarityBase


@pytest.mark.asyncio
async def test_pydaantic_model():
    """
    Test generating a pydantic base model from the database objects
    """
    assert issubclass(PulsarityBase.generate_pydaantic_model(), BaseModel)


@pytest.mark.asyncio
async def test_pydaantic_queryset():
    """
    Test generating a pydantic queryset model from the database objects
    """
    assert issubclass(PulsarityBase.generate_pydaantic_queryset(), BaseModel)
