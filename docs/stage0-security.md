# Etap 0 — wdrożone zabezpieczenia

Stan implementacji: 2026-09-17. Dokument uzupełnia historyczny
[audyt](security-audit.md); nie stanowi audytu infrastruktury produkcyjnej.

## Członkostwa i uprawnienia

`ClubMembership` jest źródłem autoryzacji: User → członkostwo → klub → rola.
Jedno konto może mieć niezależne role w wielu klubach. Wymagany jest status
`ACTIVE`; legacy `People.sport_club` i flagi `Workers` nie nadają uprawnień.
Profile People/Workers/Athletes pozostają dla zgodności danych i formularzy.

| Operacja | OWNER | MANAGER | COACH | MEMBER |
| --- | --- | --- | --- | --- |
| Własne kluby, szczegóły klubu, prywatne wiadomości | Tak | Tak | Tak | Tak |
| Lista osób w klubie | Tak | Tak | Tak | Nie |
| Dane klubu i konta bankowego — edycja | Tak | Tak | Nie | Nie |
| Dodanie zawodnika / trenera | Tak | Tak | Nie | Nie |
| Dodanie managera / właściciela | Tak | Nie | Nie | Nie |
| Edycja osoby i danych opłat | Tak | Tylko MEMBER/COACH | Nie | Nie |
| Tworzenie klubu i administracja członkostwami | Administrator platformy | Administrator platformy | Administrator platformy | Administrator platformy |

Superuser jest administratorem platformy i ma jawny dostęp do wszystkich
klubów. Samo `is_staff` nie omija klubowej autoryzacji. Modele klubu i
członkostwa w Django admin są dostępne wyłącznie superuserowi.
Tożsamość konta należącego do kilku klubów oraz konta Django staff/superuser
może edytować wyłącznie administrator platformy. Właściciel klubowy nie może
zdegradować istniejącego właściciela przez formularz edycji osoby.

Widoki sprawdzają role dla GET i POST, a wskazane osoby i odbiorcy wiadomości
muszą należeć do wybranego klubu. Lista klubów jest ograniczona do aktywnych
członkostw. Wiadomości prywatne są filtrowane po odbiorcy i klubie.
Niezaimplementowana tablica klubowa zwraca 501 po sprawdzeniu uprawnień.

## Migracja istniejących danych

Uruchomienie w lokalnym środowisku uv:

```sh
DJANGO_DEBUG=true uv run manage.py migrate
```

W Docker Compose:

```sh
docker compose up --build -d --wait
```

Migracja 0004 tworzy członkostwa z obecnych profili:

- manager → MANAGER, **INACTIVE** do ręcznego sprawdzenia;
- trener bez flagi managera → COACH, ACTIVE;
- pozostali, w tym sam skarbnik → MEMBER, ACTIVE;
- profil bez klubu → bez członkostwa.

Nie przypisuje automatycznie właścicieli. Flaga skarbnika nie jest podstawą
nadania roli managera. Administrator powinien zweryfikować stare konta,
ustawić właściciela każdego klubu i aktywować zaufanych managerów w
`/admin/CrossBoxManager/clubmembership/`. Jest to celowe ze względu na
potwierdzoną w audycie możliwość nieuprawnionego nadania starych flag.
Migracje nie usuwają starych profili ani danych treningowych.

## Logowanie i hasła

Publiczne wyjątki middleware dopasowują dokładny login i ścieżki admina.
Każdy widok chroni również własne operacje. Tworzenie kont wymaga uprawnień
klubowych oraz walidacji hasła z danymi nowego użytkownika. Tworzenie konta,
profilu i członkostwa jest transakcyjne. Wylogowanie wymaga POST z CSRF.

Backend logowania obejmuje aplikację oraz Django admin. Stałe okno 15 minut
pozwala na 10 prób na konto i 50 prób z adresu źródłowego, także udanych.
Liczniki są współdzielone przez bazę i nie resetują się przy zmianie procesu.
Zwracany komunikat nie ujawnia, czy konto istnieje lub zostało ograniczone.
Źródłem IP jest `REMOTE_ADDR`; nagłówki klienta nie są zaufane. Za reverse
proxy limit IP dotyczy adresu proxy, chyba że serwer z zaufaną konfiguracją
ustawia rzeczywisty adres klienta. Dopasować limity do takiej infrastruktury.

Zaplanuj codziennie usuwanie wygasłych liczników:

```sh
python manage.py clear_login_attempts
```

## Konfiguracja środowiska

Domyślnie `DEBUG=False`. Bez sekretu i konkretnych hostów aplikacja odmówi
startu. Lokalny development uv wymaga jawnego `DJANGO_DEBUG=true`; przy braku
sekretu generuje klucz na czas procesu. Dla trwałych sesji lokalnych ustaw
własny `DJANGO_SECRET_KEY`. Compose jawnie włącza tryb lokalny.

Przykład zmiennych produkcyjnych (sekret wstrzyknąć z magazynu sekretów):

```sh
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=box.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://box.example.com
```

Produkcja włącza przekierowanie HTTPS, secure cookies sesji i CSRF oraz HSTS
na rok. `DJANGO_TRUST_PROXY_HTTPS=true` można ustawić tylko za zaufanym proxy,
które usuwa przekazany przez klienta `X-Forwarded-Proto` i ustawia własny.

`DJANGO_HSTS_INCLUDE_SUBDOMAINS=true` i `DJANGO_HSTS_PRELOAD=true` są osobnymi
decyzjami wdrożeniowymi. Włączyć je po potwierdzeniu HTTPS dla całej domeny.
Bez nich `check --deploy` zgłasza W005/W021; pozostałe zabezpieczenia działają.
CI sprawdza wariant z obydwiema opcjami włączonymi i nie wycisza ostrzeżeń.

`localsettings.py` nadal może nadpisywać konfigurację, więc trzeba go również
sprawdzić na docelowym serwerze. Compose i runserver pozostają środowiskiem
lokalnym; nie są konfiguracją serwera produkcyjnego.

## Weryfikacja i działania na rzeczywistym wdrożeniu

```sh
DJANGO_DEBUG=true uv run manage.py check
DJANGO_DEBUG=true uv run manage.py makemigrations --check --dry-run
DJANGO_DEBUG=true uv run manage.py test CrossBoxManager
# Poniżej użyć rzeczywistej konfiguracji produkcyjnej:
python manage.py check --deploy --fail-level WARNING
```

CI wykonuje testy, kontrolę migracji i kontrolę ustawień produkcyjnych.
Testy obejmują izolację klubów, role, nieaktywne członkostwa, próby eskalacji,
CSRF, limity logowania, rollback tworzenia konta i migrację legacy ról.

Przed danymi prawdziwego klubu pozostaje wykonanie na docelowej infrastrukturze:

- wymiana używanego wcześniej sekretu i unieważnienie starych sesji;
- sprawdzenie zaufanych kont i aktywacja managerów po migracji;
- potwierdzenie HTTPS, hostów i ustawień proxy, w tym lokalnych nadpisań;
- kontrola `check --deploy` i test dostępu na wdrożeniu.

Nie wykonano rotacji sekretów ani zmian na zewnętrznym serwerze w ramach
implementacji w repozytorium.

Implementacja opiera się na mechanizmach opisanych w dokumentacji Django:
[walidacja haseł](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/)
i [konfiguracja wdrożenia](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).
