document.addEventListener('DOMContentLoaded', () => {
    const API_PARCELE = 'http://127.0.0.1:5000/api/parcele';
    const API_MERENJA = 'http://127.0.0.1:5000/api/merenja';

    const filterParcela = document.getElementById('filter-parcela');
    const inputParcela = document.getElementById('input-parcela');
    const inputDatum = document.getElementById('input-datum');
    const inputNdvi = document.getElementById('input-ndvi');
    const merenjeForm = document.getElementById('merenje-form');
    const merenjaLista = document.getElementById('merenja-lista');

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

    filterParcela.addEventListener('change', fetchMerenja);

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
