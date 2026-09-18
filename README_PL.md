# SportManager
Django project for handling and managing sport club and sport comunity around this club.  

# CrossBoxManager
Django application for SportManager project.

## Uruchomienie przez Docker Compose

Konfiguracja służy do lokalnego developmentu. Frontend to szablony HTML
serwowane przez backend Django; oba są dostępne na tym samym porcie.
Wymagany jest uruchomiony Docker oraz Docker Compose v2 obsługujący `--wait`.
Nie trzeba instalować Pythona, uv ani PostgreSQL na hoście.
Wszystkie poniższe polecenia wykonuj w katalogu głównym repozytorium.

Szybkie uruchomienie z przebudową obrazów i oczekiwaniem na gotowość usług:

```sh
./run.sh
```

Skrypt korzysta z konfiguracji `.env`, jeśli istnieje, i można wywołać go
również z innego katalogu, podając ścieżkę do `run.sh`.
Przy pierwszym uruchomieniu utwórz następnie konto administratora zgodnie
z instrukcją poniżej.

### Pierwsze uruchomienie

1. Sprawdź dostępność Dockera:

   ```sh
   docker compose version
   docker info
   ```

2. Opcjonalnie przygotuj konfigurację lokalną:

   ```sh
   cp .env.example .env
   ```

   Edytuj `.env` przed pierwszym startem, jeśli chcesz zmienić porty lub dane
   logowania. Bez tego pliku Compose użyje wartości domyślnych.

3. Zbuduj obrazy i uruchom usługi:

   ```sh
   docker compose up --build -d --wait
   docker compose ps
   ```

   Pierwszy start pobiera obrazy i instaluje zależności z `uv.lock`.
   Backend czeka na gotowość bazy, wykonuje migracje i uruchamia Django.
   `--wait` czeka na gotowość obu usług.

4. Utwórz konto administratora (jednorazowo dla nowej bazy):

   ```sh
   docker compose exec backend python manage.py createsuperuser
   ```

5. Otwórz stronę logowania i zaloguj się utworzonym kontem.
   Konto administratora umożliwia też dostęp do panelu `/admin/`.

### Adresy i połączenie z bazą

- Frontend i backend: <http://localhost:8000/login/>.
- Panel administratora: <http://localhost:8000/admin/>.
- PostgreSQL z hosta: `localhost:5433`, baza `sportmanager`, użytkownik
  `sportmanager`, hasło `sportmanager-dev`.
- Backend łączy się z bazą pod adresem `db:5432` w sieci Compose.

Porty są wystawione na `127.0.0.1`. Backend czeka na gotowość PostgreSQL
i automatycznie wykonuje migracje przed startem. Dane bazy są przechowywane
w wolumenie `postgres_data`; istniejąca baza SQLite nie jest importowana.

Do połączenia z PostgreSQL w kliencie takim jak DBeaver lub pgAdmin użyj
powyższych danych albo wartości ustawionych w `.env`.

| Zmienna w `.env` | Domyślnie | Znaczenie |
| --- | --- | --- |
| `BACKEND_PORT` | `8000` | Port aplikacji na hoście |
| `POSTGRES_HOST_PORT` | `5433` | Port PostgreSQL na hoście |
| `POSTGRES_DB` | `sportmanager` | Nazwa bazy |
| `POSTGRES_USER` | `sportmanager` | Użytkownik bazy |
| `POSTGRES_PASSWORD` | `sportmanager-dev` | Hasło bazy |
| `DJANGO_SECRET_KEY` | Klucz deweloperski z `.env.example` | Klucz podpisywania danych Django |

Jeśli port jest zajęty, ustaw np. `BACKEND_PORT=8001` lub
`POSTGRES_HOST_PORT=5434` i ponownie uruchom Compose. Strona będzie wtedy
dostępna pod `http://localhost:8001/login/`, a baza pod `localhost:5434`.
Porty wewnętrzne kontenerów pozostają odpowiednio 8000 i 5432.
Zmiana danych logowania PostgreSQL po utworzeniu wolumenu wymaga również
zmiany użytkownika/hasła w samej bazie.

### Codzienna praca

Uruchomienie istniejącego środowiska:

```sh
docker compose up -d --wait
```

Po zmianach w kodzie lub zależnościach przebuduj backend — kod jest kopiowany
do obrazu, więc edycja plików na hoście wymaga ponownego zbudowania:

```sh
docker compose up --build -d --wait
```

Podgląd stanu, logów i sprawdzenie konfiguracji Django:

```sh
docker compose ps
docker compose logs -f backend
docker compose logs -f db
docker compose exec backend python manage.py check
```

Podgląd logów zakończ przez `Ctrl+C`; kontenery nadal działają.
Konsola PostgreSQL w kontenerze:

```sh
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Zatrzymanie środowiska:

```sh
docker compose down
```

`docker compose down` zachowuje dane. `docker compose down -v` usuwa również
wolumen bazy i wszystkie zapisane w nim dane.
Konfiguracja używa serwera deweloperskiego Django i `DEBUG=true`;
przed wdrożeniem potrzebna jest osobna konfiguracja produkcyjna.

### Problemy z uruchomieniem

- Zajęty port: zmień `BACKEND_PORT` lub `POSTGRES_HOST_PORT` w `.env`.
- Brak połączenia z Dockerem: uruchom daemon Docker i sprawdź uprawnienia
  swojego użytkownika do korzystania z niego.
- Usługa nie jest gotowa lub migracje nie przechodzą: sprawdź
  `docker compose ps -a` oraz `docker compose logs backend db`.
- Niepoprawne hasło bazy po zmianie `.env`: istniejący wolumen zachowuje
  wcześniejsze dane logowania PostgreSQL.

## Uruchomienie przez uv

Wymagany Python 3.10 lub nowszy oraz [uv](https://docs.astral.sh/uv/getting-started/installation/).
Polecenia wykonuj w katalogu głównym repozytorium. Ten wariant domyślnie
używa SQLite w pliku `db.sqlite3` i działa niezależnie od bazy Compose.

```sh
uv sync --locked
DJANGO_DEBUG=true uv run manage.py migrate
DJANGO_DEBUG=true uv run manage.py createsuperuser
DJANGO_DEBUG=true uv run manage.py runserver
```

Otwórz <http://127.0.0.1:8000/login/> lub <http://127.0.0.1:8000/admin/>.
Serwer działa na pierwszym planie; zatrzymaj go przez `Ctrl+C`.
Jeśli Compose już zajmuje port 8000, uruchom Django przez
`DJANGO_DEBUG=true uv run manage.py runserver 8001` i użyj portu 8001 w przeglądarce.

Zależności bezpośrednie są w `pyproject.toml`, a dokładne wersje i hashe
w `uv.lock`. Plik lock należy przechowywać w repozytorium.
`uv sync --locked --no-dev` instaluje wyłącznie zależności aplikacji.
Grupa `dev` zawiera Black i pip-audit. Aktualizacja: `uv lock --upgrade`,
następnie `uv sync --locked` i ponowna weryfikacja:

```sh
DJANGO_DEBUG=true uv run manage.py check
DJANGO_DEBUG=true uv run manage.py makemigrations --check --dry-run
uv run pytest
uv run pip-audit
```

Projekt używa Django 5.2 LTS i `django-bootstrap5` zamiast niezgodnego
z Django 5 pakietu `django-bootstrap-v5`. Zachowano Django REST Framework
i sterownik PostgreSQL z poprzednich zależności na potrzeby konfiguracji lokalnych;
domyślna baza to SQLite. Zależności pośrednie wybiera uv; usunięto niepotrzebny
na Pythonie 3.10+ `backports.zoneinfo` oraz stare, nieużywane bezpośrednio piny.

Przed wdrożeniem zapoznaj się z [raportem bezpieczeństwa](docs/security-audit.md).
Konfigurację lokalną można nadpisać w ignorowanym przez Git
`SportManager/localsettings.py`. Historyczny raport opisuje stan przed wdrożeniem Etapu 0;
aktualne zabezpieczenia i wymagane działania wdrożeniowe opisano poniżej.


Etap 0: zasady dostępu, migracja ról i konfiguracja produkcyjna są opisane
w [instrukcji zabezpieczeń](docs/stage0-security.md). Development poza Compose
wymaga jawnego `DJANGO_DEBUG=true`; produkcja wymaga `DJANGO_SECRET_KEY`
i `DJANGO_ALLOWED_HOSTS`.


## Testy przez pytest

Wszystkie testy znajdują się w `CrossBoxManager/tests/`:
`test_views.py`, `test_security.py` i `test_negative.py`.

```sh
uv sync --locked
uv run pytest
uv run pytest CrossBoxManager/tests/test_negative.py -q
uv run pytest -k csrf
```

Konfiguracja w `pyproject.toml` wybiera `SportManager.test_settings`.
Pytest korzysta z oddzielnej testowej bazy SQLite w pamięci; nie wymaga
ustawiania `DJANGO_DEBUG`, sekretu ani uruchamiania PostgreSQL.
Dotychczasowa komenda `DJANGO_DEBUG=true uv run manage.py test CrossBoxManager`
również działa. W CI testy uruchamiane są przez pytest.
