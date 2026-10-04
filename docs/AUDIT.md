# Audit prima dell'implementazione

Data: 4 ottobre 2026. Oggetto: [piano proposto](PIANO.md).

Documento storico della fase precedente all'implementazione. Il successivo
benchmark pilota e le prove eseguite sono descritti nel [README](../README.md)
e nel [report di validazione](PILOT_VALIDATION.md); l'agente non è ancora implementato.

Questo è un audit progettuale svolto prima di implementare e provare l'agente.
Non è una revisione indipendente del codice e non certifica la funzionalità.

## Giudizio

Procedere con un prototipo misurabile e circoscritto è ragionevole. Il progetto
ha potenziale per un portfolio di AI engineering/data engineering. Originalità
del dibattito multi-agente, superiorità del sistema, domanda commerciale e
affidabilità in produzione non sono dimostrate.

Il contributo difendibile è un workflow riproducibile per modifiche Python/SQL
che combina evidenze del repository, critica delle assunzioni, approvazione e
verifica. La qualità del portfolio dipenderà dall'implementazione e dai risultati,
non dal numero di agenti o dal nome del modello.

## Criticità e correzioni richieste

| Rischio | Valutazione | Correzione nel piano / prova richiesta |
| --- | --- | --- |
| Idea già esplorata | Confermato: MetaGPT e ChatDev coprono collaborazione e orchestrazione | Posizionamento specifico sui dati e confronto misurato; nessuna rivendicazione di novità scientifica |
| Troppe categorie di lavoro | Alto nella proposta iniziale | Python/pandas, un caso ML, SQL su copie; PostgreSQL e automazioni amministrative successive |
| Logorrea non definita | Bloccante per una valutazione credibile | Rubrica su riuso, duplicazioni, dipendenze e scope, subordinata alla correttezza |
| Consenso tra agenti uguale a verità | Non valido | Evidenze e test indipendenti; dichiarare blocchi e dubbi |
| Critica sistematica all'utente | Rischio di peggiorare l'esperienza | Controlli con suggerimenti corretti e preferenze legittime; misurare obiezioni inutili |
| Errori correlati dello stesso modello | Probabile, entità non misurata | Proposte indipendenti, scambio simmetrico, confronti con autocritica; nessuna promessa che più ruoli risolvano il problema |
| Costo e ritardo dei doppi cicli | Intrinseci al disegno | Contare chiamate e token reali, limiti, misurare durata e tempo umano |
| Orchestratore come giudice unico | Inadeguato | Controlli deterministici, test e revisione umana con rubrica |
| Cambio modello/provider silenzioso | Può rendere i risultati non confrontabili | Registrare endpoint, modello, versione e parametri; segnalare versioni non fissabili |
| Produzione di codice non verificato | Contrario alla promessa | Esecuzione reale, test pertinenti e stato incompleto esplicito |
| Benchmark troppo piccolo o memorizzato | Cinque famiglie sono solo uno screening | Task nuovi separati per famiglia e limiti dichiarati |
| User simulator compiacente | Può falsare il confronto | Risposte ai chiarimenti prestabilite e uguali per tutte le configurazioni |
| Fine-tuning come scorciatoia | Non giustificato all'inizio | Prima contesto, strumenti e configurazioni; nessun training nell'MVP |
| Dati aziendali via API | Dipende dal provider e dalla configurazione | Dati sintetici/pubblici nel prototipo; requisiti del cliente verificati prima di usarne i dati |
| Docker considerato isolamento sufficiente | Non dimostrato dalla sola disponibilità del daemon | Test di mount, rete, privilegi, risorse e assenza di segreti nel worker |
| Portfolio fatto soltanto di prompt | Poco convincente | Task end-to-end, checkpoint, interruzioni, prove riproducibili e report dei fallimenti |

## Verifica di fattibilità nell'ambiente corrente

Controlli eseguiti, senza installare il progetto o chiamare API a pagamento:

- checkout `/workspace/Agentic-codebase` inizialmente vuoto e senza commit;
- nessun file AGENTS.md trovato nell'ispezione di `/workspace`;
- Python 3.12.14 e uv disponibili;
- Docker presente e daemon raggiungibile (`docker info`: 28.4.0);
- pytest non presente nel PATH corrente: sarà una dipendenza di sviluppo;
- nessun binding secret o requisito runtime dichiarato nella configurazione
  ambiente letta; ZAI_API_KEY, Z_AI_API_KEY e OPENROUTER_API_KEY non presenti
  nel processo, verificando solo presenza e non valori;
- rete configurata con preset package manager, senza domini personalizzati;
  l'accesso ai futuri endpoint di inferenza non è stato verificato.

La disponibilità di Docker non prova che immagini, dataset o isolamento del
worker funzionino. Non è stata eseguita inferenza con nessuno dei candidati.
Le fonti dei casi e i listini secondari sono stati letti, non convalidati mediante
esecuzioni. Alcuni siti di documentazione/listini hanno restituito 403 dal proxy
durante la ricerca; questo non dimostra che un endpoint API sia indisponibile.

Le credenziali e gli eventuali domini necessari saranno configurati dopo la
scelta dell'endpoint. I valori devono essere inseriti nei meccanismi sicuri del
provider/ambiente, non in chat o nei file del repository.

Nessuno di questi prerequisiti impedisce di consolidare il piano. Credenziali,
accesso e budget sono invece necessari prima della campagna con modelli reali.

## Audit delle promesse economiche e tecniche

1. Le tariffe mostrate sono una fotografia di una fonte secondaria, non prezzi
   contrattuali garantiti. Prima della spesa occorre confermarle.
2. Il calcolo di 13,44 USD usa 30 esecuzioni per ciascuno dei tre modelli e
   consumi ipotetici uguali. Non è una stima sperimentale del costo reale.
3. Il tetto proposto di 30–50 USD riguarda lo screening; non l'intero sviluppo,
   il confronto tra architetture o l'operatività mensile.
4. Pesi aperti non significano hosting economico, dati privati sull'API o supporto
   automatico al fine-tuning da parte del provider.
5. Un costo/token inferiore non dimostra un costo/task inferiore. Conteggiare
   errori, retry e interventi umani.
6. La personalizzazione iniziale modifica workflow, contesto e policy, non i
   pesi del modello. Un eventuale hosting privato rimane una fase separata.
7. Non è verificato che GLM sia migliore o più economico di ogni modello chiuso.
   Il portfolio non deve rivendicarlo sulla base della selezione attuale.

## Criteri per procedere, ridurre o fermarsi

### Prima delle prove con modelli reali

- Riprodurre le fixture e verificare che le soluzioni errate vengano respinte.
- Provare il worker isolato; non passare all'esecuzione diretta sull'host se fallisce.
- Configurare un endpoint, confermare limiti/prezzi e un tetto di spesa esplicito.
- Verificare che il consumo sia misurabile e che il limite sia applicato prima
  di nuove richieste, tenendo conto anche delle richieste già in corso.

### Prima di dichiarare l'MVP funzionante

- Completare almeno un task Python e un task SQL realmente utili, con patch e
  verifiche che possano fallire; non basta una conversazione convincente.
- Nessuna modifica del progetto prima dell'approvazione nei test previsti.
- Invalidare un'approvazione dopo un cambiamento materiale del piano/repository.
- Riprendere una sessione senza duplicare azioni; gestire anche fallimenti parziali.
- Fermarsi correttamente al budget o al limite di riparazioni.
- Mostrare un caso di indicazione errata riconosciuta e uno di indicazione
  corretta accettata. Riportare anche i casi in cui il comportamento fallisce.
- Un'altra persona deve poter riprodurre un task seguendo le istruzioni.

Il superamento di questi controlli prova quei comportamenti nel perimetro
testato; non dimostra assenza generale di difetti o sicurezza in produzione.

### Prima di sostenere che il confronto tra agenti aggiunge valore

- Baseline con stesso modello, strumenti, esecutore e criterio di approvazione.
- Confronto anche con autocritica e a budget comparabile.
- Valutazione su famiglie di problemi non usate per ottimizzare i prompt.
- Conteggi appaiati dei successi, regressioni, costi e interventi umani;
  nessuna conclusione basata solo sul giudizio dell'orchestratore.
- Evidenza di un miglioramento utile al manutentore, non soltanto di risposte
  più lunghe o di punteggi estetici più alti.

Se non emerge un vantaggio, pubblicare il risultato. La modalità di confronto
può restare sperimentale; la scelta di renderla predefinita o limitarla ai task
ambigui va riesaminata con l'utente. Non alterare la valutazione per farla vincere.

Se l'agente singolo non completa task utili, lavorare su contesto, strumenti,
modello e verifiche prima di aggiungere nodi e ulteriori agenti.

Se il costo/tempo umano annulla il beneficio, ridurre il perimetro o il numero
di cicli e ripetere le prove; non presentare come efficiente un sistema che
richiede costante supervisione correttiva.

## Evidenze per un portfolio credibile

Una demo riuscita, una demo con arresto motivato, un confronto con baseline e
istruzioni riproducibili rendono il lavoro valutabile. Mostrare codice, diff,
test, consumi e decisioni progettuali è più utile di una sola chat tra ruoli.

Un pilot con una persona tecnica esterna è necessario per una prima verifica
di usabilità. Il benchmark non sostituisce la validazione del bisogno presso
PMI reali. Nessun risparmio di tempo o interesse commerciale è ancora misurato.

## Esito finale dell'audit

Proposta sufficientemente definita per iniziare M0: fixture e runner di
valutazione. Nessuna implementazione applicativa è iniziata in questo audit.
I blocchi prima dell'inferenza sono endpoint, credenziali, accesso e budget;
prima di affermazioni di utilità comparativa servono i risultati sperimentali.

Il piano è coerente a condizione di mantenere il perimetro ristretto, rendere
le approvazioni controlli software e lasciare che i risultati mettano in
discussione anche l'architettura scelta.
