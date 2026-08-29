import sqlite3
import csv

conn = sqlite3.connect('baza.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS parcele(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naziv VARCHAR(255) NOT NULL,
    lokacija VARCHAR(255) NOT NULL,
    lat REAL,
    lon REAL,
    povrsina_ha REAL
               );
    ''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS merenja(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parcela_id INTEGER NOT NULL,
    datum VARCHAR(10) NOT NULL,
    ndvi REAL NOT NULL,
    ndwi REAL,
    klasifikacija VARCHAR(20) NOT NULL,
    izvor VARCHAR(20) NOT NULL DEFAULT 'satelit',
    FOREIGN KEY (parcela_id) REFERENCES parcele(id)
               );
    ''')

lista_parcela = []
with open('parcele.csv', mode='r', encoding='utf-8', newline='') as parcele_fajl:
    reader = csv.DictReader(parcele_fajl)
    for row in reader:
        lista_parcela.append(row)

lista_merenja = []
with open('merenja.csv', mode='r', encoding='utf-8', newline='') as merenja_fajl:
    reader = csv.DictReader(merenja_fajl)
    for row in reader:
        lista_merenja.append(row)

parcele = [tuple(parcela.values()) for parcela in lista_parcela]
merenja = [tuple(merenje.values()) for merenje in lista_merenja]

cursor.execute("SELECT COUNT(*) FROM parcele")
if cursor.fetchone()[0] == 0:
    cursor.executemany("INSERT INTO parcele (naziv, lokacija, lat, lon, povrsina_ha) VALUES (?,?,?,?,?)", parcele)
    cursor.executemany("INSERT INTO merenja (parcela_id, datum, ndvi, ndwi, klasifikacija, izvor) VALUES (?,?,?,?,?,?)", merenja)

print('Baza uspesno kreirana, tabele parcele i merenja su dostupne')

conn.commit()
conn.close()
