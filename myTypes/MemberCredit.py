class MemberCredit:
    valid: bool = True
    photo: bool
    new_account: bool
    username: str | None
    bio: str | None
    joined_time: int
    joined_time_readable: str
    msg_count_before_24h: int