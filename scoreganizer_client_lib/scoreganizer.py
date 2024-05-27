import requests
from requests.auth import HTTPDigestAuth
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from .exceptions import build_exception
from .score import Scores
from .tournament import Tournaments


DEFAULT_RETRY = Retry(
    total=5,
    read=5,
    connect=5,
    status_forcelist=[429, 500, 502, 503, 504],
    backoff_factor=8,
)
DEFAULT_ADAPTER = HTTPAdapter(max_retries=DEFAULT_RETRY)


class Scoreganizer:
    def __init__(
        self,
        host="scoreganizer.net",
        port=443,
        https=True,
        digest_auth_username=None,
        digest_auth_password=None,
        http_adapter=None,
        auth_filename=None,
    ):
        self.host = host
        self.port = port
        self.https = https

        if http_adapter is None:
            http_adapter = DEFAULT_ADAPTER

        digest_auth = self._get_digest_auth(digest_auth_username, digest_auth_password)
        self.session = requests.Session()
        if digest_auth is not None:
            self.session.auth = digest_auth
        self.session.mount("http://", http_adapter)
        self.session.mount("https://", http_adapter)
        self.tournaments = Tournaments(self)
        self.scores = Scores(self)
        self.auth_filename = auth_filename
        self.username = None
        if self.auth_filename is not None:
            self._read_auth_file()

    def _get_digest_auth(self, username, password):
        if username is None or password is None:
            return None
        return HTTPDigestAuth(username, password)

    @property
    def _base_url(self):
        proto = "https" if self.https else "http"
        return f"{proto}://{self.host}:{self.port}/api/"

    def _url(self, path):
        return f"{self._base_url}{path}"

    def _raise_if_error(self, response):
        if not response.ok:
            raise build_exception(response)

    def token_status(self):
        response = self.session.get(
            self._url("token_status"),
        )
        self._raise_if_error(response)
        return response.json().get("status")

    def token_status_ok(self):
        return self.token_status().startswith("ok")

    def login(self, username, password):
        response = self.session.post(
            self._url("obtain_token"),
            data={
                "username": username,
                "password": password,
            },
        )
        self._raise_if_error(response)
        api_token = response.json().get("token", None)
        self.username = username
        return self._set_token(api_token)

    def _set_token(self, api_token):
        auth_str = f"{self.username}:{api_token}"
        self.set_auth_str(auth_str)
        return auth_str

    def refresh_login(self):
        response = self.session.post(self._url("refresh_token"))
        self._raise_if_error(response)
        return self._set_token(response.json().get("token"))

    def refresh_login_if_stale(self):
        if self.token_status() == "ok_stale":
            return self.refresh_login()
        return None

    def set_auth_str(self, auth_str):
        self.session.headers.update(
            {
                "X-Scoreganizer-Authorization": auth_str,
            }
        )
        if self.auth_filename is not None:
            self._write_auth_file(auth_str)

    def _read_auth_file(self):
        # a+ and seek(0) to create the file if it doesn't exist yet
        with open(self.auth_filename, "a+") as auth_file:
            auth_file.seek(0)
            # rstrip in case someone edits the file and saves with trailing newline
            self.set_auth_str(auth_file.read().rstrip())

    def _write_auth_file(self, auth_str):
        with open(self.auth_filename, "w") as auth_file:
            auth_file.write(auth_str)
