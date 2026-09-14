# Procena stanja vegetacije — NDVI / NDWI

Domaći zadaci i seminarski rad iz predmeta **Internet inteligentnih uređaja**,
Fakultet organizacionih nauka, Univerzitet u Beogradu, 2026.

Student: Dušan Aksentijević, 2020/0168

## O projektu

Sistem za praćenje stanja vegetacije na poljoprivrednim parcelama, sa dva izvora
podataka:

1. **Satelitski sloj** — Flask aplikacija na zahtev preuzima Sentinel-2 snimak sa
   Copernicus servisa, računa NDVI i NDWI, pravi mapu i upisuje merenje u bazu.
2. **Terenski sloj** — Arduino stanica sa senzorom vlage zemljišta i temperature,
   koja istu klasifikaciju određuje na licu mesta i prikazuje je RGB diodom.

Oba sloja upisuju merenja u istu aplikaciju (zadatak 1), gde se porede.

## Klasifikacija

| NDVI | Stanje | Boja |
|---|---|---|
| < 0.2 | degradirana / gola površina | crvena |
| 0.2 – 0.4 | slaba / suva vegetacija | žuta |
| ≥ 0.4 | zdrava vegetacija | zelena |

Referentna definicija je u [zajednicko/klasifikacija.py](zajednicko/klasifikacija.py);
svaki zadatak nosi svoju kopiju pragova, da bi se mogao pokrenuti sam za sebe.

## Struktura

```
zadatak-1-flask/            Flask, SQLite, REST API, veb stranica i Sentinel-2 obrada
zadatak-2-projektovanje/    projektovanje pametnog okruženja (Floorplanner)
zadatak-3-arduino/          analogni senzori + RGB dioda (Arduino, Wokwi, Fritzing)
zadatak-4-rpi/              Arduino → Raspberry Pi → Flask JSON servis
zajednicko/                 referentna definicija pragova
```

## Pokretanje

```
python -m venv .venv
.venv\Scripts\activate
```

Objedinjena Flask aplikacija:

```
cd zadatak-1-flask
pip install -r requirements.txt
Copy-Item .env.example .env
python database_setup.py
python app.py
```

U `.env` treba uneti podatke Copernicus OAuth klijenta:

```env
CLIENT_ID=tvoj-client-id
CLIENT_SECRET=tvoj-client-secret
```

Aplikacija se otvara na `http://127.0.0.1:5000`. Izborom parcele i klikom na
**Preuzmi sa satelita** preuzima se najnoviji odgovarajući Sentinel-2 snimak,
računaju se NDVI i NDWI, prikazuju mapa i udeli klasa, a rezultat se upisuje u
postojeću listu merenja.

Zadatak 4 — servis terenske stanice (bez Arduina vraća probno očitavanje):

```
cd zadatak-4-rpi
pip install -r requirements.txt
python servis.py
```

## Hardver

| Komponenta | Model |
|---|---|
| Mikrokontroler | Arduino Uno R3 |
| Mikroračunar | Raspberry Pi 4 Model B |
| Vlaga zemljišta | kapacitivni senzor v1.2 (A0) |
| Temperatura | TMP36 (A1) |
| Signalizacija | RGB LED, zajednička katoda, 3 × 220 Ω (D9, D10, D11) |

Kolo je simulirano u Wokwi-ju; šeme su crtane u Fritzingu.
