/**
 * Autocomplétion et suggestions pour les parties
 * - Recherche de parties existantes
 * - Suggestion de normalisation en temps réel
 * - Détection de dossiers similaires
 */

class AutocompleteParties {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            minChars: 2,
            maxResults: 10,
            typePartie: '', // 'physique', 'morale', ou vide
            onSelect: null, // callback(partie)
            ...options
        };

        this.resultsContainer = null;
        this.selectedIndex = -1;
        this.debounceTimer = null;

        this.init();
    }

    init() {
        // Créer le conteneur de résultats
        this.resultsContainer = document.createElement('div');
        this.resultsContainer.className = 'autocomplete-results';
        this.resultsContainer.style.cssText = `
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            width: 100%;
        `;

        // Positionner le conteneur
        this.input.parentElement.style.position = 'relative';
        this.input.parentElement.appendChild(this.resultsContainer);

        // Événements
        this.input.addEventListener('input', () => this.onInput());
        this.input.addEventListener('keydown', (e) => this.onKeydown(e));
        this.input.addEventListener('blur', () => setTimeout(() => this.hide(), 200));
        this.input.addEventListener('focus', () => {
            if (this.input.value.length >= this.options.minChars) {
                this.search(this.input.value);
            }
        });
    }

    onInput() {
        clearTimeout(this.debounceTimer);

        const value = this.input.value.trim();

        if (value.length < this.options.minChars) {
            this.hide();
            return;
        }

        // Debounce pour éviter trop de requêtes
        this.debounceTimer = setTimeout(() => {
            this.search(value);
        }, 300);
    }

    onKeydown(e) {
        const items = this.resultsContainer.querySelectorAll('.autocomplete-item');

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
                this.updateSelection(items);
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.updateSelection(items);
                break;
            case 'Enter':
                if (this.selectedIndex >= 0 && items[this.selectedIndex]) {
                    e.preventDefault();
                    items[this.selectedIndex].click();
                }
                break;
            case 'Escape':
                this.hide();
                break;
        }
    }

    updateSelection(items) {
        items.forEach((item, index) => {
            item.style.backgroundColor = index === this.selectedIndex ? '#e5e7eb' : 'white';
        });
    }

    async search(query) {
        try {
            const params = new URLSearchParams({
                q: query,
                type: this.options.typePartie,
                limite: this.options.maxResults
            });

            const response = await fetch(`/gestion/api/parties/autocomplete/?${params}`);
            const data = await response.json();

            this.showResults(data.resultats, query);
        } catch (error) {
            console.error('Erreur autocomplétion:', error);
        }
    }

    showResults(resultats, query) {
        this.resultsContainer.innerHTML = '';
        this.selectedIndex = -1;

        if (resultats.length === 0) {
            this.resultsContainer.innerHTML = `
                <div style="padding: 10px; color: #888; text-align: center;">
                    <i class="fas fa-info-circle"></i> Aucune partie trouvée pour "${query}"
                    <div style="margin-top: 5px; font-size: 12px;">
                        <a href="#" onclick="event.preventDefault(); document.getElementById('btn-nouvelle-partie')?.click();"
                           style="color: #3b82f6;">
                            + Créer une nouvelle partie
                        </a>
                    </div>
                </div>
            `;
            this.show();
            return;
        }

        resultats.forEach((partie, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.style.cssText = `
                padding: 10px 12px;
                cursor: pointer;
                border-bottom: 1px solid #eee;
                transition: background-color 0.15s;
            `;

            const typeIcon = partie.type === 'morale' ? 'fa-building' : 'fa-user';
            const typeColor = partie.type === 'morale' ? '#3b82f6' : '#10b981';

            item.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fas ${typeIcon}" style="color: ${typeColor};"></i>
                    <div style="flex: 1;">
                        <div style="font-weight: 500;">${this.escapeHtml(partie.label)}</div>
                        ${partie.email ? `<div style="font-size: 12px; color: #888;">${this.escapeHtml(partie.email)}</div>` : ''}
                    </div>
                </div>
            `;

            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f3f4f6';
            });
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = this.selectedIndex === index ? '#e5e7eb' : 'white';
            });

            item.addEventListener('click', () => {
                this.selectPartie(partie);
            });

            this.resultsContainer.appendChild(item);
        });

        this.show();
    }

    selectPartie(partie) {
        this.input.value = partie.label;
        this.input.dataset.partieId = partie.id;
        this.hide();

        if (this.options.onSelect) {
            this.options.onSelect(partie);
        }

        // Déclencher un événement personnalisé
        this.input.dispatchEvent(new CustomEvent('partieSelected', { detail: partie }));
    }

    show() {
        this.resultsContainer.style.display = 'block';
    }

    hide() {
        this.resultsContainer.style.display = 'none';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}


/**
 * Vérification de dossiers similaires
 */
class VerificationDossierSimilaire {
    constructor(formElement, options = {}) {
        this.form = formElement;
        this.options = {
            demandeursSelector: '[name="demandeurs"]',
            defendeursSelector: '[name="defendeurs"]',
            alerteContainer: null,
            ...options
        };

        this.init();
    }

    init() {
        // Créer le conteneur d'alerte s'il n'existe pas
        if (!this.options.alerteContainer) {
            this.alerteContainer = document.createElement('div');
            this.alerteContainer.id = 'alerte-dossiers-similaires';
            this.alerteContainer.style.display = 'none';
            this.form.insertBefore(this.alerteContainer, this.form.firstChild);
        } else {
            this.alerteContainer = this.options.alerteContainer;
        }

        // Observer les changements sur les champs parties
        this.form.addEventListener('change', (e) => {
            if (e.target.matches(this.options.demandeursSelector) ||
                e.target.matches(this.options.defendeursSelector)) {
                this.verifier();
            }
        });

        // Observer les sélections d'autocomplétion
        this.form.addEventListener('partieSelected', () => {
            setTimeout(() => this.verifier(), 100);
        });
    }

    async verifier() {
        const demandeurs = this.getSelectedIds(this.options.demandeursSelector);
        const defendeurs = this.getSelectedIds(this.options.defendeursSelector);

        if (demandeurs.length === 0 || defendeurs.length === 0) {
            this.masquerAlerte();
            return;
        }

        try {
            const params = new URLSearchParams();
            demandeurs.forEach(id => params.append('demandeurs[]', id));
            defendeurs.forEach(id => params.append('defendeurs[]', id));

            const response = await fetch(`/gestion/api/dossiers/verifier-similaire/?${params}`);
            const data = await response.json();

            if (data.alerte) {
                this.afficherAlerte(data.dossiers_similaires);
            } else {
                this.masquerAlerte();
            }
        } catch (error) {
            console.error('Erreur vérification dossiers:', error);
        }
    }

    getSelectedIds(selector) {
        const elements = this.form.querySelectorAll(selector);
        const ids = [];

        elements.forEach(el => {
            if (el.dataset.partieId) {
                ids.push(el.dataset.partieId);
            } else if (el.value && !isNaN(el.value)) {
                ids.push(el.value);
            }
        });

        return ids;
    }

    afficherAlerte(dossiers) {
        let html = `
            <div class="bg-amber-50 border-l-4 border-amber-400 p-4 mb-4">
                <div class="flex items-start">
                    <i class="fas fa-exclamation-triangle text-amber-400 mt-1 mr-3"></i>
                    <div class="flex-1">
                        <h4 class="text-amber-800 font-medium">Dossier(s) existant(s) avec les mêmes parties</h4>
                        <p class="text-amber-700 text-sm mt-1">
                            ${dossiers.length} dossier(s) impliquant les mêmes parties existe(nt) déjà.
                            Vérifiez qu'il ne s'agit pas d'un doublon avant de continuer.
                        </p>
                        <ul class="mt-2 space-y-1">
        `;

        dossiers.forEach(dossier => {
            html += `
                <li class="text-sm">
                    <a href="${dossier.url}" target="_blank" class="text-blue-600 hover:underline">
                        <strong>${dossier.reference}</strong>
                    </a>
                    - ${dossier.intitule || 'Sans intitulé'}
                    <span class="text-gray-500">(${dossier.date_ouverture})</span>
                </li>
            `;
        });

        html += `
                        </ul>
                        <div class="mt-3">
                            <label class="inline-flex items-center text-sm">
                                <input type="checkbox" id="confirmer-nouveau-dossier" class="mr-2">
                                <span class="text-amber-800">Je confirme vouloir créer un nouveau dossier (affaire distincte)</span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.alerteContainer.innerHTML = html;
        this.alerteContainer.style.display = 'block';

        // Bloquer la soumission tant que non confirmé
        const submitBtn = this.form.querySelector('[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;

            document.getElementById('confirmer-nouveau-dossier')?.addEventListener('change', (e) => {
                submitBtn.disabled = !e.target.checked;
            });
        }
    }

    masquerAlerte() {
        this.alerteContainer.style.display = 'none';
        this.alerteContainer.innerHTML = '';

        const submitBtn = this.form.querySelector('[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
        }
    }
}


/**
 * Suggestion de normalisation en temps réel
 */
class SuggestionNormalisation {
    constructor(inputElement, formeElement = null) {
        this.input = inputElement;
        this.formeElement = formeElement;
        this.suggestionDiv = null;
        this.debounceTimer = null;

        this.init();
    }

    init() {
        this.suggestionDiv = document.createElement('div');
        this.suggestionDiv.style.cssText = `
            font-size: 12px;
            color: #059669;
            margin-top: 4px;
            display: none;
        `;
        this.input.parentElement.appendChild(this.suggestionDiv);

        this.input.addEventListener('input', () => this.onInput());
        this.input.addEventListener('blur', () => this.onBlur());
    }

    onInput() {
        clearTimeout(this.debounceTimer);

        const value = this.input.value.trim();
        if (value.length < 3) {
            this.hide();
            return;
        }

        this.debounceTimer = setTimeout(() => {
            this.checkSuggestion(value);
        }, 500);
    }

    onBlur() {
        // Garder la suggestion visible quelques secondes
        setTimeout(() => this.hide(), 3000);
    }

    async checkSuggestion(nom) {
        try {
            const forme = this.formeElement?.value || '';
            const params = new URLSearchParams({ nom, forme });

            const response = await fetch(`/gestion/api/parties/suggerer-normalisation/?${params}`);
            const data = await response.json();

            if (data.suggestion && data.suggestion.a_corriger) {
                this.showSuggestion(data.suggestion);
            } else {
                this.hide();
            }
        } catch (error) {
            console.error('Erreur suggestion:', error);
        }
    }

    showSuggestion(suggestion) {
        let html = `<i class="fas fa-lightbulb mr-1"></i> Suggestion: <strong>${suggestion.nom_suggere}</strong>`;

        if (suggestion.forme_juridique_detectee) {
            html += ` <span class="bg-blue-100 text-blue-700 px-1 rounded">${suggestion.forme_juridique_detectee}</span>`;
        }

        html += ` <button type="button" onclick="this.parentElement.previousElementSibling.value='${suggestion.nom_suggere}'; this.parentElement.style.display='none';"
                         class="ml-2 text-blue-600 hover:underline">Appliquer</button>`;

        this.suggestionDiv.innerHTML = html;
        this.suggestionDiv.style.display = 'block';
    }

    hide() {
        this.suggestionDiv.style.display = 'none';
    }
}


// Export pour utilisation globale
window.AutocompleteParties = AutocompleteParties;
window.VerificationDossierSimilaire = VerificationDossierSimilaire;
window.SuggestionNormalisation = SuggestionNormalisation;
