import sqlite3
from flask import Flask, g, jsonify, request, render_template
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
