# Audyt bezpieczeństwa — 2026-09-16

Zakres: kod Django, konfiguracja, szablony i znane podatności zależności.
To przegląd repozytorium i testy na tymczasowej bazie SQLite, bez testowania
uruchomionego serwera produkcyjnego ani jego infrastruktury.
W ramach zmian zaktualizowano zależności i przeniesiono je do uv.
Poniższe błędy kodu i konfiguracji pozostają do naprawienia.

## 1. Krytyczne: możliwość utworzenia konta bez logowania

`SportManager/settings.py:128`: `LOGIN_EXEMPT_URLS = ('/admin')` jest napisem,
nie krotką. `CrossBoxManager/middleware.py:10` iteruje po jego znakach,
tworząc wyrażenia regularne `a`, `d`, `m`, `i`, `n` oraz `/`.
Dopasowanie do ścieżki pozbawionej początkowego `/` zwalnia m.in.
`athlete_add/…` z logowania. Zwolnienie loginu również nie ma końcowej kotwicy.

Potwierdzenie na tymczasowej bazie: anonimowy GET `/athlete_add/1/` zwrócił 200,
a POST z poprawnymi danymi formularza i hasłem `x` utworzył konto.
Testowy klient nie wymuszał CSRF; rzeczywisty klient może pobrać token
z publicznie dostępnego formularza. CSRF nie zastępuje autoryzacji.

Naprawa: poprawna krotka i zakotwiczone wzorce (`^admin(?:/|$)`), dokładne
dopasowanie loginu oraz kontrola uprawnień w samych widokach.

## 2. Wysokie: brak autoryzacji obiektów i operacji

`CrossBoxManager/views.py:49`, `:73`, `:99`, `:157`, `:193`, `:234`, `:355`:
widoki nie sprawdzają członkostwa w klubie ani uprawnień zarządzającego.
Middleware sprawdza wyłącznie logowanie. ID klubu i osoby pochodzą z URL;
`PersonModifyView` pobiera osobę bez ograniczenia do wskazanego klubu.
Analogiczny brak sprawdzenia dotyczy odbiorcy i nadawcy wiadomości.

Skutki: odczyt danych osobowych członków cudzych klubów, modyfikacja danych
klubu (w tym konta bankowego), tworzenie pracowników z flagą managera,
zmiana danych użytkowników i ról klubowych oraz wiadomości między klubami.
Flaga managera nie oznacza uprawnień administratora Django.

Potwierdzenie: konto sportowca z punktu 1 wykonało POST `/club_modify/1`;
odpowiedź 302, a pole `bank_account` zostało zmienione w bazie.

Naprawa: wspólna kontrola członkostwa i ról dla GET oraz POST, filtrowanie
obiektów po klubie, ograniczenie edycji ról i tworzenia klubów do uprawnionych
użytkowników. Dodać testy prób dostępu między klubami i eskalacji ról.

## 3. Wysokie: ujawniony klucz i ustawienia deweloperskie

`SportManager/settings.py:23–28`: stały `SECRET_KEY` w repozytorium,
`DEBUG = True`, pusta lista hostów. Jeżeli klucz był używany na wdrożeniu,
należy go wymienić; samo usunięcie z bieżącego pliku nie usuwa go z historii.
Klucz umożliwia fałszowanie danych podpisywanych przez Django; wpływ na sesje
zależy od używanego backendu (domyślny backend tego projektu jest bazodanowy).
DEBUG może ujawniać kod, zmienne i szczegóły błędów przy dostępności serwera.

`manage.py check --deploy` zgłosił 6 ostrzeżeń: brak HSTS, przekierowania HTTPS,
secure cookies sesji i CSRF, włączony DEBUG oraz puste ALLOWED_HOSTS.
Konfiguracja reverse proxy i `localsettings.py` nie była dostępna do oceny.

Naprawa: sekret z konfiguracji środowiska, bezpieczne domyślne ustawienia,
konkretne hosty oraz konfiguracja HTTPS odpowiednia dla wdrożenia.

## 4. Średnie: brak walidacji siły haseł i ograniczenia logowania

`CrossBoxManager/forms.py:14–29`, `CrossBoxManager/views.py:178`, `:214`:
`create_user()` hashuje hasło, ale nie wywołuje walidatorów haseł.
Formularze nie wywołują `validate_password`; zaakceptowano hasło `x`.
`LoginView` nie ma ograniczenia prób logowania w kodzie projektu.
Nie można wykluczyć limitowania na poziomie niewidocznej infrastruktury.

Naprawa: walidacja hasła z danymi tworzonego użytkownika oraz ograniczenie
prób logowania z uwzględnieniem konta i źródła żądania.

## 5. Niskie: wylogowanie przez GET

`CrossBoxManager/views.py:38–41`: GET zmienia stan sesji; cudza strona może
spowodować wylogowanie przez nawigację do `/logout/`.
Naprawa: POST z tokenem CSRF oraz formularz zamiast linku w szablonach.

## Zależności

Źródło wyników: pip-audit 2.10.1, baza PyPI, skan 2026-09-16.
Pełne dane: [przed migracją](dependency-audit-before.json)
i [po migracji](dependency-audit-after.json).
W starym pliku skaner zwrócił 108 wpisów podatności w 6 pakietach;
wynik zawiera powtórzenia identyfikatorów, więc nie oznacza 108 różnych CVE.
Występowanie podatnego pakietu nie dowodzi wykorzystania konkretnej luki
w aplikacji.

| Pakiet | Stara wersja | Przykład podatności |
| --- | --- | --- |
| Django | 4.2.9 | CVE-2024-24680 |
| djangorestframework | 3.14.0 | CVE-2024-21520 |
| sqlparse | 0.4.4 | CVE-2024-4340 |
| black | 23.12.1 | CVE-2024-21503 |
| click | 8.1.7 | CVE-2026-7246 |
| soupsieve | 2.5 | CVE-2026-49477 |

Django 4.2 zakończyło wsparcie w kwietniu 2026:
[harmonogram Django](https://www.djangoproject.com/download/).
Przeniesiono aplikację do Django 5.2 LTS. Stary `django-bootstrap-v5`
wymaga Django <5, dlatego zastąpiono go `django-bootstrap5` i zmieniono nazwę
aplikacji oraz biblioteki tagów w szablonie bazowym.
Black i pip-audit są w grupie dev, a zależności pośrednie rozwiązuje uv.
`backports.zoneinfo` nie jest potrzebny przy wymaganym Pythonie >=3.10.
Zachowano DRF i psycopg2-binary z poprzedniej konfiguracji, choć domyślny kod
nie korzysta z DRF, a baza jest SQLite.

Skan całego nowego środowiska (łącznie z narzędziami dev) zakończył się kodem 0:
**No known vulnerabilities found**. Nie stanowi to gwarancji braku nowych
lub nieujawnionych podatności. Dokładne wersje i hashe są w `uv.lock`.

## Weryfikacja migracji

- Python 3.12.3, `uv sync`: poprawne rozwiązanie i instalacja zależności.
- `manage.py check`: brak błędów.
- `manage.py makemigrations --check --dry-run`: brak zmian modeli.
- `manage.py test`: repozytorium nie zawiera testów (0 uruchomionych).
- Na tymczasowej bazie wykonano migracje oraz sprawdzono logowanie,
  renderowanie listy klubów, szczegółów klubu i listy osób (HTTP 200).
- Skompilowano wszystkie szablony aplikacji z nową biblioteką Bootstrap.
- Potwierdzono możliwość anonimowego tworzenia konta i zmiany konta bankowego
  przez sportowca. Tymczasową bazę usunięto po sprawdzeniu.

Priorytet dalszej pracy: zamknąć anonimowe tworzenie kont, wdrożyć autoryzację
obiektów i ról, wymienić używany klucz i poprawić konfigurację wdrożenia.
