import aiosqlite

from myTypes.LearningRecord import LearningRecord
import random

class LearningDao:
    # table learning
    # 'recordid INTEGER PRIMARY KEY, '
    # 'fromChatId INTEGER, '
    # 'callerUserId INTEGER, '
    # 'callerChatId INTEGER, '
    # 'answerMsgId INTEGER, '
    # 'keyword TEXT,'
    # 'learntRespMsgId INTEGER,'
    # 'autoTrigger INTEGER'
    def __init__(self, db):
        from .KimikaDB import KimikaDB
        self.__kimikaDB: KimikaDB = db
        assert self.__kimikaDB is not None

    async def get_answers(self, chat_id: int, keyword: str) -> LearningRecord | None:
        # 1. 查詢該 chat 的所有 learning record
        # 2. 檢查 arg keyword 是否 in record， 去除所有不 in 的 record
        # 3. 返回一個 LearningRecord
        cursor = await self.__kimikaDB.execute('SELECT * FROM learning WHERE fromChatId=:cid', {'cid': chat_id})
        rows = await cursor.fetchall()
        if rows:
            results: list[aiosqlite.Row] = []
        else:
            return None

        for record in rows:
            if record[5].lower() in keyword.lower():
                results.append(record)

        if not results:
            return None

        result = random.choice(results)

        learning_record = LearningRecord()
        learning_record.from_chat_id = result[1]
        learning_record.caller_user_id = result[2]
        learning_record.caller_chat_id = result[3]
        learning_record.answer_msg_id = result[4]
        learning_record.keyword = result[5]
        learning_record.learnt_resp_msg_id = result[6]
        learning_record.auto_trigger = result[7] == 1

        return learning_record

    async def set_answer(self, learning_record: LearningRecord):
        await self.__kimikaDB.execute(
            'INSERT INTO learning('
            'fromChatId, '
            'callerUserId, '
            'callerChatId, '
            'answerMsgId, '
            'keyword, '
            'learntRespMsgId, '
            'autoTrigger) VALUES (?,?,?,?,?,?,?)',
            (learning_record.from_chat_id,
             learning_record.caller_user_id,
             learning_record.caller_chat_id,
             learning_record.answer_msg_id,
             learning_record.keyword,
             learning_record.learnt_resp_msg_id,
             learning_record.auto_trigger
             )
        )
        await self.__kimikaDB.commit()

    async def del_answer(self, chat_id: int, learnt_msg_id: int) -> bool:
        cursor = await self.__kimikaDB.execute('SELECT * FROM learning WHERE fromChatId=:cid AND learntRespMsgId=:lid',
                                               {'cid': chat_id, 'lid': learnt_msg_id})
        rows = await cursor.fetchall()
        if not rows:
            return False

        await self.__kimikaDB.execute(
            'DELETE FROM learning WHERE fromChatId=:cid AND learntRespMsgId=:lid',
            {'cid': chat_id, 'lid': learnt_msg_id}
        )
        await self.__kimikaDB.commit()
        return True
