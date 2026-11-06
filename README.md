**🏠 OrbitaCasa 🇮🇹 [![Sito Web](https://img.shields.io/badge/SITO_UFFICIALE-VISITA-4f46e5?style=flat-square&logo=google-chrome&logoColor=white)](https://renato-4132.github.io/OrbitaCasa/)**

**Il centro di comando per la tua gestione domestica, dalle spese quotidiane al risparmio intelligente.**

<img width="882" height="463" alt="logo" src="https://github.com/user-attachments/assets/642def87-3203-4ffe-a728-5c52f06119c2" />

---

![Windows](https://img.shields.io/badge/Windows-✔️-blue?style=flat-square&logo=windows&logoColor=white)
![macOS](https://img.shields.io/badge/macOS-✔️-lightgrey?style=flat-square&logo=apple&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-✔️-yellow?style=flat-square&logo=linux&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-✔️-2496ED?style=flat-square&logo=docker&logoColor=white)
![Android](https://img.shields.io/badge/Android-App_companion-3DDC84?style=flat-square&logo=android&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white)
![Versione](https://img.shields.io/badge/VERSIONE-2.5.7-orange?style=flat-square)
![Licenza](https://img.shields.io/badge/LICENZA-BSL_1.1-4f46e5?style=flat-square)
![Visite](https://visitor-badge.laobi.icu/badge?page_id=Renato-4132.OrbitaCasa&left_text=VISITE%20TOTALI&color=4f46e5)
![Installazioni](https://visitor-badge.laobi.icu/badge?page_id=Renato-4132.OrbitaCasa.Installazioni&left_text=INSTALLAZIONI%20TOTALI&color=22c55e)

---

**🏆 COME CI VEDONO**

[![FinanzaCafona](https://img.shields.io/badge/FinanzaCafona-Top_3_App_Budget_Familiare-4f46e5?style=flat-square&logo=google-chrome&logoColor=white)](https://finanzacafona.it/2026/05/app-per-gestire-il-budget-familiare.html)

> *"Questa è forse la chicca dell'articolo e l'app per gestire il budget familiare più completa fra tutte"* — [FinanzaCafona, Maggio 2026](https://finanzacafona.it/2026/05/app-per-gestire-il-budget-familiare.html)

---

**🚀 L'ESSENZA DEL SOFTWARE**

**OrbitaCasa** è un ecosistema progettato per chi vuole il controllo totale sulle proprie finanze senza rinunciare alla **Privacy**. Unisce la potenza di un software gestionale alla semplicità di un'app domestica.

* 🛡️ **Zero Cloud di default**: i tuoi dati restano sul tuo PC. IA, sync mail e accessi remoti li fanno uscire solo se li attivi tu.
* 💰 **Smart Saving**: algoritmi per il confronto prezzi e il risparmio.
* 📱 **Mobile Ready**: app Android dedicate (OrbitaWeb e OrbitaNotify), accesso da browser con biometria e QR per scaricare gli APK.
* 📑 **Paperless**: archiviazione digitale di tutti i tuoi documenti PDF.
* 🔓 **Niente canoni**: gratis, con una licenza "viva" che si allunga più la usi (vedi sotto).
  
> **Nota tecnica sulla sync:** OrbitaCasa evita deliberatamente le API bancarie (PSD2) per proteggere la privacy dell'utente ed evitare i costi di sottoscrizione che renderebbero il progetto a pagamento. Crediamo in un software libero da canoni e da occhi indiscreti.

**🏅 LICENZA VIVA — GRATIS, A PUNTI**

<details> <summary><b>Clicca per i dettagli sulla licenza</b></summary>

Non paghi mai, ma la licenza non è "per sempre" a prescindere: più usi l'app, più sali di livello, più si allunga. Ogni traguardo raggiunto estende in automatico la scadenza.

Il codice è distribuito con licenza Business Source License 1.1: è consultabile e gratuito da usare, entro i limiti indicati nel file LICENSE del repository. Dal 15 maggio 2029 (Change Date) diventa GNU GPL v3.

</details>

**⚠️ NOVITÀ**

<details>
<summary><b>Clicca per conoscere le ultime novità (v2.5.7)</b></summary>

È uscita la versione **2.5.7** di OrbitaCasa, l'app desktop per gestire le spese di casa.
Il pezzo grosso: ora il telefono può inserire i movimenti al posto tuo.

**📲 Notifiche → spese, da qualsiasi app**

L'app Android **OrbitaNotify** legge le notifiche di qualsiasi app che ne manda (banca, carte, wallet, negozi…) e inoltra a OrbitaCasa quelle che parlano di soldi, per esempio "hai pagato 100 € di bolletta".
Vengono lette con regole testuali e, se non bastano, interviene Gemini.
Ne nasce una spesa proposta che confermi con un clic, oppure che si registra da sola se lo decidi tu per quella app.

Tu decidi cosa può entrare:

- Ogni app ha la sua regola, e può essere protetta da una parola chiave personale, così non vengono autorizzati movimenti che non hai richiesto
- Filtri a parole incluse ed escluse per far passare solo le notifiche giuste
- Categoria, conto, metodo e tag vengono ricordati per ogni app
- I doppioni vengono saltati e finiscono nel log

In OrbitaCasa trovi la finestra "Notifiche e spese da confermare", con un indicatore rosso nella schermata principale.
Il collegamento è protetto da un token, con blocco dell'IP dopo 10 tentativi falliti.

**🤖 OrbitaNotify (Android)**

- Canale Orbita accanto a Mail, Telegram e ntfy, anche più canali insieme
- Registrazione automatica a scelta per ogni app (mai, solo con regole fisse, sempre)
- Invio ritentato se manca la rete, password e token cifrati sul telefono

**🌐 OrbitaWeb e QR di download**

- Nuova app Android **OrbitaWeb** per collegarsi dal telefono al server web di OrbitaCasa
- Nella finestra "Gestione Accessi Remoti" c'è un QR per scaricare l'APK, e nella finestra Info quelli di OrbitaNotify e OrbitaWeb, con il link sotto
- Il link punta sempre all'ultima release

**🔧 Accessi remoti più facili**

Nuovo pulsante "Verifica connessione": controlla se il server è attivo, se ascolta sulla rete di casa e se il dominio punta al tuo IP pubblico, e ti dice cosa controllare se il telefono non si collega.

**📧 Sync mail**

Per ogni regola per mittente, la casella "Gemini compila i campi vuoti": sceglie tipo, categoria, conto e metodo solo tra quelli già esistenti, senza toccare mai i campi compilati a mano.

</details>

---

**🔥 POTENZA IN 80+ FUNZIONI**

<details>
<summary><b>Clicca per vedere tutte le funzioni</b></summary>

---

**🟠 Inserimento Manuale o Automatico**

1. **Importazione Estratti** — PDF e CSV da banca, stipendi, cedolini, spese — il punto di ingresso di tutto
2. **Sincronizzazione Gmail** — Fatture scaricate e archiviate in automatico dall'email
3. **Archivio Documenti Contabili PDF** — Ogni movimento collegato al suo documento — tutto aggregato in un posto
4. **Scansione Documenti da Scanner** — Acquisisci i fogli da scanner USB o di rete direttamente in un PDF, con Analisi AI opzionale
5. **Scansiona e salva PDF** — Scansiona e salva il PDF dove vuoi, senza archiviarlo
6. **SmartCat** — Categorizza da solo basandosi sullo storico — l'utente non ci pensa
7. **Gestione Ricorrenze** — Inserisci una volta affitto, abbonamenti, stipendio — poi dimentica
8. **Spese Pianificate** — Dilaziona una spesa in quote automatiche fino alla cifra prefissata
9. **Agenda & Promemoria** — Appuntamenti e scadenze su calendario, con ripetizioni, avvisi ed email

---

**🟢 Fondamenta operative**

10. **Saldo Bancario** — Riconciliazione immediata — quanto ho davvero sul conto
11. **Calendario Heartbeat** — Vista globale degli impegni finanziari nel tempo
12. **Ricerca Multi-Filtro** — Trova qualsiasi movimento in un istante
13. **Sicurezza Password** — Accesso protetto — dati finanziari, non si scherza
14. **Backup & Ripristino** — Automatico, incrementale, con snapshot e rollback integrato
15. **Promemoria Categorie** — Avvisi su spese ricorrenti dimenticate rispetto ai mesi passati
16. **Profili Multi-Utente** — Database separati per più persone o nuclei familiari: ognuno con i propri movimenti, categorie e credenziali
17. **Esportazione TXT/PDF/Stampa** — I dati sempre esportabili nel formato che serve
18. **Configurazione** — Tutto configurabile, dati sempre sicuri e portabili
19. **Azzeramento Dati Selettivo** — Resetta un singolo ambito senza toccare il resto del database
20. **Vai al Movimento** — Doppio clic su una spesa e la raggiungi nella lista principale
21. **Controllo Estratti (Riconciliazione)** — Confronto tra database ed estratti di conti e carte, con "Importa Mancanti"

---

**🔵 Analisi e controllo**

22. **Grafici Drill-Down** — Analisi visiva profonda — dove vanno davvero i soldi
23. **Analisi Categorie** — Finestra unica a tab: Dettaglio, Aggrega, Time Machine, Trend, Budget superato, Target
24. **Monitoraggio Budget per Categoria** — Avviso quando si supera la soglia di spesa, mensile o annuale
25. **Fondo Risparmio** — Tracking risparmi accantonati e obiettivi
26. **Simulatore Risparmio** — Calcola come e quando raggiungere un obiettivo
27. **Proiezioni Finanziarie** — Rendite, spese e patrimonio nel futuro
28. **Stampa Report** — Documentazione professionale pronta all'uso
29. **Analisi Finanziaria con IA** — Analisi intelligente dell'andamento complessivo
30. **Chiedi al Database con l'IA** — Domande in linguaggio naturale su tutti i moduli, con storico ed export PDF/TXT
31. **Calcolo Inflazione** — Tasso reale calcolato sullo storico personale
32. **Invio Estratti Mail** — Distribuzione automatica dei report
33. **Analisi Mese** — Cruscotto e Saldi conti del mese
34. **Metodo 50/30/20** — Entrate divise in Bisogni 50%, Desideri 30%, Risparmio 20%, con classe assegnata a ogni categoria e andamento mensile/annuale

---

**🟡 Strumenti avanzati**

35. **Gestione Immobili** — Entrate/uscite per immobile, estratto conto, riepilogo
36. **AutoPark — Gestione Veicoli** — Scadenze bollo/assicurazione/revisione, consumi, costo al km, spese per veicolo
37. **Gestione MyBusiness** — Agenda, preventivi, fatturazione, magazzino
38. **Gestione Associativa e Multiconto** — Associazione tra entità contabili e conti bancari
39. **Finanziamenti, Mutui e Prestiti** — Rate, variazioni ed estinzioni, piano di ammortamento e simulatori, anche da browser
40. **Algoritmo FairShare** — Ripartizione equa spese tra più persone, quote calcolate al centesimo
41. **Conti Personali FairShare** — Conto individuale per tracciare spese nel gruppo
42. **Estratto Analitico & Dare/Avere** — Chi deve cosa a chi, con filtri per stato e ordinamento
43. **CommunityPool** — Dividi le spese senza svelare il resto dei tuoi conti: pubblichi solo ciò che vuoi, il resto resta tuo
44. **Mercati Finanziari** — Monitoraggio real-time indici e asset globali
45. **Portafoglio Investimenti** — Titoli e asset con prezzi live e controvalore
46. **Monitor Utenze** — Consumi di luce, gas e acqua sotto controllo
47. **Manutenzione e Risparmio Casa** — Calendario manutenzioni periodiche per impianti ed elettrodomestici
48. **Confronto Prezzi** — Ottimizza la spesa alimentare nel tempo
49. **Analizzatore Semantico IA** — Analisi intelligente e confronto multi-documento
50. **Fondo Pensione** — Piano, versamenti per tipologia, valorizzazioni e riscatti/anticipazioni
51. **Portafoglio Bancario Multi-Conto** — Riepilogo di tutti i conti con distribuzione per categoria
52. **Trasferimenti tra Conti** — Pianifica trasferimenti singoli o in serie ricorrenti tra conti
53. **Conto Risparmio Automatico** — Ogni uscita di una categoria Risparmio genera il trasferimento al conto risparmio
54. **Notifiche Email Pianificate** — Report multipli programmabili con frequenza personalizzata
55. **StockBox (Magazzino)** — Magazzino generico per tutto ciò che vuoi tenere in scorta, con scorta minima e massima

---

**🟣 Telefono, Web e Automazioni**

56. **OrbitaNotify: notifiche → spese** — L'app Android legge le notifiche di banca, carte e negozi e le trasforma in spese da confermare (o registrate in automatico, per app)
57. **OrbitaWeb (app Android)** — Collega il telefono al server web di OrbitaCasa
58. **Home e Calendario web** — Pagina iniziale a tessere e calendario cliccabile con i movimenti del giorno
59. **Webserver Remoto** — Consulta i dati da smartphone anche in remoto, con agenda, chat IA, pagina Mutui e Prestiti, accesso biometrico e "Verifica connessione"
60. **Movimenti da Web** — Inserimento, modifica e ricerca avanzata con tag, orario e metodo di pagamento
61. **Chiedi all'IA da Browser** — La chat sui tuoi dati anche dal telefono, con i dati che restano sul tuo PC
62. **StockBox da Telefono** — Carica e scarica articoli con il barcode e ricava la Lista spesa dalle scorte
63. **Docker & Accesso via Browser** — OrbitaCasa su server o NAS, usato da qualsiasi PC o tablet
64. **QR di Download App** — Gli APK delle app Android sempre all'ultima release, da scansionare

---

**⚫ Specialistiche e comfort**

65. **Archivio Documenti Personali** — Documenti sempre a portata di mano, con scadenze
66. **Modulo Dieta** — Pasti, macronutrienti, peso e grafico BMI
67. **Pet Care** — Profili degli animali, vaccinazioni e scadenze veterinarie, promemoria cura e peso sotto controllo
68. **Rubrica Vcard/Android** — Esporta/importa contatti dallo smartphone
69. **Retention Automatica** — Rimuove automaticamente i dati più vecchi
70. **Tasti Shortcut Personali** — Funzioni rapide con combinazioni di tasti
71. **Temi Personalizzabili** — Interfaccia adattata al proprio stile
72. **Smart Info Point** — Tooltip ricchi su movimenti, tabelle, grafici e documenti con statistiche di spesa
73. **Carosello Grafici** — Tour automatico degli andamenti all'avvio
74. **Auto-Iconizza** — Riduzione a icona per inattività
75. **Notifiche Auto-chiudenti** — Avvisi che scompaiono dopo tempo prestabilito
76. **Aggiornamenti Automatici** — App, moduli e librerie Python aggiornati da GitHub, con backup e ripristino
77. **Messaggi di Servizio e Changelog** — Novità e avvisi dentro l'app, senza popup invadenti
78. **Licenza a Punti (Gamification)** — Usa l'app, sali di livello, allunghi la licenza gratuita
79. **Streak & Livelli** — Da Novizio a Leggenda (e oltre): mantieni la costanza giorno dopo giorno e scala i livelli a vita
80. **Badge Mese & Anno** — Oltre al livello a vita, guadagni riconoscimenti dedicati al mese e all'anno in corso
81. **Profilo Demo** — Prova l'app con dati di esempio

</details>

**⚙️ INSTALLAZIONE**

<details>
<summary><b>Clicca per vedere le istruzioni di installazione</b></summary>

**🟦 Windows (Automatico)**

Metodo consigliato per utenti Windows.
1. Scarica l'installer: [**O.C.Win.Installer.zip**](https://github.com/Renato-4132/OrbitaCasa/raw/main/O.C.Win.Installer.zip)
2. Estrai ed esegui il file EXE.
> **Nota:** Rieseguendo l'installer potrai creare nuovi profili utente separati.

**🍎 macOS (Sperimentale)**

Script `.command` che installa Python da solo (se manca) e scarica OrbitaCasa da GitHub. Non ancora testato su tutte le versioni di macOS.
1. Scarica l'installer: [**O.C.Mac_Setup.zip**](https://github.com/Renato-4132/OrbitaCasa/raw/main/O.C.Mac_Setup.zip)
2. Estrai lo zip, poi fai **tasto destro → Apri** sul file `OrbitaCasa_Mac_Installer.command` (il doppio click semplice non basta la prima volta: macOS blocca gli script scaricati da internet).
> ⚠️ **Sperimentale:** in caso di problemi resta valida anche la procedura Manuale qui sotto.

**🟩 Manuale (Tutti i SO)**

**Prerequisito:** Python 3.13+.
> ⚠️ **IMPORTANTE:** Durante l'installazione di Python, spunta la casella **"Add Python to PATH"**.

1. Crea una cartella dedicata (il nome della cartella sarà il tuo **Nome Profilo**).
2. Inserisci il file `OrbitaCasa.pyw` all'interno.
3. Il Software installerà in automatico le dipendenze: tkcalendar google-genai requests flask Pillow segno pywin32 (solo Windows) cryptography pystray pymupdf yfinance tkinterdnd2 webauthn

</details>

**🐳 Docker & Accesso via Browser**

<details>
<summary><b>Clicca per vedere come usare OrbitaCasa con Docker</b></summary>

Esegui OrbitaCasa sul tuo server o NAS tramite Docker e gestisci le tue finanze domestiche direttamente dal browser di qualsiasi PC o tablet remoto, senza installazioni locali.

1. Scarica il pacchetto: [**orbitacasa-docker.zip**](https://github.com/Renato-4132/OrbitaCasa/raw/main/orbitacasa-docker.zip)
2. Estrai lo zip e scegli la cartella giusta: `orbitacasa-docker-linux` per Linux/NAS, `orbitacasa-docker-win-mac` per Windows e macOS.
3. Segui le istruzioni nel file `LEGGIMI.md` della cartella (contiene `Dockerfile` e `docker-compose.yml`).

</details>

**📱 App Android**

<details>
<summary><b>Clicca per vedere le app per il telefono</b></summary>

- **OrbitaWeb**: si collega al server web di OrbitaCasa dal telefono. Repo: [Renato-4132/OrbitaWeb](https://github.com/Renato-4132/OrbitaWeb)
- **OrbitaNotify**: inoltra a OrbitaCasa le notifiche che parlano di soldi, per trasformarle in spese. Repo: [Renato-4132/OrbitaNotify](https://github.com/Renato-4132/OrbitaNotify)

I QR per scaricare gli APK (sempre all'ultima release) sono in OrbitaCasa, nella finestra "Gestione Accessi Remoti" e nella finestra Info.

</details>

**📺 [Guarda il Video](https://github.com/Renato-4132/OrbitaCasa/raw/main/screenshots/OrbitaCasa.mp4)**

📩 **ASSISTENZA TECNICA**

Per bug, suggerimenti o supporto: helporbitacasa@gmail.com

**La storia di OrbitaCasa**

<details>
<summary><b>Dietro le quinte — Da una scrivania tappezzata di post-it a più di 100.000 righe di codice</b></summary>

**Chi c'è dietro**

Mi chiamo Renato e programmo da 40 anni, e in tutto questo tempo ho scritto tante di quelle cose che i pivelli leoni da tastiera di oggi nemmeno se le immaginano.
Non ho una laurea né un titolo di studio, ma non mi sono mai mancate la voglia di imparare e la fantasia per creare cose a cui magari nessuno aveva ancora pensato.
Ho scritto dei software che hanno lasciato una storia.

Poi sono arrivate la famiglia e una lunga pausa, ma senza mai perdere la voglia di creare.

**Colpa dei post-it**

Per anni ho tenuto i conti di casa con un'app sullo smartphone che andava sempre in crash e mi faceva perdere i dati, con un foglio Excel e con un archivio per documenti, fatture e bollette.
Finché un giorno ho visto la mia compagna tappezzare la scrivania di post-it per tenere i conti.
E lì ho detto: così non si può andare avanti.

Classificatori, garanzie, fatture, buste paga: un foglio Excel, per quanto potente, non sarebbe mai arrivato dove volevo io.
Ho scritto 100 righe di codice e l'ho chiamato «Spese».
Dopo un mese si chiamava già CasaFacile, e potevamo inserire i conti e guardarci le statistiche.

**L'ambizione, questa brutta bestia**

Poi, siccome l'ambizione è una brutta bestia (e forse eravamo troppo gasati), è diventato CasaFacilePro.
A maggio l'ho ribattezzato OrbitaCasa.
Non si trattava più di fare due conti: volevo sapere dove fossero le fatture, capire davvero dove andavano i soldi e tenere traccia dei consumi.
Dopo più di una bolletta stratosferica per colpa di una perdita, la cosa era diventata personale.

Il buon Vittorio, su Finanza Cafona, ci ha dedicato una recensione top e l'effetto è stato devastante: in tanti l'hanno installata.
Tra notti insonni, un saggio copia-incolla e un pizzico di IA, siamo arrivati a più di 100.000 righe di codice.

**Cosa sa fare oggi**

Nel frattempo siamo cresciuti.
OrbitaCasa vanta ora oltre 80 funzioni diverse, un manuale di oltre 100 pagine e tante cose che altri software nemmeno si sognano.
Serve a gestire:

- Conti personali e famiglia.
- Finanziamenti personali con gestione delle rate, immobili, parco auto e mezzi e micro-attività.
- Fondi risparmio, gestione della manutenzione casa, gestione dei nostri cari animaletti domestici.
- **Organizzazione chirurgica:** ogni spesa è puntualmente assegnata a uno specifico conto o a un tag dedicato, con in più la possibilità di dilazionare le spese in automatico fino al raggiungimento della quota prefissata.
- **Importazione e archiviazione documentale:** potete importare gli estratti conto per i vostri movimenti, e archiviare in un unico posto documenti, fatture e bollette, anche scansionandoli direttamente dallo scanner di casa.
- **Report ed email automatiche:** l'app vi manda report ed estratti conto giornalieri, settimanali o mensili direttamente via email.
- **Alert di budget:** ti avvisa in tempo reale se sfori la soglia impostata su una categoria.
- **Il "Chi l'ha visto?" delle scadenze:** tiene traccia e avvisa per qualsiasi scadenza immaginabile (documenti, patenti, bollette, revisioni).
- **Architettura locale:** i dati restano sul vostro PC, con tanto di webserver integrato e accesso biometrico da qualsiasi device.
- **Il telefono al lavoro:** le notifiche di banca e carte diventano spese da confermare, grazie alle app Android OrbitaNotify e OrbitaWeb.
- **AI integrata:** analizza le bollette, calcola i costi medi, prevede le spese future e fa un'analisi finanziaria completa (e questi sono gli unici dati che escono, e solo se volete).

**La grande svolta sulla licenza (e basta con le mazzette)**

Visto il tempo investito, all'inizio avevo pensato a un bel canone in abbonamento.
Poi ho capito che mi dà molta più soddisfazione parlare con le persone, cercare di risolvere i loro problemi e leggere i vostri feedback.
Risultato? Nessun abbonamento commerciale.
Ho sempre pensato di tenerlo gratuito, perché tanti «sciagurati» come me potessero iniziare a gestire la propria casa, e tutto quello che le ruota intorno, con semplicità.

Il codice licenza c'è ancora, ma viene concesso completamente gratis.
Ho lasciato tutta la logica per un motivo preciso: tenere traccia di quello che mi chiedete, per potervi ricontattare all'occorrenza.
Visto che per la privacy non conservo né i nomi né i dati, l'unico riferimento è l'ID assegnato a ogni installazione: con quello posso scrivere un log e seguire le richieste di ciascuno.

Poi c'è l'altro motivo: invogliare le persone a usarla davvero, senza lasciarla scadere.
Per questo il sistema assegna dei livelli di utilizzo: chi la usa con costanza viene premiato con l'allungamento automatico della licenza di mese in mese, senza scadenze traumatiche o la rottura di dover fare continue richieste.
Più la usi per metterti in riga, più lei ti regala serenità.

**Per chi è?**

L'idea originaria era nata per aiutare un gruppo di disgraziati della finanza domestica (tipo il sottoscritto).
Poi, tra richieste folli arrivate su Reddit, idee rubate su Facebook e ore passate a studiare podcast e pagine di settore, l'ho resa una suite il cui motto è:

> «Per tanti, ma non per tutti.»

Se cercate una gestione veramente meticolosa delle finanze e di tutto ciò che orbita intorno alla vostra casa (da qui il nome, OrbitaCasa), fateci un giro.

**Grazie**

Devo ringraziare tutti quelli che sono stati presenti in questo percorso.
Prima di tutti Vittorio, che mi ha sempre dato una spinta morale per andare avanti.
Poi i mod, le pagine di finanza su Reddit, chi ha contribuito con le proprie idee (compresi chi lavora in U.C. e I.S.P.) e le pagine Facebook da cui ho preso spunto, come «Maleducati Finanziari» e «La Budgettista».
E voi che leggete e ascoltate sempre con ironia.

Per qualsiasi richiesta resto a disposizione via email.
Grazie e buon divertimento!

*— Renato*

</details>

---

**🌐 SCOPRI DI PIÙ [![Sito Web](https://img.shields.io/badge/SITO_UFFICIALE-VISITA-4f46e5?style=flat-square&logo=google-chrome&logoColor=white)](https://renato-4132.github.io/OrbitaCasa/) [![FaceBook](https://img.shields.io/badge/FaceBook-4f46e5?style=flat-square&logo=google-chrome&logoColor=white)](https://www.facebook.com/orbitahome/)**
