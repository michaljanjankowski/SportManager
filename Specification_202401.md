# Cross(fit) Box Manager

## Założenia techniczne

- UI: wprowadzić HTML Bootstrap.
- Rozważyć wykorzystanie sygnałów Django.
- Wprowadzić deployment z Docker Compose.
- Wprowadzić REST Framework.

## Nawigacja i funkcje interfejsu

1. Kluby: zobacz kluby, dodaj klub, modyfikuj klub. Kliknięcie klubu otwiera drugi poziom nawigacji.
2. W obrębie klubu:
   - Zobacz ludzi w klubie: wyświetl wszystkich, modyfikuj osobę, wyślij wiadomość.
   - Dodaj ludzi w klubie: otwórz formularz dodania.
   - Zobacz treningi: wyświetl treningi.

## Tabele i zasoby

### Box (klub)

- Nazwa.
- Adres.
- NIP.
- Numer konta.
- Założyciel.
- Kadra — relacja jeden do wielu z kadrą.
- Sale — relacja jeden do wielu z salami.
- Sprzęty — relacja jeden do wielu ze sprzętami.
- Zawodnicy — relacja jeden do wielu z zawodnikami.
- Aktualny harmonogram pracy — relacja jeden do wielu z treningami.
- Skrzynia wiadomości — relacja jeden do wielu z wiadomościami.

### Wiadomości

- Data wysłania.
- Od kogo.
- Do kogo.
- Czy przeczytana?
- Treść.
- Box.

### Kadra / personel

- `isManager`.
- `isSkarbnik`.
- `isTrener`.
- Box.

### Zawodnik

- Imię.
- Nazwisko.
- Email.
- Box.

### Trening

- Dzień tygodnia.
- Godzina.
- Nazwa, np. weightlifting.
- Czy aktywny?
- Box.

### Event treningowy

- Data.
- Prowadzący.
- Uczestnicy.
- Plan.
- Sprzęt dla jednej osoby.
- Relacja jeden do wielu z treningiem.

### Sale / pomieszczenia

- Nazwa sali.
- Liczba miejsc.
- Box.

### Sprzęt

- Nazwa sprzętu.
- Ilość sprzętu.

## Role i uprawnienia

### Skarbnik / administrator

- Pobiera opłaty.
- Wysyła na email monity o brak zapłaty.
- Raportuje managerowi stan przychodów.
- Raportuje managerowi stan kosztów: sali, mediów, sprzętu i utrzymania kadry.

### Manager klubu

- Zakłada klub.
- Może zarządzać kilkoma klubami.
- Ma uprawnienia skarbnika.
- Może dodać skarbnika.
- Może dodać trenera do kadry.
- Przypisuje trenera do treningu.

### Zawodnik — zalogowany

- Płaci abonament.
- Otrzymuje i wysyła wiadomości do innych zawodników.
- Otrzymuje i wysyła wiadomości do trenerów.
- Może zapisać się na trening.
- Może zapisać się na zawody.
- Dodaje swoje dokonania z Endomondo.

Atrybuty zawodnika:

- Dane personalne.
- Treningi, w których wziął udział.
- Uzyskane wyniki — ważne z psychologicznego punktu widzenia w MVP.

### Trener

- Dane personalne.

## Planowanie

### Plan pracy klubu

- Okres obowiązywania: od–do.

### Szczegóły eventu treningowego

- Jeden trener prowadzący zajęcia.
- Zawodnicy biorący udział.
- Plan treningu i ćwiczeń.
- Czas: od–do.
- Miejsce.
- Potrzebny sprzęt (MVP).

### Plan żywieniowy zawodnika

- Autor: jeden trener.
- Zawodnik: dla kogo jest plan?
- Skład posiłków / plan posiłków.

### Zawody

- Trener prowadzący na zawody.

## Integracje i pomysły

- Integracja ze Stravą.
- Możliwość logowania przez Facebook.
