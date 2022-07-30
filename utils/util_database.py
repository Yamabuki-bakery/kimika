import global_var
from database.KimikaDB import KimikaDB


async def init_db():
    global_var.db = KimikaDB()
    await global_var.db.init()
