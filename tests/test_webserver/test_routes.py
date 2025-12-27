"""
HTTP route tests
"""

import pytest
from httpx import AsyncClient

from pulsarity.database.heat import HEAT_ADAPTER, HEAT_LIST_ADAPTER, Heat
from pulsarity.database.pilot import PILOT_ADAPTER, PILOT_LIST_ADAPTER, Pilot
from pulsarity.database.raceclass import (
    RACECLASS_ADAPTER,
    RACECLASS_LIST_ADAPTER,
    RaceClass,
)
from pulsarity.database.raceevent import (
    RACE_EVENT_ADAPTER,
    RACE_EVENT_LIST_ADAPTER,
    RaceEvent,
)
from pulsarity.database.round import ROUND_ADAPTER, ROUND_LIST_ADAPTER, Round
from pulsarity.webserver.validation import LoginResponse


async def webserver_login_valid(client: AsyncClient, user_creds: tuple[str, str]):
    """
    Sends the provided credentials to the login api to check if they are
    valid
    """

    login_data = {"username": user_creds[0], "password": user_creds[1]}
    response = await client.post("/login", json=login_data)
    assert response.status_code == 200

    # Simulate reading JSON as the client
    data_ = response.json()
    assert isinstance(data_, dict)

    data = LoginResponse.model_validate(data_)

    assert data.status is True
    reset_required = data.password_reset_required
    assert reset_required is not None
    return reset_required


@pytest.mark.asyncio
async def test_webserver_login_valid(client: AsyncClient, user_creds: tuple[str, str]):
    """
    Test to see if the base credentials are valid through the api
    """
    await webserver_login_valid(client, user_creds)


@pytest.mark.asyncio
async def test_webserver_login_invalid(
    client: AsyncClient, user_creds: tuple[str, str]
):
    """
    Test to see if the api detects bad credentials
    """
    fake_password = "fake_password"
    login_data = {"username": user_creds[0], "password": fake_password}
    response = await client.post("/login", json=login_data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_invalid(client: AsyncClient, user_creds: tuple[str, str]):
    """
    Test reseting a password while providing invalid credentials
    """
    login_data = {"username": user_creds[0], "password": user_creds[1]}
    response = await client.post("/login", json=login_data)
    assert response.status_code == 200

    password = "password"
    assert password != user_creds[1]

    data = {"old_password": password, "new_password": "new_password"}

    response = await client.post("/reset-password", json=data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_valid(client: AsyncClient, user_creds: tuple[str, str]):
    """
    Test reseting a password while providing valid credentials
    """
    new_password = "new_password"

    reset_required = await webserver_login_valid(client, user_creds)
    assert reset_required is True

    reset_data = {
        "old_password": user_creds[1],
        "new_password": new_password,
    }

    response = await client.post("/reset-password", json=reset_data)
    assert response.status_code == 200

    new_creds = (user_creds[0], new_password)

    reset_required = await webserver_login_valid(client, new_creds)
    assert reset_required is False


@pytest.mark.asyncio
async def test_password_reset_blocked(client: AsyncClient, user_creds: tuple[str, str]):
    """
    Test reseting a password while note being authenticated
    """

    reset_data = {
        "old_password": user_creds[1],
        "new_password": "new_password",
    }

    response = await client.post("/reset-password", json=reset_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_pilot(authed_client: AsyncClient):
    """
    Test getting individual pilots through the rest api
    """
    await Pilot.bulk_create([Pilot(callsign="foo"), Pilot(callsign="bar")])

    response = await authed_client.get("/pilots/1")
    assert response.status_code == 200

    pilot = PILOT_ADAPTER.validate_json(response.content)
    assert pilot.id == 1
    assert pilot.display_callsign == "foo"

    response = await authed_client.get("/pilots/2")
    assert response.status_code == 200

    pilot = PILOT_ADAPTER.validate_json(response.content)
    assert pilot.id == 2
    assert pilot.display_callsign == "bar"


@pytest.mark.asyncio
async def test_get_pilot_does_not_exist(authed_client: AsyncClient):
    """
    Test getting a pilot that doesn't exist
    """

    response = await authed_client.get("/pilots/1")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_pilots(authed_client: AsyncClient):
    """
    Test getting pilots through the rest api
    """
    await Pilot.bulk_create([Pilot(callsign="foo"), Pilot(callsign="bar")])

    response = await authed_client.get("/pilots")
    assert response.status_code == 200

    pilots = PILOT_LIST_ADAPTER.validate_json(response.content)
    assert len(pilots) == 2
    assert pilots[0].display_callsign == "foo"
    assert pilots[1].display_callsign == "bar"


@pytest.mark.asyncio
async def test_get_event(authed_client: AsyncClient, basic_event: RaceEvent):
    """
    Test getting individual events through the api
    """
    response = await authed_client.get("/events/1")
    assert response.status_code == 200

    event = RACE_EVENT_ADAPTER.validate_json(response.content)
    assert event.id == basic_event.id
    assert event.name == basic_event.name
    assert event.date == basic_event.date


@pytest.mark.asyncio
async def test_get_event_does_not_exist(authed_client: AsyncClient):
    """
    Test getting a pilot that doesn't exist
    """

    response = await authed_client.get("/events/1")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_events(authed_client: AsyncClient, basic_event: RaceEvent):
    """
    Test getting events through the rest api
    """
    response = await authed_client.get("/events")
    assert response.status_code == 200

    events = RACE_EVENT_LIST_ADAPTER.validate_json(response.content)
    assert len(events) == 1
    assert events[0].id == basic_event.id
    assert events[0].name == basic_event.name
    assert events[0].date == basic_event.date


@pytest.mark.asyncio
async def test_get_raceclass(authed_client: AsyncClient, basic_raceclass: RaceClass):
    """
    Test getting individual raceclasses through the api
    """
    response = await authed_client.get("/raceclasses/1")
    assert response.status_code == 200

    raceclass = RACECLASS_ADAPTER.validate_json(response.content)
    assert raceclass.id == basic_raceclass.id
    assert raceclass.name == basic_raceclass.name


@pytest.mark.asyncio
async def test_get_raceclasses_does_not_exist(authed_client: AsyncClient):
    """
    Test getting a pilot that doesn't exist
    """
    response = await authed_client.get("/raceclasses/1")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_event_raceclasses(
    authed_client: AsyncClient, basic_raceclass: RaceClass
):
    """
    Test getting raceclasses for an event through the api
    """
    response = await authed_client.get("/events/1/raceclasses")
    assert response.status_code == 200

    raceclasses = RACECLASS_LIST_ADAPTER.validate_json(response.content)
    assert len(raceclasses) == 1
    assert raceclasses[0].id == basic_raceclass.id
    assert raceclasses[0].name == basic_raceclass.name


@pytest.mark.asyncio
async def test_get_round(authed_client: AsyncClient, basic_round: Round):
    """
    Test getting individual raceclasses through the api
    """
    response = await authed_client.get("/rounds/1")
    assert response.status_code == 200

    round_ = ROUND_ADAPTER.validate_json(response.content)
    assert round_.id == basic_round.id
    assert round_.round_num == basic_round.round_num


@pytest.mark.asyncio
async def test_get_round_does_not_exist(authed_client: AsyncClient):
    """
    Test getting a pilot that doesn't exist
    """
    response = await authed_client.get("/rounds/1")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_raceclass_rounds(authed_client: AsyncClient, basic_round: Round):
    """
    Test getting individual raceclasses through the api
    """
    response = await authed_client.get("/raceclasses/1/rounds")
    assert response.status_code == 200

    rounds = ROUND_LIST_ADAPTER.validate_json(response.content)
    assert rounds[0].id == basic_round.id
    assert rounds[0].round_num == basic_round.round_num


@pytest.mark.asyncio
async def test_get_heat(authed_client: AsyncClient, basic_heat: Heat):
    """
    Test getting individual raceclasses through the api
    """
    response = await authed_client.get("/heats/1")
    assert response.status_code == 200

    heat = HEAT_ADAPTER.validate_json(response.content)
    assert heat.id == basic_heat.id
    assert heat.heat_num == basic_heat.heat_num


@pytest.mark.asyncio
async def test_get_heat_does_not_exist(authed_client: AsyncClient):
    """
    Test getting a pilot that doesn't exist
    """
    response = await authed_client.get("/heats/1")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_round_heats(authed_client: AsyncClient, basic_heat: Heat):
    """
    Test getting individual raceclasses through the api
    """
    response = await authed_client.get("/rounds/1/heats")
    assert response.status_code == 200

    heats = HEAT_LIST_ADAPTER.validate_json(response.content)
    assert heats[0].id == basic_heat.id
    assert heats[0].heat_num == basic_heat.heat_num
