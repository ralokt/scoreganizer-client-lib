from datetime import timedelta
import time

from requests.exceptions import RequestException as NetworkException


class ScoreganizerError(BaseException):
    def __init__(self, error):
        self.error = error


class ScoreganizerWait(ScoreganizerError):
    def __init__(self, error, wait_time):
        super().__init__(error)
        self.wait_time = wait_time

    def do_wait(self):
        time.sleep(self.wait_time.total_seconds())


class ScoreganizerKeyExists(ScoreganizerError):
    pass


class ScoreganizerTooEarly(ScoreganizerWait):
    pass


class ScoreganizerInvalidLoginData(ScoreganizerError):
    pass


class ScoreganizerInvalidData(ScoreganizerError):
    pass


class ScoreganizerNotLoggedIn(ScoreganizerError):
    pass


class ScoreganizerRetry(ScoreganizerError):
    pass


class ScoreganizerNotGenerated(ScoreganizerError):
    pass


class ScoreganizerNotGeneratedYet(ScoreganizerWait):
    pass


class ScoreganizerNeverGenerated(ScoreganizerError):
    pass


class ScoreganizerTokenTooRecent(ScoreganizerError):
    pass


EXCEPTION_CLS_MAP = {
    "too_early": ScoreganizerTooEarly,
    "key_exists": ScoreganizerKeyExists,
    "invalid_login_data": ScoreganizerInvalidLoginData,
    "invalid_data": ScoreganizerInvalidData,
    "not_logged_in": ScoreganizerNotLoggedIn,
    "retry": ScoreganizerRetry,
    "not_generated": ScoreganizerNotGenerated,
    "not_generated_yet": ScoreganizerNotGeneratedYet,
    "never_generated": ScoreganizerNeverGenerated,
    "token_too_recent": ScoreganizerTokenTooRecent,
}


def build_exception(response):
    if response.content:
        response_json = response.json()
        error = response_json.get("error")
        wait = response_json.get("wait", None)
    else:
        error = str(response.status_code)
        wait = None

    default_cls = ScoreganizerWait if wait is not None else ScoreganizerError
    cls = EXCEPTION_CLS_MAP.get(error, default_cls)
    if wait is not None:
        wait_time = timedelta(seconds=float(wait))
        wait_time -= response.elapsed
        wait_time = max(wait_time, timedelta(seconds=0))
        return cls(error, wait_time)
    return cls(error)


__all__ = [
    "ScoreganizerError",
    "ScoreganizerWait",
    "ScoreganizerKeyExists",
    "ScoreganizerTooEarly",
    "ScoreganizerInvalidData",
    "ScoreganizerInvalidLoginData",
    "ScoreganizerNotLoggedIn",
    "ScoreganizerRetry",
    "ScoreganizerNotGenerated",
    "ScoreganizerNotGeneratedYet",
    "ScoreganizerNeverGenerated",
    "ScoreganizerTokenTooRecent",
    "build_exception",
    "NetworkException",
]
