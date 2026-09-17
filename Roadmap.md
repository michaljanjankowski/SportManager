# Roadmapa rozwoju SportManager / CrossBox

Plan na podstawie przekazanej rozmowy o kierunku rozwoju projektu.
Data opracowania: 2026-09-17.

## Cel produktu

Rozwijać istniejący SportManager jako **CrossBox — platformę zarządzania
boxami functional fitness, CrossFit, HYROX i weightlifting**. Pierwsza wersja
komercyjna ma obsługiwać grafik, rezerwacje, obecności, karnety i płatności,
a następnie dostarczać właścicielowi informacje o kondycji biznesu.

Główny proces zawodnika:

**Grafik → rezerwacja lub lista oczekujących → trening → check-in → wynik → historia / PR.**

Pierwszy cel operacyjny: jeden prawdziwy box prowadzi cały tygodniowy grafik
w aplikacji, wygodnej również na telefonie.

## Zasady i zakres

| Decyzja | Zakres |
| --- | --- |
| Zachować | Django 5.2, PostgreSQL, Docker Compose, uv i CI |
| Zachować | Szablony Django + Bootstrap jako frontend MVP |
| Zachować i rozwijać | Obsługę wielu klubów, role klubowe oraz wyniki zawodników |
| Przebudować | Autoryzację, członkostwo i role booleanowe na model uprawnień w klubie |
| Przebudować | Powiązanie zawodnika z kontem na User + członkostwo w klubie |
| Przebudować | Treningi na szablony zajęć i konkretne sesje w grafiku |
| Zbudować | Rezerwacje, limity miejsc, waitlist, obecności, karnety, płatności i dashboard |
| Odłożyć | Plan żywieniowy, Stravę, social/community, sprzęt, zawody i rozbudowane wiadomości |

Wykorzystać istniejący kod i dane. Zmiany modeli wprowadzać migracjami,
bez rozpoczynania projektu od nowa. Odłożenie funkcji nie oznacza usuwania
ich kodu. Integrację z operatorem płatności rozpocząć po potwierdzeniu
zainteresowania pilotem.

## Kolejność i bramki realizacji

| Etap | Priorytet | Rezultat umożliwiający przejście dalej |
| --- | --- | --- |
| 0 — SECURITY | P0 | Bezpieczne przetwarzanie danych prawdziwego klubu |
| 1 — BOOKING MVP | P1 | Jeden box prowadzi tygodniowy grafik i zapisy w aplikacji |
| 2 — MONEY | P1 | Właściciel zarządza karnetami i wpłatami bez osobnego Excela |
| 3 — BUSINESS | P2 | Dashboard wspiera codzienną pracę właściciela |
| 4 — PERFORMANCE | P2 | Zawodnik zapisuje wyniki i śledzi postępy |

Etap 0 blokuje pilot z rzeczywistymi danymi. Terminy ustalić po oszacowaniu
zadań; rozmowa nie określa dat ani czasu trwania etapów.
Niezaznaczone zadania poniżej wymagają wykonania lub potwierdzenia.

## Etap 0 — SECURITY: bezpieczeństwo przed pilotem

**Cel:** zamknąć krytyczne i wysokie problemy z
[audytu bezpieczeństwa](docs/security-audit.md) oraz sprawdzić izolację klubów.
Audyt opisuje stan z 2026-09-16. Obecnie
[CrossBoxManager/tests.py](CrossBoxManager/tests.py) zawiera już testy widoków
klubu i wiadomości; nie należy traktować informacji z rozmowy o „0 testów”
jako aktualnego stanu. Ich obecność nie potwierdza zamknięcia całego audytu.

### Zadania

- [x] Zweryfikować aktualny stan każdego problemu z audytu i udokumentować naprawy.
- [x] Naprawić `LOGIN_EXEMPT_URLS` oraz dokładne dopasowanie ścieżek publicznych.
- [x] Zablokować anonimowe tworzenie kont poza świadomie zaprojektowanym procesem rejestracji.
- [x] Wprowadzić `ClubMembership`: `user`, `club`, `role`, `status`, `joined_at`.
- [x] Wprowadzić role `OWNER`, `MANAGER`, `COACH`, `MEMBER` zamiast flag booleanowych.
- [x] Zdefiniować macierz uprawnień do danych klubu, członków, grafiku i finansów.
- [x] Wymagać aktywnego członkostwa i właściwej roli dla każdej operacji GET i POST.
- [x] Filtrować odczyty i modyfikacje obiektów po klubie, także po identyfikatorach z URL i formularzy.
- [x] Ograniczyć zmianę ról, tworzenie personelu i klubów do uprawnionych użytkowników.
- [x] Przygotować migrację dotychczasowych profili i ról bez niezamierzonego podniesienia uprawnień.
- [ ] Zweryfikować stare konta managerów i aktywować zaufane członkostwa na wdrożeniu.
- [x] Przenieść sekret do konfiguracji środowiska i usunąć stały klucz z ustawień.
- [ ] Wymienić wcześniej używany klucz na rzeczywistym wdrożeniu i unieważnić stare sesje.
- [x] Przygotować konfigurację produkcyjną: `DEBUG=False`, hosty, HTTPS, secure cookies i HSTS odpowiednie dla infrastruktury.
- [x] Włączyć walidację haseł i ograniczanie prób logowania.
- [x] Zmienić wylogowanie na POST z CSRF.
- [x] Dodać testy anonimowego dostępu, eskalacji ról i odczytu/zapisu między klubami.
- [x] Uruchamiać testy uprawnień w CI i zweryfikować konfigurację przez `check --deploy`.

Implementacja i instrukcja wdrożenia: [Etap 0 — zabezpieczenia](docs/stage0-security.md).
Kod i testy są wdrożone w repo; pilot wymaga jeszcze działań na docelowej infrastrukturze.

### Kryteria ukończenia

- Anonimowy użytkownik nie tworzy kont przez chronione endpointy.
- Zawodnik nie zmienia danych finansowych klubu ani ról personelu.
- Użytkownik klubu A nie odczytuje ani nie modyfikuje danych klubu B.
- Wszystkie krytyczne i wysokie problemy audytu mają potwierdzone naprawy.
- Testy regresji przechodzą, a ustawienia produkcyjne są zweryfikowane.

## Etap 1 — BOOKING MVP: grafik i rezerwacje

**Cel:** jeden prawdziwy box obsługuje cały tygodniowy grafik przez CrossBox.

### Zadania

- [ ] Uporządkować klub, zawodników i trenerów wokół konta User i członkostwa.
- [ ] Ustalić mapowanie obecnego `SportClub` na docelowe `Organization` i `Location`.
- [ ] Wprowadzić `ClassTemplate` dla typów zajęć: CrossFit, Weightlifting, HYROX, Open Gym.
- [ ] Wprowadzić `ClassSession`: data i godzina, trener, lokalizacja oraz limit miejsc.
- [ ] Obsłużyć cykliczny grafik oraz zmianę lub odwołanie pojedynczej sesji.
- [ ] Przygotować tygodniowy grafik i szczegóły zajęć czytelne na telefonie.
- [ ] Wprowadzić `Booking`: zapis zawodnika i anulowanie rezerwacji.
- [ ] Egzekwować limit miejsc i zapobiegać podwójnym zapisom, także przy równoczesnych żądaniach.
- [ ] Wprowadzić listę oczekujących i ustalić zasady przejmowania zwolnionego miejsca.
- [ ] Ustalić zasady anulowania, terminy zapisów i obsługi nieobecności.
- [ ] Wprowadzić `Attendance` i check-in dostępny dla trenera lub managera.
- [ ] Udostępnić trenerowi listę uczestników, a zawodnikowi jego rezerwacje.
- [ ] Przetestować pełny proces na telefonie i przeprowadzić pilot w jednym boxie.

### Kryteria ukończenia

- Właściciel tworzy tygodniowy grafik, a trener widzi uczestników swoich sesji.
- Zawodnik rezerwuje miejsce lub trafia na waitlist i może anulować zapis.
- Równoczesne zapisy nie przekraczają pojemności zajęć.
- Check-in zapisuje obecność, a dane pozostają odizolowane między klubami.
- Box prowadzi pełny tydzień zajęć w aplikacji; uwagi z pilota są zapisane i priorytetyzowane.

## Etap 2 — MONEY: karnety i płatności

**Cel:** właściciel przestaje prowadzić członkostwa i wpłaty w Excelu.

### Zadania

- [ ] Wprowadzić `MembershipPlan`: cena, okres ważności oraz limit wejść lub unlimited.
- [ ] Wprowadzić `Subscription`: przypisanie planu zawodnikowi i okres rozliczeniowy.
- [ ] Obsłużyć statusy subskrypcji: `active`, `paused`, `overdue`, `cancelled`.
- [ ] Ustalić zasady zużycia wejść przy rezerwacji, obecności, anulowaniu i nieobecności.
- [ ] Powiązać uprawnienie do rezerwacji z ważnością karnetu i dostępnymi wejściami.
- [ ] Wprowadzić `Payment`: kwota, okres, termin oraz status `paid`, `pending`, `failed`.
- [ ] Umożliwić managerowi ręczne odnotowanie wpłaty i korekty z historią zmian.
- [ ] Udostępnić listę zaległości i podstawowe przypomnienia o płatności.
- [ ] Pokazać zawodnikowi ważność karnetu, pozostałe wejścia i stan opłat.
- [ ] Umożliwić przeniesienie danych karnetów i wpłat używanych przez pilotażowy box.
- [ ] Zweryfikować limity wejść, zmiany statusów i uprawnienia do danych finansowych.

### Kryteria ukończenia

- Manager zarządza planami, karnetami i ręcznie potwierdza płatności.
- System wskazuje zaległości i egzekwuje uzgodnione zasady dostępu do zajęć.
- Zawodnik widzi aktualny stan swojego karnetu.
- Pilotażowy box prowadzi pełny okres rozliczeniowy w aplikacji.

**Po walidacji pilota:** osobno zaplanować integrację operatora płatności,
płatności cykliczne i obsługę zdarzeń rozliczeniowych.

## Etap 3 — BUSINESS: dashboard i retention

**Cel:** właściciel codziennie otwiera aplikację, aby sprawdzić stan biznesu.

### Zadania

- [ ] Zdefiniować metryki: aktywni członkowie, wpływy, MRR, frekwencja, churn i retention.
- [ ] Rozróżnić rzeczywiście otrzymane wpłaty od MRR wynikającego z aktywnych subskrypcji.
- [ ] Pokazać liczbę aktywnych członków, miesięczne wpływy i zaległe płatności.
- [ ] Pokazać dzisiejsze zajęcia z obłożeniem, trenerem i listą uczestników.
- [ ] Wskazać zawodników długo nieaktywnych, ze spadkiem frekwencji lub kończącym się karnetem.
- [ ] Ustalić z pilotem progi alertów i okresy porównania frekwencji.
- [ ] Zapewnić przejście z alertu do osoby i konkretnego działania managera.
- [ ] Wprowadzić podstawowy podgląd trendów frekwencji, odejść i utrzymania członków.
- [ ] Zweryfikować obliczenia na danych pilota i ograniczyć dostęp do wskaźników biznesowych.

### Kryteria ukończenia

- Właściciel z jednego ekranu widzi dzisiejszy grafik, obłożenie i stan finansów.
- Każda metryka ma jasną definicję oraz określony okres pomiaru.
- Alerty wskazują konkretne osoby wymagające uwagi i są użyteczne w pilocie.
- Dashboard korzysta z rzeczywistych danych rezerwacji, obecności i płatności.

## Etap 4 — PERFORMANCE: wyniki i postępy

**Cel:** zawodnik korzysta z aplikacji również dla historii własnych wyników.

### Zadania

- [ ] Wprowadzić `Workout` i przypisywanie treningu do sesji.
- [ ] Uporządkować istniejące wyniki i wprowadzić `PerformanceResult`.
- [ ] Ustalić formaty wyników: czas, liczba powtórzeń, ciężar i wariant skalowania.
- [ ] Umożliwić zapis oraz korektę wyniku zawodnika w ramach właściwych uprawnień.
- [ ] Udostępnić historię wyników i rekordy osobiste (PR).
- [ ] Wprowadzić klubowy leaderboard z zasadami porównywania wyników i widoczności danych.
- [ ] Zweryfikować obliczanie PR, porównywalność wyników i izolację klubów.

### Kryteria ukończenia

- Zawodnik zapisuje wynik po treningu i przegląda swoją historię.
- Rekordy osobiste są wyliczane dla porównywalnych ćwiczeń i wariantów.
- Ranking respektuje zakres klubu i ustalone zasady widoczności.

## Docelowy model domeny

Model z rozmowy jest kierunkiem rozwoju, a nie obowiązkiem jednorazowego
przepisania wszystkich modeli. `ClubMembership` z etapu 0 musi pozostać
spójnym źródłem uprawnień przy późniejszym wprowadzaniu organizacji i lokalizacji.
Szczegóły rozdzielenia członkostwa personelu i zawodników ustalić przed migracją.

| Obszar | Docelowe encje | Etap |
| --- | --- | --- |
| Dostęp | User, ClubMembership, role i status członkostwa | 0 |
| Organizacja | Organization, Location, StaffMembership, Member | 1, rozwój wraz z potrzebami pilota |
| Grafik | ClassTemplate, ClassSession | 1 |
| Udział | Booking, waitlist, Attendance | 1 |
| Karnety i rozliczenia | MembershipPlan, Subscription, Payment | 2 |
| Wyniki | Workout, PerformanceResult, PR | 4 |

## Praca z roadmapą

- Każdy etap kończyć sprawdzeniem jego kryteriów ukończenia.
- Do zadań dopisywać odnośniki do issues/PR oraz zaznaczać je po weryfikacji.
- Po pilocie aktualizować priorytety na podstawie problemów właściciela, trenerów i zawodników.
- Funkcje odłożone wracają do planu dopiero po potwierdzeniu potrzeby; nie blokują pierwszej wersji komercyjnej.

Dokumenty odniesienia: [specyfikacja](Specification_202401.md),
[audyt bezpieczeństwa](docs/security-audit.md),
[instrukcja uruchomienia](README_PL.md).
