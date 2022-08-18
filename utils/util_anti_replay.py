import asyncio
import logging

import pyrogram

import global_var


async def ado_nothing(*_):
    pass


def do_nothing(*_):
    pass


def anti_replay(handler: callable) -> callable:
    if asyncio.iscoroutinefunction(handler):
        # @wraps(fn)
        async def wrapper(client: pyrogram.Client, message: pyrogram.types.Message, *args):
            if is_replay(client, handler, message, *args):
                # raise AssertionError(f'[anti_replay] Handler {handler.__name__} message {message.id} at {message.chat.id} replayed!')
                return await ado_nothing(client, message, *args)
            return await handler(client, message, *args)

        return wrapper
    else:
        # @wraps(fn)
        def wrapper(client: pyrogram.Client, message: pyrogram.types.Message, *args):
            if is_replay(client, handler, message, *args):
                return do_nothing(client, message, *args)
            return handler(client, message, *args)

        return wrapper


def is_replay(client: pyrogram.Client, handler: callable, message: pyrogram.types.Message, *args) -> bool:
    query_id = hash_query(client, handler, message, *args)
    if query_id in global_var.ANTI_REPLAY_LIST:
        logging.warning(f'[anti_replay] [{handler.__name__}] message {message.id} at {message.chat.id} replayed!')
        return True
    else:
        if len(global_var.ANTI_REPLAY_LIST) == 3000:
            logging.info(f'[anti_replay] Clearing ANTI_REPLAY_LIST')
            global_var.ANTI_REPLAY_LIST = []
        global_var.ANTI_REPLAY_LIST.append(query_id)
        return False


def hash_query(client: pyrogram.Client, handler: object, message: pyrogram.types.Message, *args) -> int:
    # print(f'the function is {id(handler)}')
    # print(f'the message is {message.id} from {message.chat.id}')
    argv = ''
    for arg in args:
        argv += str(arg)
    return hash(client.name) ^ hash(argv) ^ hash(handler) ^ hash(message.chat.id) ^ hash(message.id << 32)
    # return hash(client.name + str(id(handler)) + str(message.id) + str(message.chat.id) + str(argv))
