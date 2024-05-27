# Scoreganizer Client Lib

The official client library for Scoreganizer, based on `requests`.

Supports:

 - auth
 - getting lists of tournaments
 - participating in tournaments
 - generating and getting tournament keys
 - uploading scores to tournaments

In short, this library can be used to build a client that takes full advantage of the
Scoreganizer API.

It was written for use in the VSH plugin, but also with the explicit intent that it
will make third-party clients much easier to create - for example, if someone wants to
make a client using Arbiter instead of ViennaSweeper.

The API itself may change, but the latest version of this library should always work
with the currently deployed version of Scoreganizer. An effort will be made to avoid a
situation where breaking changes in this client library and the Scoreganizer API
conspire to break existing code without much advance warning. More concrete
guarantees/deprecation timelines will be made/published when both APIs have seen some
use, and 1.0.0 of this library is released.

## Scoreganizer basics

Scoreganizer is a web platform that allows anyone to host Minesweeper tournaments.

Users **participate** in **tournaments**. Once a tournament starts, users can generate
a **tournament key**. This key is then embedded into replays, either automatically by a
client, or manually by the user for Arbiter, and is used to validate that replays were
generated after the tournament started.

Uploads are only accepted until the tournament ends, validating that the replays were
also generated before the tournament ended.

This is the basic workflow. The following variations exist:

 - tournaments, while open entry by default, can also be configured to require
   confirmation by the host for players to participate
 - hosts can invite specific players to tournaments
 - different tournament modes exist, and may restrict the workflow:
   - entry after the tournament has already started can be prohibited (for example, if
     the mode needs to know the number of players for some reason). No such modes exist
     yet.
   - a mode can limit the valid upload period per user in other ways. For example, the
     `sum_timelimit` mode gives every player a fixed amount of time to play within a
     longer timespan once they generate their key.

## Some examples

### A quick and dirty example

```python
>>> from scoreganizer_client_lib.scoreganizer import Scoreganizer
>>> from pprint import pprint
>>>
>>> sc = Scoreganizer(host="localhost", port=8000, https=False)
>>>
>>> sc.login("ralokt", "REDACTED")
'ralokt:9cb34fba788e2d81daeb40e0f0dbaec0558c6b72f0aa89dc59bbd2548b0577be'
>>>
>>> pprint(sc.tournaments.my_active())
[Tournament(id=35,
            mode='sum',
            modeparams='1+1+1',
            name='dj42test2',
            location='here',
            start=datetime.datetime(2024, 5, 20, 13, 37),
            end=datetime.datetime(2025, 5, 20, 13, 37),
            open_entry=True,
            hide_results=False,
            status='participating'),
 Tournament(id=36,
            mode='sum',
            modeparams='1+1+1',
            name='dj42test3',
            location='here',
            start=datetime.datetime(2024, 5, 25, 7, 23, 17, 340015),
            end=datetime.datetime(2025, 5, 24, 15, 42),
            open_entry=True,
            hide_results=False,
            status='participating')]
>>>
>>> sc.tournaments.get_key(35)
'1_35_99a8472376717bc7a676876cf0d351e3'
>>>
>>> # after setting arbiter nick to "ralokt#1_35_99a8472376717bc7a676876cf0d351e3"
>>> sc.scores.upload_filename("/path/to/arbiter/HI-SCORE Beg_8.33_3BV=22_3BVs=2.64_ralokt.avf")
>>>

```

#### Step by step

##### Imports

```python
from scoreganizer_client_lib.scoreganizer import Scoreganizer
from pprint import pprint
```

Here, we just import things we will need.

##### Creating an instance of the API

```python
>>> sc = Scoreganizer(host="localhost", port=8000, https=False)
```

Here, we make an instance of our API client.

This instance will remember our authentication credentials once we have logged in, and
can also be used to update a file containing saved credentials.

##### Logging in

```python
>>> sc.login("ralokt", "REDACTED")
'ralokt:9cb34fba788e2d81daeb40e0f0dbaec0558c6b72f0aa89dc59bbd2548b0577be'
```

Here, we log in with a username and password. Note that while the instance remembers
our credentials, they are also returned in case we want to manage them ourselves.

##### Showing our active tournaments

```python
>>> pprint(sc.tournaments.my_active())
[Tournament(id=35,
            mode='sum',
            modeparams='1+1+1',
            name='dj42test2',
            location='here',
            start=datetime.datetime(2024, 5, 20, 13, 37),
            end=datetime.datetime(2025, 5, 20, 13, 37),
            open_entry=True,
            hide_results=False,
            status='participating'),
 Tournament(id=36,
            mode='sum',
            modeparams='1+1+1',
            name='dj42test3',
            location='here',
            start=datetime.datetime(2024, 5, 25, 7, 23, 17, 340015),
            end=datetime.datetime(2025, 5, 24, 15, 42),
            open_entry=True,
            hide_results=False,
            status='participating')]
```

Here, we get a list of our active tournaments. Active tournaments are either in the
future, or happening right now. The `my_active` endpoint only returns tournaments we
are already participating in (or were invited to, or requested to join).

##### Getting a key

```python
>>> sc.tournaments.get_key(35)
'1_35_99a8472376717bc7a676876cf0d351e3'
```

Here, we get our tournament key. This can only be done once a tournament has started.
The key is embedded in the replay in order to prove that the replay was created/the
game played after the tournament started.

 - For ViennaSweeper, the nickname field needs to be set to the key
 - For Arbiter, the name field needs to be set to the key. A hash (`#`) can be used to
   denote the start of the key, so that players can prepend their name.
   For example, for the game in question, the nickname was set to
   `ralokt#1_35_99a8472376717bc7a676876cf0d351e3`

##### Uploading a game

```python
>>> sc.scores.upload_filename("/path/to/arbiter/HI-SCORE Beg_8.33_3BV=22_3BVs=2.64_ralokt.avf")
```

Here, we upload a game to the tournament. `sc.scores.upload_file` also exists for
filelike objects, and the uploaded mimetype can likewise be set.

### Handling exceptions

```python

from requests.exceptions import RequestException
from scoreganizer_client_lib import Scoreganizer
from scoreganizer_client_lib.exceptions import ScoreganizerInvalidLoginData

# connects to scoreganizer.net by default
sc = Scoreganizer()

while True:
    username = input("username: ")
    password = input("password: ")
    try:
        sc.login(username, password)
    except ScoreganizerInvalidLoginData:
        print("invalid login data!")
    except RequestException as ex:
        print("something went wrong while sending the request")
        raise ex
    except ScoreganizerError as ex:
        print(f"unexpected response from the server: {ex.error}")
        raise ex
    else:
        break

# we are logged in!

# (... do more stuff)
```

`ScoreganizerError` is a common base class for all application-level errors.
However, we also need to keep an eye out for `RequestException`, as something could go
wrong on a lower level.

Note that we aren't retrying here in case of network failure - that's because we don't
need to. The `requests` session is already configured to back off and retry for quite a
bit, more than enough to weather a bit of temporary packet loss or a few HTTP 50x
responses/disconnects during a server restart.

In general, instances of `ScoreganizerError` have an `error` attribute that contains
the string error code sent by the server (for example: `"invalid_login_data"`,
`"not_logged_in"`, etc).

### Using an authfile to manage data

```python
from scoreganizer_client_lib.scoreganizer import Scoreganizer

sc = Scoreganizer(
    host="localhost",
    port=8000,
    https=False,
    auth_filename="scoreganizer_auth.txt",
)
if not sc.token_status_ok():
    username = input("username: ")
    password = input("password: ")
    sc.login(username, password)

# we are logged in!

# (... do more stuff)
```

Note the extra `auth_filename` parameter.

This will

 - create the auth file if it doesn't exist yet
 - if it does, it will use the credentials contained
 - it will also keep the file up to date with the current credentials - for example, if
   the token is refreshed

We then check if we're logged in, and only prompt the user for their username and
password if we don't have valid credentials saved.

## Usage

### General notes

Usage of this library is pretty straightforward:

 - Import the `scoreganizer_client_lib.Scoreganizer` class
 - Instantiate it with configuration options
 - Call its methods that cause requests to be sent

With the last point, it's important to note that, being based on `requests`, **these
methods are synchronous**, meaning that they only return when the request in question is
done. Also, `requests` isn't thread-safe - so all calls to its methods should happen in
the same thread.

(Side note: There is also currently **neither async support nor any utilities that make
working around this limitation easier**; this may change in the future, and contributions
would be welcome!)

**Methods are namespaced in a way that reflects the actual path of the endpoints.** For
example, to get a list of active tournaments, you call
`scoreganizer.tournaments.active()`.

Methods will either

 - **Return a result if the request succeeded**. Results already have python types and are
   ready for use - no shenanigans like conversion, extraction from JSON, etc necessary.
 - **Raise `scoreganizer_client_lib.exceptions.ScoreganizerError` (or a subclass) if the
   request succeeded, but the server returned an error** of some sort (for example, bad
   login data was sent). The exception has an attribute `error` that describes what
   went wrong.

   Some values of `error` cause a specific subclass to be raised; for example, if
   `error` is `"too_early"`, then `ScoreganizerTooEarly` will be raised.

   - For requests relating to tournament keys, the server will include information on
     how long to wait to try again in the response. In these cases, a subclass of
     `scoreganizer_client_lib.exceptions.ScoreganizerWait` is raised. This is a
     subclass of `ScoreganizerError` that also has a `wait_time` attribute (which is a
     `datetime.timedelta`).

     `wait_time` is **NOT** the wait time provided by the server - rather, it's that
     minus the elapsed time of the request, to compensate for ping. There is also a
     convenience method `do_wait` that will call `time.sleep` for `wait_time`. Note
     that there is **NO LIMIT** here - you're responsible for making sure that this
     doesn't hang your program.

 - Or **raise `requests.exceptions.RequestException` (or a subclass) if the request
   didn't succeed** (for example, the server was offline, or the network connection was
   down).

   In future versions, this might change if we switch away from requests for
   something more async-friendly.

   There is also `scoreganizer_client_lib.exceptions.NetworkException`, which is
   currently an alias of `requests.exceptions.RequestException`, and can be imported
   instead if you want to future-proof your code and don't care about the details of
   what went wrong.

### API

Note that this library is still in very early stages of development. While anything not
documented here is considered an implementation detail that may change in patch
versions without warning, this API may still change, too - however, unless otherwise
specified, backwards-incompatible changes will be considered breaking, and trigger a
bump of the minor version.

#### `scoreganizer_client_lib.Scoreganizer`

##### `__init__`

```python
Scoreganizer.__init__(
    host="scoreganizer.net",
    port=443,
    https=True,
    http_adapter=None,
    auth_filename=None,
)
```

`host` - the host to connect to. Default: `"scoreganizer.net"`

`port` - the port to connect to. Default: `443`

`https` - whether or not to use HTTPS. Default: `True`

`http_adapter` - an instance of `requests.adapters.HTTPAdapter`. Can be used to change
how `requests` works under the hood. The default is to add a retry policy that will try
hard to get a request through - for details, check the source code, and only touch this
if you know what you're doing. **MAY BE CHANGED OR REMOVED AT ANY TIME.**

`auth_filename` - path to a file. If set, will read this file on startup, use the
credentials contained, and write any new/changed credentials back to this file.
Default: `None`

##### `login`

```python
Scoreganizer.login(
    self,
    username,
    password,
)
```

Will attempt to get authentication credentials for the scoreganizer user with username
`username` and password `password`.

On success, returns credentials as a string. If `auth_filename` was passed in
`__init__`, the new credentials will be written to that file.

`scoreganizer_client_lib.exceptions.InvalidLoginData` will be raised if the server
rejects the login data.

##### `set_auth_str`

```python
Scoreganizer.set_auth_str(
    self,
    auth_str,
)
```

Will set the authentication credentials in `auth_str`. If `auth_filename` was passed in
`__init__`, the new credentials will be written to that file.

##### `token_status`

```python
Scoreganizer.token_status()
```

 **MAY BE CHANGED OR REMOVED AT ANY TIME.** - might replace with an enum, use
 `token_status_ok` where applicable.

Will check the status of the currently remembered auth token.

On success, returns one of:

 - `"ok"`
 - `"ok_stale"`
 - `"expired"`
 - `"nonexistent"`


Will set the authentication credentials in `auth_str`. If `auth_filename` was passed in
`__init__`, the new credentials will be written to that file.

##### `token_status_ok`

```python
Scoreganizer.token_status_ok()
```

Returns a `bool` indicating whether or not the auth token we have right now is OK to
use (whether or not we are logged in).

##### `refresh_login`

```python
Scoreganizer.refresh_login()
```

Will attempt to obtain and set new authentication credentials.

Somewhat low-level - you probably want to use `refresh_login_if_stale` instead.

Returns the new credentials.

`scoreganizer_client_lib.exceptions.ScoreganizerTokenTooRecent` will be raised if the
server refused to regenerate a token because this was done recently.

`scoreganizer_client_lib.exceptions.ScoreganizerNotLoggedIn` will be raised if no valid
auth credentials were provided.


##### `refresh_login_if_stale`

```python
Scoreganizer.refresh_login_if_stale()
```

Will obtain and set new authentication credentials if the current ones are valid, but
stale.

Returns the new credentials, if applicable, `None` otherwise.

#### `scoreganizer_client_lib.tournament.Tournaments` (`Scoreganizer().tournament`)

Although this class is where those methods live, as stated above - use a `Scoreganizer`
instance to access them. (as in: `sc = Scoreganizer(); sc.tournament.<method>`).

##### Lists - `Tournaments.{all, archive, in_progress, upcoming, active, my_active}`

```python
scoreganizer.tournaments.{all, archive, in_progress, upcoming, active, my_active}()
```

All of these methods return a generator of `Tournament` instances on success. The only
difference is what will be included in the response:

 - `all` - all tournaments that were ever created.
 - `archive` - all tournaments that have already ended.
 - `in_progress` - all tournaments that are in progress right now.
 - `upcoming` - all tournaments that haven't started yet.
 - `active` - all tournaments that are either in `upcoming` or `in_progress`.
 - `my_active` - all tournaments that are in `active` where the participation workflow
   has started for the current user, ie:
   - participation is confirmed, or
   - the user has requested to participate, or
   - the user was invited by the host

   hosts that don't participate don't show up here. **REQUIRES LOGIN.**

##### `Tournaments.participate`

```python
scoreganizer.tournaments.participate(tournament)
```

Participate (or ask to participate if entry isn't open) in `tournament`.

`tournament` can be a `Tournament` instance returned by one of the lists, but also
anything that can be converted to `int`, in which case the tournament with that `id` is
used.

Returns `None` on success.

##### `Tournaments.player_confirm`

```python
scoreganizer.tournaments.player_confirm(tournament)
```

Confirm participation in `tournament`, where the player was invited by the host.

Outside of this precondition, behavior is undefined.

`tournament` can be a `Tournament` instance returned by one of the lists, but also
anything that can be converted to `int`, in which case the tournament with that `id` is
used.

Returns `None` on success.

##### `Tournaments.gen_key`

```python
scoreganizer.tournaments.gen_key(tournament)
```

Attempts to generate a key for this user and tournament. Will return the tournament key
(a `str`) on success.

May raise `scoreganizer_client_lib.exceptions.ScoreganizerTooEarly` if the tournament
hasn't started yet. This is a subclass of `ScoreganizerWait`.

May raise `scoreganizer_client_lib.exceptions.ScoreganizerKeyExists` if a key was
already generated. In this case, you need to use `get_key` to get the key.

##### `Tournaments.get_key`

```python
scoreganizer.tournaments.get_key(tournament)
```

Attempts to get the key for this user and tournament. Will return the tournament key (a
`str`) on success.

May raise `scoreganizer_client_lib.exceptions.ScoreganizerNeverGenerated` if the key
was never generated (and never will be).

May raise `scoreganizer_client_lib.exceptions.ScoreganizerNotGenerated` if the key
wasn't generated, but could be. In this case, you need to use `gen_key` to generate the
key.

May raise `scoreganizer_client_lib.exceptions.ScoreganizerNotGeneratedYet` if the key
wasn't generated, but can be in the future. This is a subclass of `ScoreganizerWait`.

##### `Tournaments.wait_key`

```python
scoreganizer.tournaments.wait_key(tournament)
```

Utility method to generate and/or get the key for this user and tournament, handling
exceptions that don't preclude getting a key, and waiting if necessary. Will return the
tournament key (a `str`) on success.

**This method calls `do_wait()` if either `get_key` or `gen_key` raise
`ScoreganizerWait`. It can take a theoretically unlimited amount of time to execute.**

#### `scoreganizer_client_lib.score.Scores` (`Scoreganizer().scores`)

Although this class is where those methods live, as stated above - use a `Scoreganizer`
instance to access them. (as in: `sc = Scoreganizer(); sc.scores.<method>`).

##### `Scores.upload_file`

```python
scoreganizer.scores.upload_file(
    file,
    filename,
    ext=None,
    mime_type=None,
    tries=10,
)
```

Upload the replay in the filelike object `file`, setting the filename to `filename`.

`ext` - explicitly set the extension. Will be guessed from `filename` if not passed.
One of `"rmv"`, `"avf"`.

`mime_type` - explicitly set the MIME type for the upload. Will be guessed from `ext`
if not passed. One of `"application/x-viennasweeper"`,
`"application/x-minesweeper-arbiter"`

`tries` - how often the client will retry if the server tells the client to retry. This
can happen very rarely despite an upload being valid. Default: `10` (this is way, way
overkill, but should therefore be a safe default). **DEFAULT MAY CHANGE AT ANY TIME.**

##### `Scores.upload_filename`

```python
scoreganizer.scores.upload_filename(
    filename,
    ext=None,
    mime_type=None,
    tries=10,
)
```

Just like `upload_file`, but gets the file from the filesystem at the path `filename`.

