document.addEventListener('DOMContentLoaded', () => {
    const API_PARCELE = 'http://127.0.0.1:5000/api/parcele';
    const API_MERENJA = 'http://127.0.0.1:5000/api/merenja';

    const filterParcela = document.getElementById('filter-parcela');
    const inputParcela = document.getElementById('input-parcela');
    const inputDatum = document.getElementById('input-datum');
    const inputNdvi = document.getElementById('input-ndvi');
    const merenjeForm = document.getElementById('merenje-form');
    const merenjaLista = document.getElementById('merenja-lista');
    const satelitBtn = document.getElementById('satelit-btn');
    const satelitStatus = document.getElementById('satelit-status');
    const satelitRezultat = document.getElementById('satelit-rezultat');
    const satelitDetalji = document.getElementById('satelit-detalji');
    const satelitMapa = document.getElementById('satelit-mapa');

    let parcele = {};

    async function fetchParcele() {
        try {
            const response = await fetch(API_PARCELE);
            if (!response.ok) throw new Error('Network response was not ok');
            const lista = await response.json();

            lista.forEach(parcela => {
                parcele[parcela.id] = parcela.naziv;

                const opcijaFilter = document.createElement('option');
                opcijaFilter.value = parcela.id;
                opcijaFilter.textContent = parcela.naziv;
                filterParcela.appendChild(opcijaFilter);

                const opcijaForma = document.createElement('option');
                opcijaForma.value = parcela.id;
                opcijaForma.textContent = parcela.naziv;
                inputParcela.appendChild(opcijaForma);
            });
        } catch (error) {
            console.error('Failed to fetch parcele:', error);
        }
    }

    async function fetchMerenja() {
        const parcelaId = filterParcela.value;
        const url = parcelaId ? `${API_MERENJA}?parcela_id=${parcelaId}` : API_MERENJA;

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Network response was not ok');
            const merenja = await response.json();

            merenjaLista.innerHTML = '';
            merenja.forEach(merenje => {
                const li = document.createElement('li');
                li.className = 'merenje-item';
                li.dataset.id = merenje.id;

                li.innerHTML = `
                    <span class="oznaka ${merenje.klasifikacija}"></span>
                    <span class="naziv">${parcele[merenje.parcela_id]}</span>
                    <span class="datum">${merenje.datum}</span>
                    <span class="ndvi">NDVI ${merenje.ndvi}</span>
                    <span class="stanje">${merenje.klasifikacija}</span>
                    <button class="delete-btn">Obriši</button>
                `;
                merenjaLista.appendChild(li);
            });
        } catch (error) {
            console.error('Failed to fetch merenja:', error);
            merenjaLista.innerHTML = '<li class="merenje-item">Greška pri učitavanju merenja.</li>';
        }
    }

    filterParcela.addEventListener('change', () => {
        satelitStatus.textContent = '';
        satelitRezultat.hidden = true;
        fetchMerenja();
    });

    satelitBtn.addEventListener('click', async () => {
        const parcelaId = filterParcela.value;
        if (!parcelaId) {
            satelitStatus.textContent = 'Prvo izaberi parcelu.';
            return;
        }

        satelitBtn.disabled = true;
        satelitStatus.textContent = 'Preuzimanje je u toku...';
        satelitRezultat.hidden = true;

        try {
            const response = await fetch(`/api/parcele/${parcelaId}/satelitsko-merenje`, {
                method: 'POST'
            });
            const rezultat = await response.json();
            if (!response.ok) throw new Error(rezultat.error || 'Preuzimanje nije uspelo');

            satelitStatus.textContent = rezultat.poruka || 'Novo satelitsko merenje je dodato.';
            const udeo = rezultat.udeo_povrsine;
            const tumacenjeNdwi = rezultat.ndwi > 0 ? 'prisutna voda' : 'bez izražene vode';
            satelitDetalji.textContent =
                `NDVI ${rezultat.ndvi} (${rezultat.klasifikacija}), ` +
                `NDWI ${rezultat.ndwi} (${tumacenjeNdwi}). U parceli: ` +
                `degradirana ${udeo.degradirana}%, suva ${udeo.suva}%, ` +
                `zdrava ${udeo.zdrava}%, voda ${udeo.voda}%.`;
            satelitMapa.src = `${rezultat.mapa_url}?v=${Date.now()}`;
            satelitRezultat.hidden = false;
            await fetchMerenja();
        } catch (error) {
            satelitStatus.textContent = `Greška: ${error.message}`;
        } finally {
            satelitBtn.disabled = false;
        }
    });

    merenjeForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        try {
            await fetch(API_MERENJA, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    parcela_id: Number(inputParcela.value),
                    datum: inputDatum.value,
                    ndvi: Number(inputNdvi.value)
                })
            });

            inputNdvi.value = '';
            fetchMerenja();
        } catch (error) {
            console.error('Failed to add merenje:', error);
        }
    });

    merenjaLista.addEventListener('click', async (e) => {
        if (e.target.classList.contains('delete-btn')) {
            const merenjeId = e.target.closest('.merenje-item').dataset.id;

            try {
                await fetch(`${API_MERENJA}/${merenjeId}`, {
                    method: 'DELETE'
                });

                fetchMerenja();
            } catch (error) {
                console.error('Failed to delete merenje:', error);
            }
        }
    });

    fetchParcele().then(fetchMerenja);
});
