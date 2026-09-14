import os
from datetime import datetime, timedelta, timezone
from math import sqrt
from dotenv import load_dotenv

import numpy as np
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, Rectangle
from rasterio.io import MemoryFile
from rasterio.warp import transform

load_dotenv()

TOKEN_URL = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
KATALOG_URL = 'https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search'
PROCESS_URL = 'https://sh.dataspace.copernicus.eu/api/v1/process'

POLUPRECNIK = 1000
VELICINA_SLIKE = 200
REZOLUCIJA_M = 10
KLASE = ['degradirana', 'suva', 'zdrava', 'voda']
BOJE = ['#d62728', '#ffcc00', '#2ca02c', '#1f77b4']

EVALSCRIPT = """
//VERSION=3
function setup() {
  return { input: ["B03", "B04", "B08"], output: { bands: 3, sampleType: "FLOAT32" } };
}
function evaluatePixel(uzorak) {
  return [uzorak.B03, uzorak.B04, uzorak.B08];
}
"""


def obradi_parcelu(lat, lon, povrsina_ha, mapa_putanja):
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
    klase = np.where(ndvi < 0.2, 0, np.where(ndvi < 0.4, 1, 2))
    klase[ndwi > 0] = 3

    sredina = ndvi.shape[0] // 2
    polovina_px = max(1, round(sqrt(float(povrsina_ha) * 10000) / (2 * REZOLUCIJA_M)))
    parcela = slice(sredina - polovina_px, sredina + polovina_px)
    ndvi_parcele = round(float(ndvi[parcela, parcela].mean()), 3)
    ndwi_parcele = round(float(ndwi[parcela, parcela].mean()), 3)
    klase_parcele = klase[parcela, parcela]
    udeo_povrsine = {
        klasa: round(100 * float((klase_parcele == i).mean()), 1)
        for i, klasa in enumerate(KLASE)
    }

    fig, ose = plt.subplot_mosaic(
        [['ndvi', 'ndwi'], ['klase', 'klase']],
        figsize=(10, 11)
    )
    prikaz = ose['ndvi'].imshow(ndvi, cmap='RdYlGn', vmin=-0.2, vmax=0.9)
    ose['ndvi'].set_title('NDVI')
    plt.colorbar(prikaz, ax=ose['ndvi'], fraction=0.046)

    prikaz = ose['ndwi'].imshow(ndwi, cmap='BrBG', vmin=-0.6, vmax=0.4)
    ose['ndwi'].set_title('NDWI')
    plt.colorbar(prikaz, ax=ose['ndwi'], fraction=0.046)

    ose['klase'].imshow(klase, cmap=ListedColormap(BOJE), vmin=0, vmax=3)
    ose['klase'].set_title('Klasifikacija stanja vegetacije')
    ose['klase'].legend(
        handles=[Patch(color=boja, label=klasa) for boja, klasa in zip(BOJE, KLASE)],
        loc='lower left'
    )

    for osa in ose.values():
        osa.set_xticks([])
        osa.set_yticks([])
        osa.add_patch(Rectangle(
            (parcela.start, parcela.start),
            2 * polovina_px,
            2 * polovina_px,
            fill=False,
            edgecolor='black',
            linewidth=1.5
        ))

    fig.suptitle('Sentinel-2, ' + dan)
    plt.tight_layout()
    fig.savefig(mapa_putanja, dpi=120)
    plt.close(fig)

    return {
        'datum': dan,
        'ndvi': ndvi_parcele,
        'ndwi': ndwi_parcele,
        'udeo_povrsine': udeo_povrsine
    }
