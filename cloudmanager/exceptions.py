class BoardError(Exception):
    pass


class BoardNotResponding(BoardError):
    pass


class NoSuchBoard(BoardError):
    pass
