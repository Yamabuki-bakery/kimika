import logging

from botConfig import *
import global_var
import pyrogram
import asyncio


async def ado_nothing(_, __):
    pass


def do_nothing(_, __):
    pass


def anti_replay(handler: callable) -> callable:
    if asyncio.iscoroutinefunction(handler):
        # @wraps(fn)
        async def wrapper(client: pyrogram.Client, message: pyrogram.types.Message):
            if is_replay(client, handler, message):
                # raise AssertionError(f'[anti_replay] Handler {handler.__name__} message {message.id} at {message.chat.id} replayed!')
                return await ado_nothing(client, message)
            return await handler(client, message)

        return wrapper
    else:
        # @wraps(fn)
        def wrapper(client: pyrogram.Client, message: pyrogram.types.Message):
            if is_replay(client, handler, message):
                return do_nothing(client, message)
            return handler(client, message)

        return wrapper


def is_replay(client: pyrogram.Client, handler: object, message: pyrogram.types.Message) -> bool:
    query_id = hash_query(client, handler, message)
    if query_id in global_var.ANTI_REPLAY_LIST:
        logging.warning(f'[anti_replay] Handler {handler.__name__} message {message.id} at {message.chat.id} replayed!')
        return True
    else:
        global_var.ANTI_REPLAY_LIST.append(query_id)
        return False


def hash_query(client: pyrogram.Client, handler: object, message: pyrogram.types.Message) -> int:
    # print(f'the function is {id(handler)}')
    # print(f'the message is {message.id} from {message.chat.id}')
    return hash(client.name) ^ id(handler) ^ message.id ^ (message.chat.id << 32)
