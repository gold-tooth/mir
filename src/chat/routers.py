import uuid
from typing import Annotated
from uuid import UUID

from bson.binary import Binary
from fastapi import APIRouter, Depends
from fastapi.websockets import WebSocket
from orjson import JSONEncodeError, orjson
from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from src.auth.models import AuthUser
from src.chat.exceptions import NoMatchError
from src.chat.schemas import WSAction, WSMessageRequest, WSStatus
from src.chat.utils import (
    create_message,
    delete_message,
    get_user_from_ws_cookie,
    orjson_dumps,
    update_message,
    ws_manager,
)
from src.database import mongo

ws_router = APIRouter(
    prefix="/chat",
    tags=["WebSocket chat"],
)
@ws_router.websocket("/ws")
async def websocket_chat(
    ws: WebSocket,
    user: Annotated[AuthUser, Depends(get_user_from_ws_cookie)],
):
    if user is None:
        await ws.close()
        return

    await ws_manager.connect(ws, user)

    # TODO: recieve message updates

    while True:
        try:
            text_data = await ws.receive_text()
            data = orjson.loads(text_data)
            ws_msg = WSMessageRequest.parse_obj(data)
            match ws_msg.action:
                case WSAction.CREATE:
                    await create_message(ws_msg, ws, user)
                case WSAction.DELETE:
                    await delete_message(ws_msg, ws, user)
                case WSAction.UPDATE:
                    await update_message(ws_msg, ws, user)
        except (RuntimeError, WebSocketDisconnect):  # ws connection error
            await ws_manager.disconnect(ws, user.id)
            break
        except (ValidationError, JSONEncodeError):  # pydantic schema parse error, unknown action, decode msg error
            await ws.send_text(orjson_dumps({
                "status": WSStatus.ERROR,
                "detail": "unknown action or bad message format",
            }))
        except NoMatchError as e:
            await ws.send_text(orjson_dumps({
                "status": WSStatus.ERROR,
                "detail": str(e),
            }))
        except Exception:  # noqa: BLE001
            # TODO: log this shit
            await ws_manager.disconnect(ws, user.id)
            break


@ws_router.get("/messages/{match_id}")
async def get_latest_messages(match_id: UUID):

    collection = mongo.collection

    match_id = str(match_id)

    uuid_bytes = uuid.UUID(match_id).bytes
    bin_data = Binary(uuid_bytes, subtype=3)
    query = {"match_id": bin_data}
    count = await collection.count_documents(query)
    limit = min(count, 30)
    sort = [("created_at", -1)]

    result = []
    for mess in await collection.find(query).limit(limit).sort(sort).to_list(length=limit):
        result.append({

            "_id": mess.get("_id"),
            "match_id": mess.get("match_id"),
            "from_id": mess.get("from_id"),
            "to_id": mess.get("to_id"),
            "text": mess.get("text"),
            "reply_to": mess.get("reply_to"),
            "group_id": mess.get("group_id"),
            "media": mess.get("media"),
            "created_at": mess.get("created_at"),
            "updated_at": mess.get("updated_at"),
            "status": mess.get("status"),



        })

    return result
