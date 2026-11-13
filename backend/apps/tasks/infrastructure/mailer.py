class DjangoMailer:
    def send(self, *, to: str, subject: str, body: str) -> None:
        raise NotImplementedError
