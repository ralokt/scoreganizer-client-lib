from datetime import datetime
from dataclasses import dataclass

from .exceptions import ScoreganizerKeyExists, ScoreganizerTooEarly


@dataclass
class Tournament:
    id: int
    mode: str
    modeparams: str
    name: str
    location: str
    start: datetime
    end: datetime
    open_entry: bool
    hide_results: bool
    status: str

    @classmethod
    def deserialize_many(cls, data):
        return [cls.deserialize(entry) for entry in data]

    @classmethod
    def deserialize(cls, data):
        initkwargs = {
            **data,
            "start": datetime.fromisoformat(data["start"]),
            "end": datetime.fromisoformat(data["end"]),
        }
        return cls(**initkwargs)

    def __int__(self):
        return self.id


class Tournaments:
    def __init__(self, scoreganizer):
        self._sc = scoreganizer

    @property
    def session(self):
        return self._sc.session

    def _url(self, path):
        return self._sc._url(f"tournaments/{path}")

    def participate(self, tournament):
        pk = int(tournament)
        response = self.session.post(
            self._url(f"participate/{pk}"),
        )
        self._sc._raise_if_error(response)

    def gen_key(self, tournament):
        pk = int(tournament)
        response = self.session.post(
            self._url(f"gen_key/{pk}"),
        )
        self._sc._raise_if_error(response)
        return response.json().get("key")

    def get_key(self, tournament):
        pk = int(tournament)
        response = self.session.get(
            self._url(f"get_key/{pk}"),
        )
        self._sc._raise_if_error(response)
        return response.json().get("key")

    def player_confirm(self, tournament):
        pk = int(tournament)
        response = self.session.post(
            self._url(f"player_confirm/{pk}"),
        )
        self._sc._raise_if_error(response)

    def wait_key(self, tournament):
        pk = int(tournament)
        while True:
            try:
                return self.gen_key(pk)
            except ScoreganizerTooEarly as ex:
                ex.do_wait()
            except ScoreganizerKeyExists:
                return self.get_key(pk)

    def _list(self, name):
        response = self.session.get(self._url(name))
        self._sc._raise_if_error(response)
        return Tournament.deserialize_many(response.json())

    def all(self):
        return self._list("all")

    def my_active(self):
        return self._list("my_active")

    def active(self):
        return self._list("active")

    def archive(self):
        return self._list("archive")

    def upcoming(self):
        return self._list("upcoming")

    def in_progress(self):
        return self._list("in_progress")
