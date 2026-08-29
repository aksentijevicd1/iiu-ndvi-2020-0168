# Procena stanja vegetacije — NDVI / NDWI

Domaći zadaci iz predmeta **Internet inteligentnih uređaja**
Fakultet organizacionih nauka, Univerzitet u Beogradu — 2026.

Student: Dušan Aksentijević, 2020/0168

## O projektu

Sistem za praćenje stanja vegetacije na konkretnoj parceli, sa dva nezavisna
izvora podataka koji se porede:

1. **Satelitski sloj** — snimci Sentinel-2 sa programa Copernicus. Iz njih se
   računaju indeksi NDVI i NDWI, na osnovu kojih se površina klasifikuje kao
   *zdrava*, *suva* ili *degradirana* vegetacija.
2. **In-situ sloj** — terenska stanica sa analognim senzorima (vlaga zemljišta,
   osvetljenost, temperatura) koja istu klasifikaciju određuje na licu mesta i
   signalizira je RGB diodom.

Terenska stanica služi kao provera satelitske procene — postupak poznat kao
*ground truth* validacija u daljinskoj detekciji.

### Indeksi

Računaju se iz Sentinel-2 kanala: B3 (zeleni), B4 (crveni), B8 (NIR), B11 (SWIR).

| Indeks | Formula | Šta meri |
|---|---|---|
| NDVI | `(B8 − B4) / (B8 + B4)` | gustina i vitalnost vegetacije |
| NDWI (McFeeters) | `(B3 − B8) / (B3 + B8)` | vodene površine |
| NDMI / NDWI (Gao) | `(B8 − B11) / (B8 + B11)` | sadržaj vode u biljci |

### Klasifikacija

Isti pragovi važe kroz ceo projekat — i u Python servisu i u Arduino kodu:

| NDVI | Stanje | Boja RGB diode |
|---|---|---|
| < 0.20 | degradirana / gola površina | crvena |
| 0.20 – 0.40 | slaba / suva vegetacija | žuta |
| ≥ 0.40 | zdrava vegetacija | zelena |

Definisani su na jednom mestu: [zajednicko/klasifikacija.py](zajednicko/klasifikacija.py)

## Struktura

```
zajednicko/                 indeksi i pragovi klasifikacije, deljeni kroz sve zadatke
zadatak-1-flask/            Python aplikacija: SQLite baza + REST veb servisi
zadatak-2-projektovanje/    projektovanje pametnog okruženja (plastenik)
zadatak-3-arduino/          analogni senzori + RGB dioda
zadatak-4-rpi/              Arduino → Raspberry Pi → Flask JSON servis
```

## Zadaci

| # | Zadatak | Tehnologije |
|---|---|---|
| 1 | Aplikacija sa bazom i veb servisima | Python, Flask, SQLite |
| 2 | Projektovanje pametnog okruženja | Floorplanner |
| 3 | Analogni senzori i RGB signalizacija | Arduino Uno R3, Fritzing |
| 4 | Prenos podataka na RPi i JSON servis | Arduino, Raspberry Pi 4, Flask |

## Hardver

| Komponenta | Model |
|---|---|
| Mikrokontroler | Arduino Uno R3 |
| Mikroračunar | Raspberry Pi 4 Model B (4 GB) |
| Vlaga zemljišta | kapacitivni senzor v1.2 (analogni, A0) |
| Osvetljenost | LDR GL5528 + delitelj 10 kΩ (A1) |
| Temperatura | TMP36 (A2) |
| Signalizacija | RGB LED, zajednička katoda + 3 × 220 Ω (D9, D10, D11) |

## Pokretanje

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r zadatak-1-flask/requirements.txt
python zadatak-1-flask/database_setup.py
python zadatak-1-flask/app.py
```

Aplikacija se pokreće na `http://127.0.0.1:5000`.
