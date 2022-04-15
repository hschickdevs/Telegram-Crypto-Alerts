

class CustomLogger:
    def __init__(self, identifier: str):
        self.identifier = identifier

    def log(self, message: str):
        print(f'\n<{self.identifier}> {message}')
