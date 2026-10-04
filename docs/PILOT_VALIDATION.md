# Validazione del pilota 0.1.0

Eseguita il 4 ottobre 2026. Nessuna API LLM utilizzata.

Comandi verificati dal checkout:

```bash
uv sync --frozen
uv run python -m unittest discover -s tests -v
uv run pmi-bench self-test --output runs/pilot-self-test-02.json
uv run pmi-bench export --output exports/pmi-bench-pilot-0.1.0
```

## Runner e isolamento

14 test del runner superati, 0 fallimenti e 0 skip. Comprendono una probe Docker reale: utente non privilegiato, capability assenti, no-new-privileges, mount e filesystem in sola lettura, scratch scrivibile, nessuna rotta esterna, nessun socket Docker e nessun passaggio di un marcatore sintetico dell’ambiente host. Sono controlli specifici, non una prova generale contro codice ostile.

La prima esecuzione della probe ha individuato permessi troppo restrittivi nella fixture della probe (umask). Sono stati corretti esplicitamente e la suite completa è stata rieseguita con successo. Il runner di staging dei candidati impostava già i permessi necessari.

## Candidati di calibrazione

| Scenario | Candidato | Passati | Falliti | Errori candidato | Skip | Esito atteso osservato |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| invoice_import | baseline | 3 | 3 | 2 | 0 | Sì |
| invoice_import | reference | 8 | 0 | 0 | 0 | Sì |
| invoice_import | mutation | 6 | 2 | 0 | 0 | Sì |
| local_ai_client | baseline | 3 | 7 | 0 | 0 | Sì |
| local_ai_client | reference | 10 | 0 | 0 | 0 | Sì |
| local_ai_client | mutation | 9 | 1 | 0 | 0 | Sì |
| sales_report | baseline | 2 | 5 | 0 | 0 | Sì |
| sales_report | reference | 7 | 0 | 0 | 0 | Sì |
| sales_report | mutation | 5 | 2 | 0 | 0 | Sì |

Le tre reference superano complessivamente 25/25 controlli. Le tre baseline difettose e le tre regressioni vengono respinte da controlli effettivamente eseguiti. Nessun timeout, errore infrastrutturale o skip è stato usato come evidenza di rilevamento di un bug. Gli errori del candidato sono eccezioni rilevate dal test, riportate separatamente dalle asserzioni fallite.

Il test sui proxy azzera anche l’opener globale urllib, così la decisione non dipende dalla cache di chiamate precedenti. I server e i marcatori di dati privati sono sintetici e locali al container.

[Report JSON completo con hash e risultati](validation/pilot-self-test.json).

## Export

Export locale riuscito: 3 scenario_group e 9 righe tasks.jsonl, workspace iniziali, dataset card e checksum. Un test verifica che due export abbiano gli stessi contenuti e che non includano evaluator o reference. Una bozza ZIP è disponibile nella cartella locale exports. Nessun caricamento su Kaggle è stato effettuato.

## Interpretazione

Queste prove validano il comportamento del runner e la capacità dei test di distinguere alcuni candidati noti. Non misurano GLM, un altro modello, la superiorità del multi-agente, la qualità del piano o l’approvazione nel dialogo. Il pilota è un insieme pubblico di sviluppo, non un test set nascosto o una competizione resistente a manipolazioni.
