class LearningDao:

    def __init__(self, db):
        from .KimikaDB import KimikaDB
        self.__kimikaDB: KimikaDB = db
        assert self.__kimikaDB is not None