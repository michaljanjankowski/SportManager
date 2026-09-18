# SportManager

A Django project for managing sports clubs and their communities.
CrossBoxManager is the Django application within the SportManager project.

[Dokumentacja po polsku](README_PL.md)

## Running with Docker Compose

This configuration is intended for local development. The frontend consists
of HTML templates served by the Django backend; both use the same port.
You need Docker running and Docker Compose v2 with support for `--wait`.
You do not need to install Python, uv, or PostgreSQL on the host.
Run the commands below from the repository root.

To build the images, start the services, and wait until they are ready:

```sh
./run.sh
```

The script uses `.env` if it exists. You can also run it from another directory
by providing the path to `run.sh`. On your first run, create an administrator
account as described below.

### First run

1. Check that Docker is available:

   ```sh
   docker compose version
   docker info
   ```

2. Optionally create a local configuration file:

   ```sh
   cp .env.example .env
   ```

   Edit `.env` before starting for the first time if you want to change ports
   or credentials. Without this file, Compose uses the default values.

3. Build the images and start the services:

   ```sh
   docker compose up --build -d --wait
   docker compose ps
   ```

   The first run downloads images and installs dependencies from `uv.lock`.
   The backend waits for the database, applies migrations, and starts Django.
   `--wait` waits until both services are ready.

4. Create an administrator account (once for each new database):

   ```sh
   docker compose exec backend python manage.py createsuperuser
   ```

5. Open the login page and sign in with the account you created.
   The administrator account also provides access to `/admin/`.

### Addresses and database connection

- Frontend and backend: <http://localhost:8000/login/>.
- Administration panel: <http://localhost:8000/admin/>.
- PostgreSQL from the host: `localhost:5433`, database `sportmanager`,
  username `sportmanager`, password `sportmanager-dev`.
- The backend connects to PostgreSQL at `db:5432` within the Compose network.

Ports are bound to `127.0.0.1`. The backend waits for PostgreSQL and applies
migrations automatically before starting. Database data is stored in the
`postgres_data` volume; an existing SQLite database is not imported.

To connect using DBeaver, pgAdmin, or another PostgreSQL client, use the
credentials above or the values configured in `.env`.

| Variable in `.env` | Default | Purpose |
| --- | --- | --- |
| `BACKEND_PORT` | `8000` | Application port on the host |
| `POSTGRES_HOST_PORT` | `5433` | PostgreSQL port on the host |
| `POSTGRES_DB` | `sportmanager` | Database name |
| `POSTGRES_USER` | `sportmanager` | Database username |
| `POSTGRES_PASSWORD` | `sportmanager-dev` | Database password |
| `DJANGO_SECRET_KEY` | Development key from `.env.example` | Django signing key |

If a port is already in use, set, for example, `BACKEND_PORT=8001` or
`POSTGRES_HOST_PORT=5434`, then start Compose again. The application will be
available at `http://localhost:8001/login/` and the database at `localhost:5434`.
The internal container ports remain 8000 and 5432 respectively.
Changing PostgreSQL credentials after creating the volume also requires
updating the username/password in the database itself.

### Everyday use

Start an existing environment:

```sh
docker compose up -d --wait
```

After changing code or dependencies, rebuild the backend. Source code is
copied into the image, so changes to host files require a rebuild:

```sh
docker compose up --build -d --wait
```

Inspect service status and logs, and check the Django configuration:

```sh
docker compose ps
docker compose logs -f backend
docker compose logs -f db
docker compose exec backend python manage.py check
```

Press `Ctrl+C` to stop following logs; the containers keep running.
To open a PostgreSQL console inside the container:

```sh
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Stop the environment:

```sh
docker compose down
```

`docker compose down` preserves data. `docker compose down -v` also deletes
the database volume and all data stored in it.
This configuration uses Django's development server and `DEBUG=true`;
a separate production configuration is required before deployment.

### Troubleshooting startup

- Port already in use: change `BACKEND_PORT` or `POSTGRES_HOST_PORT` in `.env`.
- Cannot connect to Docker: start the Docker daemon and check your user's
  permissions to access it.
- A service is not ready or migrations fail: check `docker compose ps -a`
  and `docker compose logs backend db`.
- Database password is incorrect after editing `.env`: an existing volume
  retains the previous PostgreSQL credentials.

## Running with uv

You need Python 3.10 or newer and
[uv](https://docs.astral.sh/uv/getting-started/installation/).
Run these commands from the repository root. This option uses SQLite in
`db.sqlite3` by default and runs independently of the Compose database.

```sh
uv sync --locked
DJANGO_DEBUG=true uv run manage.py migrate
DJANGO_DEBUG=true uv run manage.py createsuperuser
DJANGO_DEBUG=true uv run manage.py runserver
```

Open <http://127.0.0.1:8000/login/> or <http://127.0.0.1:8000/admin/>.
The server runs in the foreground; press `Ctrl+C` to stop it.
If Compose already uses port 8000, run `DJANGO_DEBUG=true uv run manage.py runserver 8001`
and use port 8001 in your browser.

Direct dependencies are defined in `pyproject.toml`; exact versions and hashes
are recorded in `uv.lock`. Keep the lock file in the repository.
`uv sync --locked --no-dev` installs only application dependencies.
The `dev` group includes Black and pip-audit. To update dependencies, run
`uv lock --upgrade`, followed by `uv sync --locked`, then verify:

```sh
DJANGO_DEBUG=true uv run manage.py check
DJANGO_DEBUG=true uv run manage.py makemigrations --check --dry-run
uv run pytest
uv run pip-audit
```

The project uses Django 5.2 LTS and `django-bootstrap5` instead of
`django-bootstrap-v5`, which is incompatible with Django 5.
Django REST Framework and the PostgreSQL driver from the previous dependencies
have been retained for local configurations; SQLite is the default database.
uv resolves transitive dependencies. The unnecessary `backports.zoneinfo`
package for Python 3.10+ and old, unused direct pins have been removed.

Before deployment, read the [security report](docs/security-audit.md).
You can override local settings in `SportManager/localsettings.py`, which
is ignored by Git. The report describes the state before Stage 0; see the
implementation and deployment notes below for the current access rules.


Stage 0 access rules, role migration and production configuration are described
in the [security implementation guide](docs/stage0-security.md) (Polish). Local
development outside Compose requires explicit `DJANGO_DEBUG=true`; production
requires `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS`.


## Running tests with pytest

All tests are in `CrossBoxManager/tests/`:
`test_views.py`, `test_security.py`, and `test_negative.py`.

```sh
uv sync --locked
uv run pytest
uv run pytest CrossBoxManager/tests/test_negative.py -q
uv run pytest -k csrf
```

`pyproject.toml` selects `SportManager.test_settings`. Pytest uses an isolated
in-memory SQLite database and needs no local secrets or PostgreSQL server.
The Django command `DJANGO_DEBUG=true uv run manage.py test CrossBoxManager`
also remains available. CI runs the tests through pytest.
