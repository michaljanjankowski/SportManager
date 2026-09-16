# SportManager
Django project for handling and managing sport club and sport comunity around this club.  

# CrossBoxManager
Django application for SportManager project.

## Uruchomienie przez uv

Wymagany Python 3.10 lub nowszy oraz [uv](https://docs.astral.sh/uv/getting-started/installation/).

```sh
uv sync --locked
uv run manage.py migrate
uv run manage.py createsuperuser
uv run manage.py runserver
```

Zależności bezpośrednie są w `pyproject.toml`, a dokładne wersje i hashe
w `uv.lock`. Plik lock należy przechowywać w repozytorium.
`uv sync --locked --no-dev` instaluje wyłącznie zależności aplikacji.
Grupa `dev` zawiera Black i pip-audit. Aktualizacja: `uv lock --upgrade`,
następnie `uv sync --locked` i ponowna weryfikacja:

```sh
uv run manage.py check
uv run manage.py makemigrations --check --dry-run
uv run manage.py test
uv run pip-audit
```

Projekt używa Django 5.2 LTS i `django-bootstrap5` zamiast niezgodnego
z Django 5 pakietu `django-bootstrap-v5`. Zachowano Django REST Framework
i sterownik PostgreSQL z poprzednich zależności na potrzeby konfiguracji lokalnych;
domyślna baza to SQLite. Zależności pośrednie wybiera uv; usunięto niepotrzebny
na Pythonie 3.10+ `backports.zoneinfo` oraz stare, nieużywane bezpośrednio piny.

Przed wdrożeniem zapoznaj się z [raportem bezpieczeństwa](docs/security-audit.md).
Konfigurację lokalną można nadpisać w ignorowanym przez Git
`SportManager/localsettings.py`. Aktualizacja zależności nie usuwa opisanych
w raporcie błędów autoryzacji aplikacji.
