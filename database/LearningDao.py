import aiosqlite

from myTypes.LearningRecord import LearningRecord


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

    async def get_answers(self, chat_id: int, keyword: str) -> list[LearningRecord]:
        cursor = await self.__kimikaDB.execute('SELECT * FROM learning WHERE fromChatId=:cid', {'cid': chat_id})
        rows = await cursor.fetchall()
        if rows:
            results: list[LearningRecord] = []
        else:
            return []

        longest_kw_len = 0
        for row in rows:
            if row[5].lower() in keyword.lower():
                if len(row[5]) > longest_kw_len:
                    longest_kw_len = len(row[5])
                    results = [gen_learning_record(row)]
                elif len(row[5]) == longest_kw_len:
                    results.append(gen_learning_record(row))

        return results

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


def gen_learning_record(data: aiosqlite.Row) -> LearningRecord:
    learning_record = LearningRecord()
    learning_record.from_chat_id = data[1]
    learning_record.caller_user_id = data[2]
    learning_record.caller_chat_id = data[3]
    learning_record.answer_msg_id = data[4]
    learning_record.keyword = data[5]
    learning_record.learnt_resp_msg_id = data[6]
    learning_record.auto_trigger = data[7] == 1
    return learning_record
