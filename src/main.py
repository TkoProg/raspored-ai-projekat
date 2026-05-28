from pathlib import Path
import sys

from parametri import BROJ_POKRETANJA_EKSPERIMENTA
from parametri import SA_BROJ_ITERACIJA
from parametri import SA_POCETNA_TEMPERATURA
from parametri import SA_HLADJENJE
from parametri import ABC_BROJ_CIKLUSA
from parametri import ABC_BROJ_IZVORA
from parametri import ABC_LIMIT

from parser import ucitaj_predmete
from parser import ucitaj_osoblje
from parser import ucitaj_ucionice
from parser import ucitaj_studente
from parser import ucitaj_termine
from parser import ucitaj_ogranicenja
from parser import ucitaj_dogadjaje
from parser import ucitaj_raspored
from validacija import ispisi_validaciju
from generator_dogadjaja import generisi_dogadjaje
from generator_dogadjaja import sacuvaj_dogadjaje
from inicijalni_raspored import napravi_inicijalni_raspored
from inicijalni_raspored import sacuvaj_raspored
from inicijalni_raspored import sacuvaj_nerasporedjene
from hard_constraints import provjeri_raspored
from fitness import izracunaj_fitness
from fitness import sacuvaj_fitness_izvjestaj
from simulirano_kaljenje import simulirano_kaljenje
from artificial_bee_colony import artificial_bee_colony
from eksperimenti import pokreni_eksperimente
from eksperimenti import sacuvaj_konvergenciju
from pdf_export import izaberi_najbolji_raspored
from pdf_export import exportuj_pdf_rasporede


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = ROOT / "output"


def sacuvaj_izvjestaj_algoritma(putanja, naziv, pocetni_fitness, najbolji_fitness, parametri, hard_greske):
    putanja = Path(putanja)
    putanja.parent.mkdir(parents=True, exist_ok=True)

    linije = []
    linije.append("=== " + naziv + " ===")
    linije.append("Pocetni fitness: " + str(pocetni_fitness))
    linije.append("Najbolji fitness: " + str(najbolji_fitness))
    linije.append("Poboljsanje: " + str(pocetni_fitness - najbolji_fitness))

    for naziv_parametra, vrijednost in parametri:
        linije.append(naziv_parametra + ": " + str(vrijednost))

    linije.append("Broj hard constraint gresaka u najboljem rasporedu: " + str(len(hard_greske)))

    tekst = "\n".join(linije)
    with open(putanja, "w", encoding="utf-8") as f:
        f.write(tekst)

    return tekst


def ucitaj_sve():
    predmeti = ucitaj_predmete(DATA_DIR)
    osoblje = ucitaj_osoblje(DATA_DIR)
    ucionice = ucitaj_ucionice(DATA_DIR)
    studenti = ucitaj_studente(DATA_DIR)
    termini = ucitaj_termine(DATA_DIR)
    ogranicenja = ucitaj_ogranicenja(DATA_DIR)
    return predmeti, osoblje, ucionice, studenti, termini, ogranicenja


def osiguraj_dogadjaje(regenerisi=False):
    predmeti, osoblje, ucionice, studenti, termini, ogranicenja = ucitaj_sve()
    dogadjaji_putanja = PROCESSED_DIR / "dogadjaji.csv"

    # Ako je projekat ranije pokretan, u data/processed mogu ostati stari dogadjaji.
    # Zato komande koje prave novi raspored mogu traziti regenerisanje.
    if regenerisi or not dogadjaji_putanja.exists():
        dogadjaji = generisi_dogadjaje(predmeti, osoblje, studenti, ucionice)
        sacuvaj_dogadjaje(dogadjaji, dogadjaji_putanja)
    else:
        dogadjaji = ucitaj_dogadjaje(dogadjaji_putanja)

    return dogadjaji


def osiguraj_inicijalni_raspored(regenerisi=False):
    predmeti, osoblje, ucionice, studenti, termini, ogranicenja = ucitaj_sve()
    dogadjaji = osiguraj_dogadjaje(regenerisi=regenerisi)
    raspored_putanja = PROCESSED_DIR / "inicijalni_raspored.csv"

    # Isto pravilo kao za dogadjaje: kada se pravi novi raspored, ne smijemo
    # naslijediti stari inicijalni_raspored.csv iz prethodne verzije projekta.
    if regenerisi or not raspored_putanja.exists():
        raspored, nerasporedjeni = napravi_inicijalni_raspored(dogadjaji, termini, ucionice, osoblje)
        sacuvaj_raspored(raspored, raspored_putanja)
        sacuvaj_nerasporedjene(nerasporedjeni, PROCESSED_DIR / "nerasporedjeni.csv")
    else:
        raspored = ucitaj_raspored(raspored_putanja)

    return raspored


def komanda_validate():
    predmeti, osoblje, ucionice, studenti, termini, ogranicenja = ucitaj_sve()
    ispisi_validaciju(predmeti, osoblje, ucionice, studenti, termini, ogranicenja)


def komanda_generate_events():
    predmeti, osoblje, ucionice, studenti, termini, ogranicenja = ucitaj_sve()
    dogadjaji = generisi_dogadjaje(predmeti, osoblje, studenti, ucionice)

    putanja = PROCESSED_DIR / "dogadjaji.csv"
    sacuvaj_dogadjaje(dogadjaji, putanja)

    print("Generisani nastavni dogadjaji:", len(dogadjaji))
    print("Sacuvano u:", putanja)


def komanda_initial_schedule():
    predmeti, osoblje, ucionice, studenti, termini, ogranicenja = ucitaj_sve()
    dogadjaji = osiguraj_dogadjaje(regenerisi=True)
    raspored, nerasporedjeni = napravi_inicijalni_raspored(dogadjaji, termini, ucionice, osoblje)

    sacuvaj_raspored(raspored, PROCESSED_DIR / "inicijalni_raspored.csv")
    sacuvaj_nerasporedjene(nerasporedjeni, PROCESSED_DIR / "nerasporedjeni.csv")

    print("Ukupno dogadjaja:", len(dogadjaji))
    print("Rasporedjeno:", len(raspored))
    print("Nerasporedjeno:", len(nerasporedjeni))
    print("Sacuvano u:", PROCESSED_DIR / "inicijalni_raspored.csv")

    if len(nerasporedjeni) > 0:
        print("Nerasporedjeni dogadjaji su u:", PROCESSED_DIR / "nerasporedjeni.csv")


def komanda_check_schedule():
    predmeti, osoblje, ucionice, studenti, termini, ogranicenja = ucitaj_sve()
    raspored = osiguraj_inicijalni_raspored()
    greske = provjeri_raspored(raspored, ucionice, osoblje)

    print("=== PROVJERA RASPOREDA ===")
    print("Broj stavki rasporeda:", len(raspored))
    print("Broj hard constraint gresaka:", len(greske))

    for greska in greske[:100]:
        print("-", greska)

    if len(greske) > 100:
        print("Prikazano je prvih 100 gresaka.")


def komanda_fitness():
    predmeti, osoblje, ucionice, studenti, termini, ogranicenja = ucitaj_sve()
    dogadjaji = osiguraj_dogadjaje()
    raspored = osiguraj_inicijalni_raspored()

    ukupno, detalji, hard_greske = izracunaj_fitness(raspored, dogadjaji, ucionice, osoblje)
    tekst = sacuvaj_fitness_izvjestaj(PROCESSED_DIR / "fitness_izvjestaj.txt", ukupno, detalji, hard_greske)

    print(tekst)
    print("")
    print("Sacuvano u:", PROCESSED_DIR / "fitness_izvjestaj.txt")


def komanda_simulated_annealing():
    predmeti, osoblje, ucionice, studenti, termini, ogranicenja = ucitaj_sve()
    dogadjaji = osiguraj_dogadjaje()
    pocetni_raspored = osiguraj_inicijalni_raspored()

    pocetni_fitness, _, _ = izracunaj_fitness(pocetni_raspored, dogadjaji, ucionice, osoblje)

    broj_iteracija = SA_BROJ_ITERACIJA
    najbolji_raspored, najbolji_fitness, historija = simulirano_kaljenje(
        pocetni_raspored,
        dogadjaji,
        termini,
        ucionice,
        osoblje,
        broj_iteracija=broj_iteracija,
        pocetna_temperatura=SA_POCETNA_TEMPERATURA,
        hladjenje=SA_HLADJENJE,
        seed=42
    )

    ukupno, detalji, hard_greske = izracunaj_fitness(najbolji_raspored, dogadjaji, ucionice, osoblje)

    sacuvaj_raspored(najbolji_raspored, PROCESSED_DIR / "sa_raspored.csv")
    sacuvaj_konvergenciju(historija, PROCESSED_DIR / "sa_konvergencija.csv", "SA")
    tekst = sacuvaj_izvjestaj_algoritma(
        PROCESSED_DIR / "sa_izvjestaj.txt",
        "SIMULIRANO KALJENJE",
        pocetni_fitness,
        najbolji_fitness,
        [("Broj iteracija", broj_iteracija)],
        hard_greske
    )
    sacuvaj_fitness_izvjestaj(PROCESSED_DIR / "sa_fitness_izvjestaj.txt", ukupno, detalji, hard_greske)

    print(tekst)
    print("")
    print("Sacuvano u:", PROCESSED_DIR / "sa_raspored.csv")
    print("Konvergencija:", PROCESSED_DIR / "sa_konvergencija.csv")


def komanda_abc():
    predmeti, osoblje, ucionice, studenti, termini, ogranicenja = ucitaj_sve()
    dogadjaji = osiguraj_dogadjaje()
    pocetni_raspored = osiguraj_inicijalni_raspored()

    pocetni_fitness, _, _ = izracunaj_fitness(pocetni_raspored, dogadjaji, ucionice, osoblje)

    broj_ciklusa = ABC_BROJ_CIKLUSA
    broj_izvora = ABC_BROJ_IZVORA
    limit = ABC_LIMIT

    najbolji_raspored, najbolji_fitness, historija = artificial_bee_colony(
        pocetni_raspored,
        dogadjaji,
        termini,
        ucionice,
        osoblje,
        broj_ciklusa=broj_ciklusa,
        broj_izvora=broj_izvora,
        limit=limit,
        seed=43
    )

    ukupno, detalji, hard_greske = izracunaj_fitness(najbolji_raspored, dogadjaji, ucionice, osoblje)

    sacuvaj_raspored(najbolji_raspored, PROCESSED_DIR / "abc_raspored.csv")
    sacuvaj_konvergenciju(historija, PROCESSED_DIR / "abc_konvergencija.csv", "ABC")
    tekst = sacuvaj_izvjestaj_algoritma(
        PROCESSED_DIR / "abc_izvjestaj.txt",
        "ARTIFICIAL BEE COLONY",
        pocetni_fitness,
        najbolji_fitness,
        [("Broj ciklusa", broj_ciklusa), ("Broj izvora hrane", broj_izvora), ("Limit", limit)],
        hard_greske
    )
    sacuvaj_fitness_izvjestaj(PROCESSED_DIR / "abc_fitness_izvjestaj.txt", ukupno, detalji, hard_greske)

    print(tekst)
    print("")
    print("Sacuvano u:", PROCESSED_DIR / "abc_raspored.csv")
    print("Konvergencija:", PROCESSED_DIR / "abc_konvergencija.csv")


def komanda_experiments(
    broj_pokretanja=BROJ_POKRETANJA_EKSPERIMENTA,
    sa_iteracija=SA_BROJ_ITERACIJA,
    abc_ciklusa=ABC_BROJ_CIKLUSA,
    abc_izvora=ABC_BROJ_IZVORA,
    abc_limit=ABC_LIMIT
):
    predmeti, osoblje, ucionice, studenti, termini, ogranicenja = ucitaj_sve()
    dogadjaji = osiguraj_dogadjaje(regenerisi=True)
    pocetni_raspored = osiguraj_inicijalni_raspored(regenerisi=True)

    tekst = pokreni_eksperimente(
        pocetni_raspored,
        dogadjaji,
        termini,
        ucionice,
        osoblje,
        PROCESSED_DIR,
        OUTPUT_DIR,
        broj_pokretanja=broj_pokretanja,
        sa_iteracija=sa_iteracija,
        abc_ciklusa=abc_ciklusa,
        abc_izvora=abc_izvora,
        abc_limit=abc_limit
    )

    print(tekst)


def komanda_export_pdf():
    predmeti, osoblje, ucionice, studenti, termini, ogranicenja = ucitaj_sve()
    dogadjaji = osiguraj_dogadjaje()
    osiguraj_inicijalni_raspored()

    naziv, raspored, fitness = izaberi_najbolji_raspored(PROCESSED_DIR, dogadjaji, ucionice, osoblje)

    if raspored is None:
        print("Nema rasporeda za PDF export.")
        return

    redovi, pdf_putanja = exportuj_pdf_rasporede(raspored, OUTPUT_DIR / "rasporedi")

    print("Koristen raspored:", naziv)
    print("Fitness:", fitness)
    print("Broj rasporeda u PDF-u:", len(redovi))
    print("PDF:", pdf_putanja)


def komanda_all():
    print("1/7 Validacija")
    komanda_validate()
    print("\n2/7 Generisanje dogadjaja")
    komanda_generate_events()
    print("\n3/7 Inicijalni raspored")
    komanda_initial_schedule()
    print("\n4/7 Provjera hard constraints")
    komanda_check_schedule()
    print("\n5/7 Fitness")
    komanda_fitness()
    print("\n6/7 Eksperimenti")
    komanda_experiments()
    print("\n7/7 PDF rasporedi")
    komanda_export_pdf()

def prikazi_pomoc():
    print("Koristenje:")
    print("python src/main.py validate")
    print("python src/main.py generate-events")
    print("python src/main.py initial-schedule")
    print("python src/main.py check-schedule")
    print("python src/main.py fitness")
    print("python src/main.py sa")
    print("python src/main.py abc")
    print("python src/main.py experiments")
    print("python src/main.py experiments 30   # 30 pokretanja po algoritmu")
    print("python src/main.py experiments 30 600 60 4 10   # pokretanja, SA iteracije, ABC ciklusi, ABC izvori, ABC limit")
    print("python src/main.py export-pdf")
    print("python src/main.py all")


def main():
    if len(sys.argv) < 2:
        prikazi_pomoc()
        return

    komanda = sys.argv[1]

    if komanda == "validate":
        komanda_validate()
    elif komanda == "generate-events":
        komanda_generate_events()
    elif komanda == "initial-schedule":
        komanda_initial_schedule()
    elif komanda == "check-schedule":
        komanda_check_schedule()
    elif komanda == "fitness":
        komanda_fitness()
    elif komanda == "simulated-annealing" or komanda == "sa":
        komanda_simulated_annealing()
    elif komanda == "artificial-bee-colony" or komanda == "abc":
        komanda_abc()
    elif komanda == "experiments":
        broj = BROJ_POKRETANJA_EKSPERIMENTA
        sa_iteracija = SA_BROJ_ITERACIJA
        abc_ciklusa = ABC_BROJ_CIKLUSA
        abc_izvora = ABC_BROJ_IZVORA
        abc_limit = ABC_LIMIT

        if len(sys.argv) >= 3:
            broj = int(sys.argv[2])
        if len(sys.argv) >= 4:
            sa_iteracija = int(sys.argv[3])
        if len(sys.argv) >= 5:
            abc_ciklusa = int(sys.argv[4])
        if len(sys.argv) >= 6:
            abc_izvora = int(sys.argv[5])
        if len(sys.argv) >= 7:
            abc_limit = int(sys.argv[6])

        komanda_experiments(broj, sa_iteracija, abc_ciklusa, abc_izvora, abc_limit)
    elif komanda == "export-pdf":
        komanda_export_pdf()
    elif komanda == "all":
        komanda_all()
    else:
        print("Nepoznata komanda:", komanda)
        prikazi_pomoc()


if __name__ == "__main__":
    main()
