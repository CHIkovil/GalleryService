
class BadMethodKwargsError(Exception):
    def __init__(self, *arg):
        super().__init__(f'Empty kwargs - {",".join(arg)}')
