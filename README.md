# Raspored AI Projekat

Projekat automatski generiše i optimizuje raspored nastave za Odsjek za matematičke i kompjuterske nauke PMF-a. Raspored se prvo formira kao validan početni raspored, a zatim se poboljšava pomoću dva metaheuristička algoritma:

* Simulirano kaljenje
* Artificial Bee Colony

Cilj projekta je dobiti raspored koji nema hard constraint greške i koji ima što manji fitness. Manji fitness znači bolji raspored.

## Korištene tehnologije

Projekat je implementiran u Pythonu. Za generisanje grafika koristi se `matplotlib`, za PDF rasporede koristi se `reportlab`, a za statističku obradu može se koristiti `scipy`.

Instalacija potrebnih paketa:

```bash
pip install -r requirements.txt
```

## Struktura projekta

```text
raspored-ai-projekat/
│
├── data/
│   ├── predmeti.csv
│   ├── osoblje.csv
│   ├── studenti.csv
│   ├── ucionice.csv
│   ├── termini.csv
│   └── ogranicenja.csv
│
├── src/
│   ├── main.py
│   ├── modeli.py
│   ├── parser.py
│   ├── parametri.py
│   ├── validacija.py
│   ├── generator_dogadjaja.py
│   ├── inicijalni_raspored.py
│   ├── hard_constraints.py
│   ├── fitness.py
│   ├── simulirano_kaljenje.py
│   ├── artificial_bee_colony.py
│   ├── eksperimenti.py
│   └── pdf_export.py
│
├── requirements.txt
└── README.md
```

## Ulazni podaci

Ulazni CSV fajlovi nalaze se u folderu `data/`.

| Fajl              | Opis                                                           |
| ----------------- | -------------------------------------------------------------- |
| `predmeti.csv`    | Predmeti, smjerovi, ciklus, semestar i fond sati za P, AV i LV |
| `osoblje.csv`     | Nastavnici i asistenti koji izvode nastavu                     |
| `studenti.csv`    | Procijenjeni broj studenata po smjeru, ciklusu i godini        |
| `ucionice.csv`    | Učionice, kapaciteti i oznaka da li je učionica laboratorija   |
| `termini.csv`     | Dostupni termini nastave                                       |
| `ogranicenja.csv` | Hard i soft ograničenja korištena u projektu                   |

## Glavni parametri

Parametri algoritama nalaze se u fajlu:

```text
src/parametri.py
```

Trenutne vrijednosti:

```python
BROJ_POKRETANJA_EKSPERIMENTA = 30

SA_BROJ_ITERACIJA = 600
SA_POCETNA_TEMPERATURA = 500.0
SA_HLADJENJE = 0.99

ABC_BROJ_CIKLUSA = 70
ABC_BROJ_IZVORA = 4
ABC_LIMIT = 15

NAJKASNIJI_KRAJ_NASTAVE = 19
```

To znači da se u eksperimentima svaki algoritam pokreće 30 puta. Nastava se ne može održavati poslije 19:00.

## Pokretanje kompletnog projekta

Najjednostavnije pokretanje cijelog projekta:

```bash
python src/main.py all
```

Ova komanda redom izvršava:

1. validaciju ulaznih podataka,
2. generisanje nastavnih događaja,
3. generisanje inicijalnog rasporeda,
4. provjeru hard constraint ograničenja,
5. računanje početnog fitnessa,
6. pokretanje eksperimenata za SA i ABC,
7. generisanje konačnog PDF rasporeda.

## Pojedinačne komande

Validacija podataka:

```bash
python src/main.py validate
```

Generisanje nastavnih događaja:

```bash
python src/main.py generate-events
```

Generisanje početnog rasporeda:

```bash
python src/main.py initial-schedule
```

Provjera hard constraint ograničenja:

```bash
python src/main.py check-schedule
```

Računanje fitnessa početnog rasporeda:

```bash
python src/main.py fitness
```

Pokretanje samo Simulated Annealing algoritma:

```bash
python src/main.py sa
```

Pokretanje samo Artificial Bee Colony algoritma:

```bash
python src/main.py abc
```

Pokretanje eksperimenata za oba algoritma:

```bash
python src/main.py experiments
```

Generisanje PDF rasporeda:

```bash
python src/main.py export-pdf
```

## Izlazni fajlovi

Pokretanjem projekta automatski se generišu folderi:

```text
data/processed/
output/
```

Najvažniji izlazni fajlovi su:

| Fajl                                         | Opis                                       |
| -------------------------------------------- | ------------------------------------------ |
| `data/processed/dogadjaji.csv`               | Generisani nastavni događaji               |
| `data/processed/inicijalni_raspored.csv`     | Početni greedy raspored                    |
| `data/processed/nerasporedjeni.csv`          | Događaji koji nisu raspoređeni, ako ih ima |
| `data/processed/fitness_izvjestaj.txt`       | Fitness izvještaj početnog rasporeda       |
| `data/processed/eksperimenti_rezultati.csv`  | Rezultati svih pokretanja SA i ABC         |
| `data/processed/eksperimenti_statistika.csv` | Deskriptivna statistika algoritama         |
| `data/processed/eksperimenti_izvjestaj.txt`  | Tekstualni izvještaj eksperimenata         |
| `output/grafici/`                            | Generisani grafici                         |
| `output/rasporedi/svi_rasporedi.pdf`         | Konačni PDF raspored                       |

Folderi `data/processed/` i `output/` nisu dio izvornog koda. Oni se generišu automatski i ne trebaju se commitati na GitHub.

## Hard constraint ograničenja

Raspored se smatra validnim samo ako zadovoljava hard constraint pravila:

* nastavnik ne može držati dva časa u isto vrijeme,
* učionica ne može imati dva događaja u isto vrijeme,
* studenti istog smjera, ciklusa, godine i semestra ne mogu imati dva časa u isto vrijeme,
* učionica mora imati dovoljan kapacitet,
* laboratorijske vježbe moraju biti u odgovarajućoj učionici,
* redovno zaposleni nemaju nastavu četvrtkom od 13:00 do 14:00,
* nastava mora završiti najkasnije u 19:00.

Provjera validnosti rasporeda pokreće se komandom:

```bash
python src/main.py check-schedule
```

Ispravan raspored treba imati:

```text
Broj hard constraint gresaka: 0
```

## Fitness funkcija

Fitness funkcija računa koliko je raspored loš. Manja vrijednost fitnessa znači bolji raspored.

Fitness uključuje velike kazne za hard constraint greške i manje kazne za soft constraint probleme, kao što su:

* rupe u rasporedu studenata,
* rupe u rasporedu nastavnika,
* previše uzastopnih časova,
* neravnomjerna raspodjela nastave po danima,
* master nastava u preranim terminima,
* vježbe prije predavanja,
* nepoštovanje individualnih želja nastavnika i saradnika.

## Simulirano kaljenje

Simulirano kaljenje kreće od početnog rasporeda i u svakoj iteraciji pokušava napraviti malu promjenu. Ako je promjena bolja, prihvata se. Ako je lošija, može se prihvatiti sa određenom vjerovatnoćom, posebno na početku kada je temperatura veća.

U ovom projektu SA koristi:

```text
600 iteracija
početna temperatura 500.0
hlađenje 0.99
```

## Artificial Bee Colony

Artificial Bee Colony koristi populaciju kandidatskih rasporeda, gdje svaki raspored predstavlja jedan izvor hrane. Algoritam pokušava poboljšavati izvore, bira bolje izvore sa većom vjerovatnoćom i zamjenjuje one koji se dugo ne popravljaju.

U ovom projektu ABC koristi:

```text
70 ciklusa
4 izvora hrane
limit 15
```

## Eksperimenti

Eksperimenti se pokreću komandom:

```bash
python src/main.py experiments
```

U eksperimentima se svaki algoritam pokreće 30 nezavisnih puta. Za svako pokretanje bilježe se:

* najbolji fitness,
* vrijeme izvršavanja,
* broj hard constraint grešaka,
* parametri algoritma.

Nakon toga se generišu statistika i grafici za poređenje SA i ABC algoritma.

## PDF raspored

Konačni PDF raspored generiše se komandom:

```bash
python src/main.py export-pdf
```

PDF se nalazi na putanji:

```text
output/rasporedi/svi_rasporedi.pdf
```

Svi rasporedi nalaze se u jednom PDF fajlu. Svaka stranica predstavlja jedan smjer, ciklus, godinu i semestar. Grupe G1 i G2 prikazane su u istom rasporedu.
