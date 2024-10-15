import os
import time

from .exceptions import ScoreganizerRetry


class Scores:
    def __init__(self, scoreganizer):
        self._sc = scoreganizer

    @property
    def session(self):
        return self._sc.session

    def _url(self, path):
        return self._sc._url(f"scores/{path}")

    def _mime_type_from_ext(self, ext):
        return {
            "rmv": "application/x-viennasweeper",
            "avf": "application/x-minesweeper-arbiter",
        }.get(ext, "application/x-viennasweeper")

    def upload_filename(self, filename, ext=None, mime_type=None, tries=10):
        # support pathlib.Path
        filename = str(filename)
        with open(filename, "rb") as file:
            return self.upload_file(
                file, filename, ext=ext, mime_type=mime_type, tries=tries
            )

    def upload_file(self, file, filename, ext=None, mime_type=None, tries=10):
        # support pathlib.Path
        filename = str(filename)
        done_tries = 0
        while True:
            try:
                done_tries += 1
                return self._upload_file(file, filename, ext=ext, mime_type=mime_type)
            except ScoreganizerRetry as ex:
                if done_tries >= tries:
                    raise ex
                time.sleep(0.3)

    def _upload_file(self, file, filename, ext=None, mime_type=None):
        filename = os.path.split(filename)[-1]
        if mime_type is None:
            if ext is None:
                ext = filename.rsplit(".", 1)[-1]
            mime_type = self._mime_type_from_ext(ext)
        response = self.session.post(
            self._url("upload"),
            files={"video": (filename, file)},
            data={"mime_type": mime_type},
        )
        self._sc._raise_if_error(response)
