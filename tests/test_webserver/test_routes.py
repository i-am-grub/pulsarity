"""
HTTP route tests
"""

import pytest
from httpx import AsyncClient

from pulsarity._protobuf import http_pb2, database_pb2
from pulsarity._protobuf.ui_pb2 import (
    UIButtonFields,
    UIETreeMapping,
    UIElementTrees,
    UIMarkdownFields,
    UIValueFields,
)
from pulsarity.database.heat import Heat
from pulsarity.database.pilot import Pilot
from pulsarity.database.raceclass import RaceClass
from pulsarity.database.raceevent import RaceEvent
from pulsarity.database.round import Round
from pulsarity.user_interface.elements import (
    UIButtonField,
    UICheckboxValueField,
    UIDateValueField,
    UIDatetimeValueField,
    UIETree,
    UIEmailValueField,
    UIMarkdownField,
    UINumberValueField,
    UIPasswordValueField,
    UIRangeValueField,
    UISelectValueField,
    UITextValueField,
    UITimeValueField,
    UIURLValueField,
    UIValueField,
)
from pulsarity.webserver._status_codes import HTTPStatusCodes

# pylint:disable=W0212

header = {"Content-Type": "application/x-protobuf"}


async def webserver_login_valid(client: AsyncClient, user_creds: tuple[str, str]):
    """
    Sends the provided credentials to the login api to check if they are
    valid
    """
    message = http_pb2.LoginRequest()
    message.username = user_creds[0]
    message.password = user_creds[1]

    response = await client.post(
        "/login", content=message.SerializeToString(), headers=header
    )

    # response = await client.post("/login", json=login_data)
    assert response.status_code == HTTPStatusCodes.OK

    # Simulate reading JSON as the client
    data = http_pb2.LoginResponse.FromString(response.content)

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
async def test_post_bad_header(client: AsyncClient, user_creds: tuple[str, str]):
    """
    Test to see if the api detects bad credentials
    """
    message = http_pb2.LoginRequest()
    message.username = user_creds[0]
    message.password = user_creds[1]
    response = await client.post("/login", content=message.SerializeToString())
    assert response.status_code == HTTPStatusCodes.UNSUPPORTED_MEDIA_TYPE


@pytest.mark.asyncio
async def test_webserver_login_invalid(
    client: AsyncClient, user_creds: tuple[str, str]
):
    """
    Test to see if the api detects bad credentials
    """
    fake_password = "fake_password"

    message = http_pb2.LoginRequest()
    message.username = user_creds[0]
    message.password = fake_password

    response = await client.post(
        "/login", content=message.SerializeToString(), headers=header
    )

    assert response.status_code == HTTPStatusCodes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_password_reset_invalid(client: AsyncClient, user_creds: tuple[str, str]):
    """
    Test reseting a password while providing invalid credentials
    """
    message = http_pb2.LoginRequest()
    message.username = user_creds[0]
    message.password = user_creds[1]

    response = await client.post(
        "/login", content=message.SerializeToString(), headers=header
    )

    password = "password"
    assert password != user_creds[1]

    message = http_pb2.ResetPasswordRequest()
    message.old_password = password
    message.new_password = "foo"
    response = await client.post(
        "/reset-password", content=message.SerializeToString(), headers=header
    )
    assert response.status_code == HTTPStatusCodes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_password_reset_valid(client: AsyncClient, user_creds: tuple[str, str]):
    """
    Test reseting a password while providing valid credentials
    """
    new_password = "foo"

    reset_required = await webserver_login_valid(client, user_creds)
    assert reset_required is True

    message = http_pb2.ResetPasswordRequest()
    message.old_password = user_creds[1]
    message.new_password = "foo"

    response = await client.post(
        "/reset-password", content=message.SerializeToString(), headers=header
    )
    assert response.status_code == HTTPStatusCodes.OK

    new_creds = (user_creds[0], new_password)

    reset_required = await webserver_login_valid(client, new_creds)
    assert reset_required is False


@pytest.mark.asyncio
async def test_password_reset_blocked(client: AsyncClient, user_creds: tuple[str, str]):
    """
    Test reseting a password while not authenticated
    """
    message = http_pb2.ResetPasswordRequest()
    message.old_password = user_creds[1]
    message.new_password = "foo"

    response = await client.post(
        "/reset-password", content=message.SerializeToString(), headers=header
    )
    assert response.status_code == HTTPStatusCodes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_pilot(authed_client: AsyncClient):
    """
    Test getting individual pilots through the rest api
    """
    await Pilot.bulk_create([Pilot(callsign="foo"), Pilot(callsign="bar")])

    response = await authed_client.get("/pilots/1")
    assert response.status_code == HTTPStatusCodes.OK

    pilot = database_pb2.Pilot.FromString(response.content)
    assert pilot.id == 1
    assert pilot.display_callsign == "foo"

    response = await authed_client.get("/pilots/2")
    assert response.status_code == HTTPStatusCodes.OK

    pilot = database_pb2.Pilot.FromString(response.content)
    assert pilot.id == 2
    assert pilot.display_callsign == "bar"


@pytest.mark.asyncio
async def test_get_pilot_does_not_exist(authed_client: AsyncClient):
    """
    Test getting a pilot that doesn't exist
    """

    response = await authed_client.get("/pilots/1")
    assert response.status_code == HTTPStatusCodes.NO_CONTENT


@pytest.mark.asyncio
async def test_get_pilots(authed_client: AsyncClient):
    """
    Test getting pilots through the rest api
    """
    await Pilot.bulk_create([Pilot(callsign="foo"), Pilot(callsign="bar")])

    response = await authed_client.get("/pilots")
    assert response.status_code == HTTPStatusCodes.OK

    pilots = database_pb2.Pilots.FromString(response.content).pilots
    assert len(pilots) == 2
    assert pilots[0].display_callsign == "foo"
    assert pilots[1].display_callsign == "bar"


@pytest.mark.asyncio
async def test_get_event(authed_client: AsyncClient, basic_event: RaceEvent):
    """
    Test getting individual events through the api
    """
    response = await authed_client.get("/events/1")
    assert response.status_code == HTTPStatusCodes.OK

    event = database_pb2.RaceEvent.FromString(response.content)
    assert event.id == basic_event.id
    assert event.name == basic_event.name


@pytest.mark.asyncio
async def test_get_event_does_not_exist(authed_client: AsyncClient):
    """
    Test getting a pilot that doesn't exist
    """

    response = await authed_client.get("/events/1")
    assert response.status_code == HTTPStatusCodes.NO_CONTENT


@pytest.mark.asyncio
async def test_get_events(authed_client: AsyncClient, basic_event: RaceEvent):
    """
    Test getting events through the rest api
    """
    response = await authed_client.get("/events")
    assert response.status_code == HTTPStatusCodes.OK

    events = database_pb2.RaceEvents.FromString(response.content).events
    assert len(events) == 1
    assert events[0].id == basic_event.id
    assert events[0].name == basic_event.name


@pytest.mark.asyncio
async def test_get_raceclass(authed_client: AsyncClient, basic_raceclass: RaceClass):
    """
    Test getting individual raceclasses through the api
    """
    response = await authed_client.get("/raceclasses/1")
    assert response.status_code == HTTPStatusCodes.OK

    raceclass = database_pb2.RaceClass.FromString(response.content)
    assert raceclass.id == basic_raceclass.id
    assert raceclass.name == basic_raceclass.name


@pytest.mark.asyncio
async def test_get_raceclasses_does_not_exist(authed_client: AsyncClient):
    """
    Test getting a pilot that doesn't exist
    """
    response = await authed_client.get("/raceclasses/1")
    assert response.status_code == HTTPStatusCodes.NO_CONTENT


@pytest.mark.asyncio
async def test_get_event_raceclasses(
    authed_client: AsyncClient, basic_raceclass: RaceClass
):
    """
    Test getting raceclasses for an event through the api
    """
    response = await authed_client.get("/events/1/raceclasses")
    assert response.status_code == HTTPStatusCodes.OK

    raceclasses = database_pb2.RaceClasses.FromString(response.content).raceclasses
    assert len(raceclasses) == 1
    assert raceclasses[0].id == basic_raceclass.id
    assert raceclasses[0].name == basic_raceclass.name


@pytest.mark.asyncio
async def test_get_round(authed_client: AsyncClient, basic_round: Round):
    """
    Test getting individual raceclasses through the api
    """
    response = await authed_client.get("/rounds/1")
    assert response.status_code == HTTPStatusCodes.OK

    round_ = database_pb2.Round.FromString(response.content)
    assert round_.id == basic_round.id
    assert round_.round_num == basic_round.round_num


@pytest.mark.asyncio
async def test_get_round_does_not_exist(authed_client: AsyncClient):
    """
    Test getting a pilot that doesn't exist
    """
    response = await authed_client.get("/rounds/1")
    assert response.status_code == HTTPStatusCodes.NO_CONTENT


@pytest.mark.asyncio
async def test_get_raceclass_rounds(authed_client: AsyncClient, basic_round: Round):
    """
    Test getting individual raceclasses through the api
    """
    response = await authed_client.get("/raceclasses/1/rounds")
    assert response.status_code == HTTPStatusCodes.OK

    rounds = database_pb2.Rounds.FromString(response.content).rounds
    assert rounds[0].id == basic_round.id
    assert rounds[0].round_num == basic_round.round_num


@pytest.mark.asyncio
async def test_get_heat(authed_client: AsyncClient, basic_heat: Heat):
    """
    Test getting individual raceclasses through the api
    """
    response = await authed_client.get("/heats/1")
    assert response.status_code == HTTPStatusCodes.OK

    heat = database_pb2.Heat.FromString(response.content)
    assert heat.id == basic_heat.id
    assert heat.heat_num == basic_heat.heat_num


@pytest.mark.asyncio
async def test_get_heat_does_not_exist(authed_client: AsyncClient):
    """
    Test getting a pilot that doesn't exist
    """
    response = await authed_client.get("/heats/1")
    assert response.status_code == HTTPStatusCodes.NO_CONTENT


@pytest.mark.asyncio
async def test_get_round_heats(authed_client: AsyncClient, basic_heat: Heat):
    """
    Test getting individual raceclasses through the api
    """
    response = await authed_client.get("/rounds/1/heats")
    assert response.status_code == HTTPStatusCodes.OK

    heats = database_pb2.Heats.FromString(response.content).heats
    assert heats[0].id == basic_heat.id
    assert heats[0].heat_num == basic_heat.heat_num


@pytest.mark.asyncio
async def test_get_etree_mappings_unauth(client: AsyncClient):
    """
    Test accessing etree mappings while being unauthenticated
    """
    response = await client.get("/etree-mappings")
    assert response.status_code == HTTPStatusCodes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_etree_mappings(authed_client: AsyncClient):
    """
    Test accessing etree mappings while being authenticated
    """
    response = await authed_client.get("/etree-mappings")
    assert response.status_code == HTTPStatusCodes.OK


@pytest.mark.asyncio
async def test_get_etree_mapping_content(authed_client: AsyncClient):
    """
    Test recieved etree mapping data
    """
    assert len(UIETree._store) == 0
    assert len(UIETree._mapping_store) == 0

    response = await authed_client.get("/etree-mappings")
    assert response.status_code == HTTPStatusCodes.OK

    etrees_container = UIElementTrees.FromString(response.content)
    assert len(etrees_container.etrees) == 0

    # Create two etrees
    tree = UIETree()
    tree.map_to_route("foo")
    tree.map_to_route("bar")

    assert len(UIETree._store) == 1
    assert len(UIETree._mapping_store) == 2

    response = await authed_client.get("/etree-mappings")
    assert response.status_code == HTTPStatusCodes.OK

    etrees_container = UIETreeMapping.FromString(response.content)
    mapping = etrees_container.mapping
    assert len(mapping) == 2
    assert "foo" in mapping
    assert tree.uid in mapping["foo"].element_ids

    assert "bar" in mapping
    assert tree.uid in mapping["bar"].element_ids


@pytest.mark.asyncio
async def test_get_etrees_unauth(client: AsyncClient):
    """
    Test accessing etrees while being unauthenticated
    """
    response = await client.get("/etrees")
    assert response.status_code == HTTPStatusCodes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_etrees(authed_client: AsyncClient):
    """
    Test accessing etrees while being authenticated
    """
    response = await authed_client.get("/etrees")
    assert response.status_code == HTTPStatusCodes.OK


@pytest.mark.asyncio
async def test_get_etrees_content(authed_client: AsyncClient):
    """
    Test recieved etree data
    """
    assert len(UIETree._store) == 0

    response = await authed_client.get("/etrees")
    assert response.status_code == HTTPStatusCodes.OK

    etrees_container = UIElementTrees.FromString(response.content)
    assert len(etrees_container.etrees) == 0

    # Create two etrees
    tree1 = UIETree()
    tree2 = UIETree()
    assert tree1.uid != tree2.uid

    assert len(UIETree._store) == 2

    response = await authed_client.get("/etrees")
    assert response.status_code == HTTPStatusCodes.OK

    etrees_container = UIElementTrees.FromString(response.content)
    etrees = etrees_container.etrees
    assert len(etrees) == 2
    keys = {etree.element_id for etree in etrees}
    assert tree1.uid in keys
    assert tree2.uid in keys


@pytest.mark.asyncio
async def test_get_markdown_fields_unauth(client: AsyncClient):
    """
    Test accessing markdown fields while being unauthenticated
    """
    response = await client.get("/markdown-fields")
    assert response.status_code == HTTPStatusCodes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_markdown_fields(authed_client: AsyncClient):
    """
    Test accessing markdown fields while being authenticated
    """
    response = await authed_client.get("/markdown-fields")
    assert response.status_code == HTTPStatusCodes.OK


@pytest.mark.asyncio
async def test_get_markdown_field_content(authed_client: AsyncClient):
    """
    Test recieved markdown field data
    """
    assert len(UIMarkdownField._store) == 0

    response = await authed_client.get("/markdown-fields")
    assert response.status_code == HTTPStatusCodes.OK

    markdown_container = UIMarkdownFields.FromString(response.content)
    assert len(markdown_container.fields) == 0

    # Create two markdown fields
    field1 = UIMarkdownField("foo")
    field2 = UIMarkdownField("bar")
    assert field1.uid != field2.uid

    assert len(UIMarkdownField._store) == 2

    response = await authed_client.get("/markdown-fields")
    assert response.status_code == HTTPStatusCodes.OK

    markdown_container = UIMarkdownFields.FromString(response.content)
    fields = markdown_container.fields
    assert len(fields) == 2
    keys = {field.element_id for field in fields}
    assert field1.uid in keys
    assert field2.uid in keys


@pytest.mark.asyncio
async def test_get_button_fields_unauth(client: AsyncClient):
    """
    Test accessing button fields while being unauthenticated
    """
    response = await client.get("/button-fields")
    assert response.status_code == HTTPStatusCodes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_button_fields(authed_client: AsyncClient):
    """
    Test accessing button fields while being authenticated
    """
    response = await authed_client.get("/button-fields")
    assert response.status_code == HTTPStatusCodes.OK


@pytest.mark.asyncio
async def test_get_button_field_content(authed_client: AsyncClient):
    """
    Test recieved button field data
    """
    assert len(UIButtonField._store) == 0

    response = await authed_client.get("/button-fields")
    assert response.status_code == HTTPStatusCodes.OK

    button_container = UIButtonFields.FromString(response.content)
    assert len(button_container.fields) == 0

    # Create two markdown fields
    field1 = UIButtonField("foo", lambda: None)
    field2 = UIButtonField("bar", lambda: None)
    assert field1.uid != field2.uid

    assert len(UIButtonField._store) == 2

    response = await authed_client.get("/button-fields")
    assert response.status_code == HTTPStatusCodes.OK

    button_container = UIButtonFields.FromString(response.content)
    fields = button_container.fields
    assert len(fields) == 2
    keys = {field.element_id for field in fields}
    assert field1.uid in keys
    assert field2.uid in keys


@pytest.mark.asyncio
async def test_get_value_fields_unauth(client: AsyncClient):
    """
    Test accessing value fields while being unauthenticated
    """
    response = await client.get("/value-fields")
    assert response.status_code == HTTPStatusCodes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_value_fields(authed_client: AsyncClient):
    """
    Test accessing value fields while being authenticated
    """
    response = await authed_client.get("/value-fields")
    assert response.status_code == HTTPStatusCodes.OK


@pytest.mark.asyncio
async def test_get_value_field_content(authed_client: AsyncClient):
    """
    Test recieved value field data
    """
    assert len(UIValueField._store) == 0

    response = await authed_client.get("/value-fields")
    assert response.status_code == HTTPStatusCodes.OK

    values_container = UIValueFields.FromString(response.content)
    assert len(values_container.fields) == 0

    # Create value fields of all types
    init_fields: list[UIValueField] = [
        UITextValueField(),
        UIPasswordValueField(),
        UIEmailValueField(),
        UIURLValueField(),
        UINumberValueField(),
        UIRangeValueField(),
        UICheckboxValueField(),
        UIDatetimeValueField(),
        UIDateValueField(),
        UITimeValueField(),
        UISelectValueField(),
    ]

    assert len(UIValueField._store) == 11

    response = await authed_client.get("/value-fields")
    assert response.status_code == HTTPStatusCodes.OK

    values_container = UIValueFields.FromString(response.content)
    fields = values_container.fields
    assert len(fields) == 11
    keys = {field.element_id for field in fields}

    field_types = set()
    for field in init_fields:
        assert field.uid in keys
        assert field.field_type not in field_types
        field_types.add(field.field_type)
