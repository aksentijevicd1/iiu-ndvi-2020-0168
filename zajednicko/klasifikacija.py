DEGRADIRANA = 'degradirana'
SUVA = 'suva'
ZDRAVA = 'zdrava'

BOJE = {
    DEGRADIRANA: (255, 0, 0),
    SUVA: (255, 200, 0),
    ZDRAVA: (0, 255, 0)
}


def klasifikuj(ndvi):
    if ndvi < 0.2:
        return DEGRADIRANA
    if ndvi < 0.4:
        return SUVA
    return ZDRAVA


def boja(stanje):
    return BOJE.get(stanje, (0, 0, 0))
