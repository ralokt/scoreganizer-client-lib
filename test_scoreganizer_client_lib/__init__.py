from contextlib import nullcontext
from io import BytesIO
import time  # noqa: F401  We need to import this to patch time.sleep
from unittest import mock
import pytest

from scoreganizer_client_lib.exceptions import (
    ScoreganizerError,
    ScoreganizerInvalidData,
    ScoreganizerInvalidLoginData,
    ScoreganizerNotLoggedIn,
    ScoreganizerRetry,
    ScoreganizerTokenTooRecent,
)
from scoreganizer_client_lib.scoreganizer import Scoreganizer
from scoreganizer_client_lib.tournament import Tournament


def tournament_json(seq):
    return {
        "id": seq,
        "mode": "sum",
        "modeparams": "1+0+0",
        "name": f"Tournament {seq}",
        "start": "2024-05-21T15:42:18.932526",
        "end": "2024-05-22T15:42:18.932534",
        "location": "The test environment",
        "open_entry": True,
        "hide_results": False,
        "status": "not_logged_in",
    }


@pytest.fixture
def tournament_1_json():
    return tournament_json(1)


@pytest.fixture
def tournament_2_json():
    return tournament_json(2)


@pytest.fixture
def tournaments_json(tournament_1_json, tournament_2_json):
    return [tournament_1_json, tournament_2_json]


@pytest.fixture(
    params=[
        lambda pk: pk,
        lambda pk: Tournament.deserialize(tournament_json(pk)),
    ]
)
def t_param(request):
    return request.param


def api_path(path):
    return f"https://scoreganizer.net:443/api/{path}"


def test_digest_auth(requests_mock):
    requests_mock.post(
        api_path("obtain_token"),
        [
            {
                "status_code": 401,
                "headers": {
                    "WWW-Authenticate": 'Digest realm="realm", nonce="a_nonce", algorithm=MD5, qop="auth"',
                },
            },
            {
                "json": {"token": "asdf"},
                "status_code": 200,
            },
        ],
    )
    sc = Scoreganizer(digest_auth_username="foo", digest_auth_password="bar")
    sc.login("user", "pass")
    assert requests_mock.call_count == 2
    auth_header = requests_mock.last_request._request.headers.get("Authorization")
    parts = (
        "Digest",
        'username="foo"',
        'realm="realm"',
        'nonce="a_nonce"',
        'uri="/api/obtain_token"',
        'algorithm="MD5"',
        'qop="auth"',
        "nc=00000001",
    )
    for part in parts:
        assert part in auth_header


def test_successful_login(requests_mock):
    requests_mock.post(
        api_path("obtain_token"),
        json={"token": "asdf"},
        status_code=200,
    )
    sc = Scoreganizer()
    sc.login("user", "pass")
    assert sc.session.headers.get("X-Scoreganizer-Authorization") == "user:asdf"


def test_unsuccessful_login(requests_mock):
    requests_mock.post(
        api_path("obtain_token"),
        json={"error": "invalid_login_data"},
        status_code=403,
    )
    sc = Scoreganizer()
    with pytest.raises(ScoreganizerInvalidLoginData):
        sc.login("user", "pass")
    assert "X-Scoreganizer-Authorization" not in sc.session.headers


@pytest.mark.parametrize(
    "response, status_code, exception_expected",
    [
        ("qwert", 200, None),
        ("token_too_recent", 429, ScoreganizerTokenTooRecent),
        ("not_logged_in", 403, ScoreganizerNotLoggedIn),
    ],
)
def test_refresh(requests_mock, response, status_code, exception_expected):
    success_expected = exception_expected is None
    json_key = "token" if success_expected else "error"
    requests_mock.post(
        api_path("obtain_token"),
        json={"token": "asdf"},
        status_code=200,
    )
    requests_mock.post(
        api_path("refresh_token"),
        json={json_key: response},
        status_code=status_code,
    )
    sc = Scoreganizer()
    sc.login("user", "pass")
    assert sc.session.headers.get("X-Scoreganizer-Authorization") == "user:asdf"
    if success_expected:
        context = nullcontext()
    else:
        context = pytest.raises(exception_expected)
    with context:
        sc.refresh_login()

    if success_expected:
        assert sc.session.headers.get("X-Scoreganizer-Authorization") == "user:qwert"


@pytest.mark.parametrize(
    "response, refresh_expected",
    [
        ("ok", False),
        ("ok_stale", True),
        ("not_sent", False),
        ("expired", False),
    ],
)
def test_refresh_if_stale(requests_mock, response, refresh_expected):
    requests_mock.post(
        api_path("obtain_token"),
        json={"token": "asdf"},
        status_code=200,
    )
    requests_mock.get(
        api_path("token_status"),
        json={"status": response},
        status_code=200,
    )
    requests_mock.post(
        api_path("refresh_token"),
        json={"token": "qwert"},
        status_code=200,
    )
    sc = Scoreganizer()
    sc.login("user", "pass")
    requests_mock.reset_mock()
    assert not requests_mock.called
    assert sc.session.headers.get("X-Scoreganizer-Authorization") == "user:asdf"
    sc.refresh_login_if_stale()
    assert requests_mock.called
    expected_call_count = 2 if refresh_expected else 1
    assert requests_mock.call_count == expected_call_count
    if refresh_expected:
        assert sc.session.headers.get("X-Scoreganizer-Authorization") == "user:qwert"


@pytest.mark.parametrize(
    "name",
    [
        "active",
        "my_active",
        "all",
        "archive",
        "upcoming",
        "in_progress",
    ],
)
def test_tournament_lists(requests_mock, tournaments_json, name):
    requests_mock.get(
        api_path(f"tournaments/{name}"),
        json=tournaments_json,
        status_code=200,
    )
    ts = Scoreganizer().tournaments
    tournaments = getattr(ts, name)()
    assert len(tournaments) == 2
    t1, t2 = tournaments
    assert t1.id == 1
    assert t1.name == "Tournament 1"
    assert t2.id == 2
    assert t2.name == "Tournament 2"


def test_tournaments_my_active_nologin(requests_mock, tournaments_json):
    requests_mock.get(
        api_path("tournaments/my_active"),
        json={"error": "not_logged_in"},
        status_code=403,
    )
    ts = Scoreganizer().tournaments
    with pytest.raises(ScoreganizerNotLoggedIn):
        ts.my_active()


def test_tournaments_get_key(requests_mock, t_param):
    requests_mock.get(
        api_path("tournaments/get_key/42069"),
        json={"key": "asdf"},
        status_code=200,
    )
    ts = Scoreganizer().tournaments
    assert ts.get_key(t_param(42069)) == "asdf"


def test_tournaments_gen_key(requests_mock, t_param):
    requests_mock.post(
        api_path("tournaments/gen_key/42069"),
        json={"key": "asdf"},
        status_code=201,
    )
    ts = Scoreganizer().tournaments
    assert ts.gen_key(t_param(42069)) == "asdf"


def test_tournaments_wait_key_gen(requests_mock, t_param):
    requests_mock.post(
        api_path("tournaments/gen_key/42069"),
        [
            {
                "json": {"error": "too_early", "wait": "0.0042069"},
                "status_code": 403,
            },
            {
                "json": {"key": "asdf"},
                "status_code": 201,
            },
        ],
    )
    ts = Scoreganizer().tournaments
    assert ts.wait_key(t_param(42069)) == "asdf"


def test_tournaments_wait_key_get(requests_mock, t_param):
    requests_mock.post(
        api_path("tournaments/gen_key/42069"),
        json={"error": "key_exists"},
        status_code=403,
    )
    requests_mock.get(
        api_path("tournaments/get_key/42069"),
        json={"key": "asdf"},
        status_code=200,
    )
    ts = Scoreganizer().tournaments
    assert ts.wait_key(t_param(42069)) == "asdf"


def test_participate(requests_mock, t_param):
    ts = Scoreganizer().tournaments
    requests_mock.post(
        api_path("tournaments/participate/42069"),
        status_code=200,
    )
    assert ts.participate(t_param(42069)) is None
    requests_mock.post(
        api_path("tournaments/participate/42069"),
        status_code=403,
    )
    with pytest.raises(ScoreganizerError):
        ts.participate(t_param(42069))


def test_player_confirm(requests_mock, t_param):
    ts = Scoreganizer().tournaments
    requests_mock.post(
        api_path("tournaments/player_confirm/42069"),
        status_code=200,
    )
    assert ts.player_confirm(t_param(42069)) is None
    requests_mock.post(
        api_path("tournaments/player_confirm/42069"),
        status_code=403,
    )
    with pytest.raises(ScoreganizerError):
        ts.player_confirm(t_param(42069))


def test_upload(requests_mock, tmp_path):
    sc = Scoreganizer().scores

    requests_mock.post(
        api_path("scores/upload"),
        status_code=201,
    )
    replay_content = "Lorem ipsum dolor sit amet, sus amogus venit impostoram"

    def _mkreplay():
        return BytesIO(replay_content.encode())

    # mime_type inferred from filename
    sc.upload_file(_mkreplay(), "test.rmv")
    assert "application/x-viennasweeper" in requests_mock.last_request.text
    assert replay_content in requests_mock.last_request.text
    assert 'filename="test.rmv"' in requests_mock.last_request.text
    assert 'name="video"' in requests_mock.last_request.text
    # mime_type inferred from extension, trumping filename
    sc.upload_file(_mkreplay(), "test.rmv", ext="avf")
    assert "application/x-minesweeper-arbiter" in requests_mock.last_request.text
    assert replay_content in requests_mock.last_request.text
    assert 'filename="test.rmv"' in requests_mock.last_request.text
    assert 'name="video"' in requests_mock.last_request.text
    # mime_type explicitly passed, trumping everything else
    sc.upload_file(
        _mkreplay(), "test.rmv", ext="avf", mime_type="application/x-viennasweeper"
    )
    assert "application/x-viennasweeper" in requests_mock.last_request.text
    assert replay_content in requests_mock.last_request.text
    assert 'filename="test.rmv"' in requests_mock.last_request.text
    assert 'name="video"' in requests_mock.last_request.text

    replay_path = tmp_path / "test.rmv"
    with replay_path.open("w") as replay_file:
        replay_file.write(replay_content)
    sc.upload_filename(replay_path)
    assert "application/x-viennasweeper" in requests_mock.last_request.text
    assert replay_content in requests_mock.last_request.text
    assert 'filename="test.rmv"' in requests_mock.last_request.text
    assert 'name="video"' in requests_mock.last_request.text

    # will retry once for invalid_data
    requests_mock.reset_mock()
    requests_mock.post(
        api_path("scores/upload"),
        json={"error": "invalid_data"},
        status_code=403,
    )
    with pytest.raises(ScoreganizerInvalidData):
        with mock.patch("time.sleep", return_value=None) as tsp:
            sc.upload_file(_mkreplay(), "test.rmv", tries=3)

    assert tsp.call_count == 0
    assert requests_mock.call_count == 1

    # will retry tries times for retry
    requests_mock.reset_mock()
    requests_mock.post(
        api_path("scores/upload"),
        json={"error": "retry"},
        status_code=403,
    )
    with pytest.raises(ScoreganizerRetry):
        with mock.patch("time.sleep", return_value=None) as tsp:
            sc.upload_file(BytesIO(), "test.rmv", tries=3)
    assert tsp.call_count == 2
    assert requests_mock.call_count == 3


@pytest.mark.parametrize(
    "status,expected_ok",
    [
        ("ok", True),
        ("ok_stale", True),
        ("not_sent", False),
        ("expired", False),
    ],
)
def test_token_status(requests_mock, status, expected_ok):
    requests_mock.get(
        api_path("token_status"),
        json={"status": status},
        status_code=200,
    )
    sc = Scoreganizer()
    assert sc.token_status() == status
    assert sc.token_status_ok() == expected_ok


def test_authfile(requests_mock, tmp_path):
    authfile_path = tmp_path / "scoreganizer_auth.txt"
    assert not authfile_path.exists()
    sc = Scoreganizer(auth_filename=authfile_path)
    assert authfile_path.exists()
    assert authfile_path.stat().st_size == 0

    requests_mock.post(
        api_path("obtain_token"),
        json={"token": "asdf"},
        status_code=200,
    )
    sc.login("user", "pass")
    assert authfile_path.stat().st_size > 0
    with authfile_path.open() as authfile:
        assert authfile.read() == "user:asdf"

    requests_mock.reset_mock()
    sc2 = Scoreganizer(auth_filename=authfile_path)
    requests_mock.get(
        api_path("token_status"),
        json={"status": "ok"},
        status_code=200,
        headers={"Authorization": "user:asdf"},
    )
    assert not requests_mock.called
    sc2.token_status()
    assert requests_mock.called
