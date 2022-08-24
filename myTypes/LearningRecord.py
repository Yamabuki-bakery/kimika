class LearningRecord:
    # record_id: int
    from_chat_id: int
    caller_user_id: int | None
    caller_chat_id: int | None
    answer_msg_id: int  # in kimika cache
    keyword: str
    learnt_resp_msg_id: int
    auto_trigger: bool  # allow auto trigger

    def __init__(self):
        pass