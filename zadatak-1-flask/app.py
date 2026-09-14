import sqlite3
from pathlib import Path
from flask import Flask, g, jsonify, request, render_template, url_for
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = 'baza.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def klasifikuj(ndvi):
    if ndvi < 0.2:
        return 'degradirana'
    if ndvi < 0.4:
        return 'suva'
    return 'zdrava'



@app.route("/")
def index():
    return render_template('index.html')

@app.route('/api/parcele', methods=['GET'])
def get_parcele():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM parcele ORDER BY id")
    parcele = cursor.fetchall()
    return jsonify([dict(parcela) for parcela in parcele])

@app.route('/api/merenja', methods=['GET'])
def get_merenja():
    parcela_id = request.args.get('parcela_id')
    db = get_db()
    cursor = db.cursor()
    if parcela_id:
        cursor.execute("SELECT * FROM merenja WHERE parcela_id = ? ORDER BY datum", (parcela_id,))
    else:
        cursor.execute("SELECT * FROM merenja ORDER BY datum")
    merenja = cursor.fetchall()
    return jsonify([dict(merenje) for merenje in merenja])

@app.route('/api/merenja', methods=['POST'])
def add_merenje():
    novo_merenje = request.json
    if not novo_merenje or 'parcela_id' not in novo_merenje or 'datum' not in novo_merenje or 'ndvi' not in novo_merenje:
        return jsonify({'error':'Polja parcela_id, datum i ndvi su obavezna'}),400

    parcela_id = novo_merenje['parcela_id']
    datum = novo_merenje['datum']
    ndvi = novo_merenje['ndvi']
    ndwi = novo_merenje.get('ndwi')
    izvor = novo_merenje.get('izvor', 'satelit')
    klasifikacija = klasifikuj(ndvi)

    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO merenja (parcela_id, datum, ndvi, ndwi, klasifikacija, izvor) VALUES (?,?,?,?,?,?)",(parcela_id, datum, ndvi, ndwi, klasifikacija, izvor))
    db.commit()
    return jsonify({'id':cursor.lastrowid, 'parcela_id':parcela_id, 'datum':datum, 'ndvi':ndvi, 'ndwi':ndwi, 'klasifikacija':klasifikacija, 'izvor':izvor}), 201

@app.route('/api/parcele/<int:parcela_id>/satelitsko-merenje', methods=['POST'])
def add_satelitsko_merenje(parcela_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM parcele WHERE id = ?", (parcela_id,))
    parcela = cursor.fetchone()
    if parcela is None:
        return jsonify({'error': 'Parcela ne postoji'}), 404

    try:
        from satelit import obradi_parcelu
        mapa_relativna = f'mape/parcela-{parcela_id}.png'
        mapa_putanja = Path(app.root_path) / 'static' / mapa_relativna
        mapa_putanja.parent.mkdir(parents=True, exist_ok=True)
        rezultat = obradi_parcelu(
            parcela['lat'],
            parcela['lon'],
            parcela['povrsina_ha'],
            mapa_putanja
        )
    except Exception as error:
        app.logger.exception('Greska pri preuzimanju satelitskog merenja')
        return jsonify({'error': str(error)}), 502

    cursor.execute(
        "SELECT * FROM merenja WHERE parcela_id = ? AND datum = ? AND izvor = 'satelit'",
        (parcela_id, rezultat['datum'])
    )
    postojece = cursor.fetchone()
    if postojece is not None:
        odgovor = dict(postojece)
        odgovor['poruka'] = 'Merenje za ovaj satelitski snimak vec postoji.'
        odgovor['udeo_povrsine'] = rezultat['udeo_povrsine']
        odgovor['mapa_url'] = url_for('static', filename=mapa_relativna)
        return jsonify(odgovor), 200

    klasifikacija = klasifikuj(rezultat['ndvi'])
    cursor.execute(
        "INSERT INTO merenja (parcela_id, datum, ndvi, ndwi, klasifikacija, izvor) VALUES (?,?,?,?,?,?)",
        (parcela_id, rezultat['datum'], rezultat['ndvi'], rezultat['ndwi'], klasifikacija, 'satelit')
    )
    db.commit()
    return jsonify({
        'id': cursor.lastrowid,
        'parcela_id': parcela_id,
        'datum': rezultat['datum'],
        'ndvi': rezultat['ndvi'],
        'ndwi': rezultat['ndwi'],
        'klasifikacija': klasifikacija,
        'izvor': 'satelit',
        'udeo_povrsine': rezultat['udeo_povrsine'],
        'mapa_url': url_for('static', filename=mapa_relativna)
    }), 201

@app.route('/api/merenja/<int:merenje_id>', methods=['PUT'])
def update_merenje(merenje_id):
    izmena = request.json
    if not izmena or 'ndvi' not in izmena:
        return jsonify({'error':'Polje ndvi je obavezno'}),400

    ndvi = izmena['ndvi']
    klasifikacija = klasifikuj(ndvi)

    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE merenja SET ndvi = ?, klasifikacija = ? WHERE id = ?",(ndvi, klasifikacija, merenje_id))
    db.commit()
    if cursor.rowcount==0:
        return jsonify({'error':'Merenje ne postoji'}), 404
    return jsonify({'id':merenje_id, 'ndvi':ndvi, 'klasifikacija':klasifikacija}), 200

@app.route('/api/merenja/<int:merenje_id>', methods=['DELETE'])
def delete_merenje(merenje_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM merenja WHERE id = ?",(merenje_id,))
    db.commit()
    if cursor.rowcount==0:
        return jsonify({'error':'Merenje ne postoji'}), 404
    return jsonify({'message':f'Merenje sa id-em {merenje_id} je uspesno obrisano'}), 200

if __name__=='__main__':
    app.run(debug=True, port=5000)
