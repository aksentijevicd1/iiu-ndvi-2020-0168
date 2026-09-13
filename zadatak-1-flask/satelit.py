import os
from datetime import datetime, timedelta, timezone
from math import sqrt
from dotenv import load_dotenv

import numpy as np
import requests
from rasterio.io import MemoryFile
from rasterio.warp import transform

load_dotenv()

TOKEN_URL = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
KATALOG_URL = 'https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search'
PROCESS_URL = 'https://sh.dataspace.copernicus.eu/api/v1/process'

POLUPRECNIK = 1000
VELICINA_SLIKE = 200
REZOLUCIJA_M = 10

EVALSCRIPT = """
//VERSION=3
function setup() {
  return { input: ["B03", "B04", "B08"], output: { bands: 3, sampleType: "FLOAT32" } };
}
function evaluatePixel(uzorak) {
  return [uzorak.B03, uzorak.B04, uzorak.B08];
}
"""


def obradi_parcelu(lat, lon, povrsina_ha):
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    sada = datetime.now(timezone.utc)
    pocetak = sada - timedelta(days=90)

    odgovor = requests.post(
        TOKEN_URL,
        data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        },
        timeout=30
    )
    odgovor.raise_for_status()
    zaglavlje = {'Authorization': 'Bearer ' + odgovor.json()['access_token']}

    pretraga = {
        'collections': ['sentinel-2-l2a'],
        'bbox': [lon - 0.01, lat - 0.01, lon + 0.01, lat + 0.01],
        'datetime': pocetak.strftime('%Y-%m-%dT%H:%M:%SZ') + '/' + sada.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'filter': 'eo:cloud_cover < 10',
        'filter-lang': 'cql2-text',
        'limit': 100
    }
    odgovor = requests.post(KATALOG_URL, headers=zaglavlje, json=pretraga, timeout=30)
    odgovor.raise_for_status()
    scene = odgovor.json().get('features', [])
    if not scene:
        raise RuntimeError('Nema Sentinel-2 snimka sa manje od 10% oblaka u poslednjih 90 dana.')

    scena = max(scene, key=lambda s: s['properties']['datetime'])
    dan = scena['properties']['datetime'][:10]

    x, y = transform('EPSG:4326', 'EPSG:32634', [lon], [lat])
    okvir = [
        x[0] - POLUPRECNIK,
        y[0] - POLUPRECNIK,
        x[0] + POLUPRECNIK,
        y[0] + POLUPRECNIK
    ]

    zahtev = {
        'input': {
            'bounds': {
                'bbox': okvir,
                'properties': {'crs': 'http://www.opengis.net/def/crs/EPSG/0/32634'}
            },
            'data': [{
                'type': 'sentinel-2-l2a',
                'dataFilter': {
                    'timeRange': {
                        'from': dan + 'T00:00:00Z',
                        'to': dan + 'T23:59:59Z'
                    }
                }
            }]
        },
        'output': {
            'width': VELICINA_SLIKE,
            'height': VELICINA_SLIKE,
            'responses': [{
                'identifier': 'default',
                'format': {'type': 'image/tiff'}
            }]
        },
        'evalscript': EVALSCRIPT
    }
    odgovor = requests.post(PROCESS_URL, headers=zaglavlje, json=zahtev, timeout=120)
    odgovor.raise_for_status()

    with MemoryFile(odgovor.content) as memorija:
        with memorija.open() as izvor:
            zeleni, crveni, nir = izvor.read().astype('float32')

    ndvi = (nir - crveni) / (nir + crveni + 0.0001)
    ndwi = (zeleni - nir) / (zeleni + nir + 0.0001)

    sredina = ndvi.shape[0] // 2
    polovina_px = max(1, round(sqrt(float(povrsina_ha) * 10000) / (2 * REZOLUCIJA_M)))
    parcela = slice(sredina - polovina_px, sredina + polovina_px)
    ndvi_parcele = round(float(ndvi[parcela, parcela].mean()), 3)
    ndwi_parcele = round(float(ndwi[parcela, parcela].mean()), 3)

    return {
        'datum': dan,
        'ndvi': ndvi_parcele,
        'ndwi': ndwi_parcele
    }
