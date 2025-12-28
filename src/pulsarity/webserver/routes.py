"""
HTTP Rest API Routes
"""

import logging
from uuid import UUID

from starlette.responses import Response
from starlette.routing import Route
from starsessions.session import regenerate_session_id

from pulsarity import ctx
from pulsarity.database.heat import HEAT_ADAPTER, HEAT_LIST_ADAPTER, Heat
from pulsarity.database.permission import SystemDefaultPerms
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
from pulsarity.database.user import User
from pulsarity.utils import background
from pulsarity.webserver._wrapper import endpoint
from pulsarity.webserver.validation import (
    BaseResponse,
    LoginRequest,
    LoginResponse,
    LookupParams,
    PaginationParams,
    ResetPasswordRequest,
)

logger = logging.getLogger(__name__)


@endpoint(requires_auth=False, response_model=BaseResponse)
async def check_auth() -> BaseResponse:
    """
    Check if a user is authenticated

    :return: The user's authentication status
    """
    auth_user = ctx.user_ctx.get()
    return BaseResponse(status=auth_user.is_authenticated)


@endpoint(requires_auth=False, request_model=LoginRequest, response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse | Response:
    """
    Pass the user credentials to log the user into the server

    :return: JSON containing the status of the request
    """
    user = await User.get_or_none(username=request.username)

    if user is not None and await user.verify_password(request.password):
        request_ = ctx.request_ctx.get()
        request_.session.update({"auth_id": user.auth_id.hex})
        regenerate_session_id(request_)

        logger.info("%s has been authenticated to the server", user.auth_id.hex)

        background.add_background_task(user.update_user_login_time)
        background.add_background_task(user.check_for_rehash, request.password)

        return LoginResponse(status=True, password_reset_required=user.reset_required)

    return Response(status_code=400)


@endpoint()
async def logout() -> Response:
    """
    Logout the currently connected client

    :return: JSON containing the status of the request
    """
    auth_user = ctx.user_ctx.get()
    logger.info("Logging out user %s", auth_user.identity)
    ctx.request_ctx.get().session.clear()
    return Response(status_code=200)


@endpoint(request_model=ResetPasswordRequest)
async def reset_password(request: ResetPasswordRequest) -> Response:
    """
    Resets the password for the client user

    :return: JSON containing the status of the request
    """
    auth_user = ctx.user_ctx.get()
    uuid = UUID(hex=auth_user.identity)
    user = await User.get_by_uuid(uuid)

    if user is not None and await user.verify_password(request.old_password):
        await user.update_user_password(request.new_password)

        logger.info("Password reset for %s completed", auth_user.identity)

        background.add_background_task(user.update_password_required, False)

        return Response(status_code=200)

    return Response(status_code=400)


@endpoint(
    SystemDefaultPerms.READ_PILOTS,
    path_model=LookupParams,
    response_model=PILOT_ADAPTER,
)
async def get_pilot(path: LookupParams) -> Pilot | Response:
    """
    Get the pilot by id

    :return: Pilot data.
    """
    pilot = await Pilot.get_by_id_with_attributes(path.id)

    if pilot is None:
        return Response(status_code=204)

    return pilot


@endpoint(
    SystemDefaultPerms.READ_PILOTS,
    query_model=PaginationParams,
    response_model=PILOT_LIST_ADAPTER,
)
async def get_pilots(query: PaginationParams) -> list[Pilot]:
    """
    A route for getting all pilots currently stored in the
    database.

    :return: A JSON model of all pilots
    """
    return (
        await Pilot.filter(id__gt=query.cursor)
        .limit(query.limit)
        .prefetch_related("attributes")
    )


@endpoint(
    SystemDefaultPerms.READ_EVENTS,
    path_model=LookupParams,
    response_model=RACE_EVENT_ADAPTER,
)
async def get_event(path: LookupParams) -> RaceEvent | Response:
    """
    Get the event by id

    :return: Event data.
    """
    event = await RaceEvent.get_by_id_with_attributes(path.id)

    if event is None:
        return Response(status_code=204)

    return event


@endpoint(
    SystemDefaultPerms.READ_EVENTS,
    query_model=PaginationParams,
    response_model=RACE_EVENT_LIST_ADAPTER,
)
async def get_events(query: PaginationParams) -> list[RaceEvent]:
    """
    A route for getting all events currently stored in the
    database.

    :return: A JSON model of all events
    """
    return (
        await RaceEvent.filter(id__gt=query.cursor)
        .limit(query.limit)
        .prefetch_related("attributes")
    )


@endpoint(
    SystemDefaultPerms.READ_RACECLASS,
    path_model=LookupParams,
    response_model=RACECLASS_ADAPTER,
)
async def get_racelass(path: LookupParams) -> RaceClass | Response:
    """
    Get the raceclass by id

    :return: Race Class data.
    """
    raceclass = await RaceClass.get_by_id_with_attributes(path.id)

    if raceclass is None:
        return Response(status_code=204)

    return raceclass


@endpoint(
    SystemDefaultPerms.READ_RACECLASS,
    path_model=LookupParams,
    query_model=PaginationParams,
    response_model=RACECLASS_LIST_ADAPTER,
)
async def get_raceclasses_for_event(
    path: LookupParams, query: PaginationParams
) -> list[RaceClass]:
    """
    A route for getting all raceclasses currently stored in the
    database.

    :return: A JSON model of all raceclasses
    """
    return (
        await RaceClass.filter(event_id=path.id)
        .filter(id__gt=query.cursor)
        .limit(query.limit)
        .prefetch_related("attributes")
    )


@endpoint(
    SystemDefaultPerms.READ_ROUND, path_model=LookupParams, response_model=ROUND_ADAPTER
)
async def get_round(path: LookupParams) -> Round | Response:
    """
    Get the round by id
    """
    round_ = await Round.get_by_id_with_attributes(path.id)

    if round_ is None:
        return Response(status_code=204)

    return round_


@endpoint(
    SystemDefaultPerms.READ_ROUND,
    path_model=LookupParams,
    query_model=PaginationParams,
    response_model=ROUND_LIST_ADAPTER,
)
async def get_rounds_for_raceclass(
    path: LookupParams, query: PaginationParams
) -> list[Round]:
    """
    Gets all rounds for a specific racelass
    """
    return (
        await Round.filter(raceclass_id=path.id)
        .filter(id__gt=query.cursor)
        .limit(query.limit)
        .prefetch_related("attributes")
    )


@endpoint(
    SystemDefaultPerms.READ_HEAT, path_model=LookupParams, response_model=HEAT_ADAPTER
)
async def get_heat(path: LookupParams) -> Heat | Response:
    """
    Get the heat by id
    """
    heat = await Heat.get_by_id_with_attributes(path.id)

    if heat is None:
        return Response(status_code=204)

    return heat


@endpoint(
    SystemDefaultPerms.READ_HEAT,
    path_model=LookupParams,
    query_model=PaginationParams,
    response_model=HEAT_LIST_ADAPTER,
)
async def get_heats_for_round(
    path: LookupParams, query: PaginationParams
) -> list[Heat]:
    """
    Gets all heats for a specific round
    """
    return (
        await Heat.filter(round_id=path.id)
        .filter(id__gt=query.cursor)
        .limit(query.limit)
        .prefetch_related("attributes")
    )


ROUTES = [
    Route("/login", endpoint=login, methods=["POST"]),
    Route("/logout", endpoint=logout),
    Route("/auth-check", endpoint=check_auth),
    Route("/reset-password", endpoint=reset_password, methods=["POST"]),
    Route("/pilots/{id:int}", endpoint=get_pilot),
    Route("/pilots", endpoint=get_pilots),
    Route("/events/{id:int}", endpoint=get_event),
    Route("/events", endpoint=get_events),
    Route("/events/{id:int}/raceclasses", endpoint=get_raceclasses_for_event),
    Route("/raceclasses/{id:int}", endpoint=get_racelass),
    Route("/raceclasses/{id:int}/rounds", endpoint=get_rounds_for_raceclass),
    Route("/rounds/{id:int}", endpoint=get_round),
    Route("/rounds/{id:int}/heats", endpoint=get_heats_for_round),
    Route("/heats/{id:int}", endpoint=get_heat),
]
