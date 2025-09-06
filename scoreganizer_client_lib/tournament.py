from datetime import datetime, timezone
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
    def deserialize_datetime(cls, dtstr):
        utc = timezone.utc
        return datetime.fromisoformat(dtstr).replace(tzinfo=utc)

    @classmethod
    def deserialize(cls, data):
        initkwargs = {
            **data,
            "start": cls.deserialize_datetime(data["start"]),
            "end": cls.deserialize_datetime(data["end"]),
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

    def _key_response(self, response, with_expiry):
        self._sc._raise_if_error(response)
        response_json = response.json()
        key = response_json.get("key")
        if not with_expiry:
            return key
        expiry = response_json.get("key_expiry")
        if expiry is not None:
            expiry = Tournament.deserialize_datetime(expiry)
        return (key, expiry)

    def gen_key(self, tournament, with_expiry=False):
        pk = int(tournament)
        response = self.session.post(
            self._url(f"gen_key/{pk}"),
        )
        return self._key_response(response, with_expiry)

    def get_key(self, tournament, with_expiry=False):
        pk = int(tournament)
        response = self.session.get(
            self._url(f"get_key/{pk}"),
        )
        return self._key_response(response, with_expiry)

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
