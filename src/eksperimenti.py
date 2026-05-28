import csv
import random
import statistics
import time
from pathlib import Path

from parametri import BROJ_POKRETANJA_EKSPERIMENTA
from parametri import SA_BROJ_ITERACIJA
from parametri import SA_POCETNA_TEMPERATURA
from parametri import SA_HLADJENJE
from parametri import ABC_BROJ_CIKLUSA
from parametri import ABC_BROJ_IZVORA
from parametri import ABC_LIMIT

from artificial_bee_colony import artificial_bee_colony
from fitness import izracunaj_fitness
from hard_constraints import provjeri_raspored
from simulirano_kaljenje import simulirano_kaljenje
from inicijalni_raspored import sacuvaj_raspored


def srednja_vrijednost(vrijednosti):
    if len(vrijednosti) == 0:
        return 0
    return sum(vrijednosti) / len(vrijednosti)


def standardna_devijacija(vrijednosti):
    if len(vrijednosti) <= 1:
        return 0
    return statistics.stdev(vrijednosti)


def medijan(vrijednosti):
    if len(vrijednosti) == 0:
        return 0
    return statistics.median(vrijednosti)


def napravi_statistiku(naziv_algoritma, vrijednosti):
    if len(vrijednosti) == 0:
        return {
            "algoritam": naziv_algoritma,
            "broj_pokretanja": 0,
            "najbolji": 0,
            "najgori": 0,
            "prosjek": 0,
            "medijan": 0,
            "std": 0
        }

    return {
        "algoritam": naziv_algoritma,
        "broj_pokretanja": len(vrijednosti),
        "najbolji": min(vrijednosti),
        "najgori": max(vrijednosti),
        "prosjek": round(srednja_vrijednost(vrijednosti), 2),
        "medijan": round(medijan(vrijednosti), 2),
        "std": round(standardna_devijacija(vrijednosti), 2)
    }


def permutacijski_test(vrijednosti_a, vrijednosti_b, broj_permutacija=1000, seed=123):
    # Jednostavan statisticki test bez scipy biblioteke.
    # H0: algoritmi imaju slican prosjecan fitness.
    # Manja p-vrijednost znaci da je razlika vjerovatno stvarna.
    random.seed(seed)

    stvarna_razlika = abs(srednja_vrijednost(vrijednosti_a) - srednja_vrijednost(vrijednosti_b))
    spojeno = list(vrijednosti_a) + list(vrijednosti_b)
    n_a = len(vrijednosti_a)
    broj_vecih = 0

    for i in range(broj_permutacija):
        random.shuffle(spojeno)
        nova_a = spojeno[:n_a]
        nova_b = spojeno[n_a:]
        razlika = abs(srednja_vrijednost(nova_a) - srednja_vrijednost(nova_b))

        if razlika >= stvarna_razlika:
            broj_vecih += 1

    p = (broj_vecih + 1) / (broj_permutacija + 1)
    return round(p, 4)


def sacuvaj_rezultate(redovi, putanja):
    putanja = Path(putanja)
    putanja.parent.mkdir(parents=True, exist_ok=True)

    kolone = [
        "algoritam",
        "run_id",
        "seed",
        "najbolji_fitness",
        "vrijeme_sekundi",
        "broj_hard_gresaka",
        "broj_iteracija_ili_ciklusa",
        "broj_izvora",
        "limit"
    ]

    with open(putanja, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=kolone)
        writer.writeheader()
        for red in redovi:
            writer.writerow(red)


def sacuvaj_statistiku(statistike, putanja):
    putanja = Path(putanja)
    putanja.parent.mkdir(parents=True, exist_ok=True)

    kolone = [
        "algoritam",
        "broj_pokretanja",
        "najbolji",
        "najgori",
        "prosjek",
        "medijan",
        "std"
    ]

    with open(putanja, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=kolone)
        writer.writeheader()
        for red in statistike:
            writer.writerow(red)


def sacuvaj_konvergenciju(historija, putanja, tip_algoritma):
    putanja = Path(putanja)
    putanja.parent.mkdir(parents=True, exist_ok=True)

    if tip_algoritma == "SA":
        kolone = ["iteracija", "najbolji_fitness", "trenutni_fitness", "temperatura"]
        with open(putanja, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(kolone)
            for red in historija:
                writer.writerow([
                    red["iteracija"],
                    red["najbolji_fitness"],
                    red["trenutni_fitness"],
                    red["temperatura"]
                ])
    else:
        kolone = ["ciklus", "najbolji_fitness", "prosjek_fitness"]
        with open(putanja, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(kolone)
            for red in historija:
                writer.writerow([
                    red["ciklus"],
                    red["najbolji_fitness"],
                    red["prosjek_fitness"]
                ])


def napravi_grafove(rezultati, statistike, najbolja_sa_historija, najbolja_abc_historija, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib.pyplot as plt
    except Exception:
        return ["Matplotlib nije instaliran, grafici nisu napravljeni."]

    poruke = []

    sa_vrijednosti = []
    abc_vrijednosti = []
    for red in rezultati:
        if red["algoritam"] == "SA":
            sa_vrijednosti.append(red["najbolji_fitness"])
        elif red["algoritam"] == "ABC":
            abc_vrijednosti.append(red["najbolji_fitness"])

    # 1. Boxplot fitnessa
    plt.figure(figsize=(7, 5))
    plt.boxplot([sa_vrijednosti, abc_vrijednosti], labels=["SA", "ABC"])
    plt.title("Poredjenje fitness vrijednosti")
    plt.ylabel("Fitness - manje je bolje")
    plt.tight_layout()
    putanja = output_dir / "boxplot_fitness.png"
    plt.savefig(putanja, dpi=150)
    plt.close()
    poruke.append(str(putanja))

    # 2. Prosjek i najbolji fitness
    oznake = []
    prosjeci = []
    najbolji = []
    for s in statistike:
        oznake.append(s["algoritam"])
        prosjeci.append(float(s["prosjek"]))
        najbolji.append(float(s["najbolji"]))

    plt.figure(figsize=(7, 5))
    x = list(range(len(oznake)))
    sirina = 0.35
    plt.bar([i - sirina / 2 for i in x], prosjeci, width=sirina, label="Prosjek")
    plt.bar([i + sirina / 2 for i in x], najbolji, width=sirina, label="Najbolji")
    plt.xticks(x, oznake)
    plt.title("Prosjecni i najbolji fitness")
    plt.ylabel("Fitness - manje je bolje")
    plt.legend()
    plt.tight_layout()
    putanja = output_dir / "prosjek_i_najbolji.png"
    plt.savefig(putanja, dpi=150)
    plt.close()
    poruke.append(str(putanja))

    # 3. Konvergencija najboljeg SA runa
    if najbolja_sa_historija:
        x = []
        y = []
        for red in najbolja_sa_historija:
            x.append(red["iteracija"])
            y.append(red["najbolji_fitness"])

        plt.figure(figsize=(7, 5))
        plt.plot(x, y, marker="o")
        plt.title("Konvergencija - Simulirano kaljenje")
        plt.xlabel("Iteracija")
        plt.ylabel("Najbolji fitness")
        plt.tight_layout()
        putanja = output_dir / "konvergencija_sa.png"
        plt.savefig(putanja, dpi=150)
        plt.close()
        poruke.append(str(putanja))

    # 4. Konvergencija najboljeg ABC runa
    if najbolja_abc_historija:
        x = []
        y = []
        for red in najbolja_abc_historija:
            x.append(red["ciklus"])
            y.append(red["najbolji_fitness"])

        plt.figure(figsize=(7, 5))
        plt.plot(x, y, marker="o")
        plt.title("Konvergencija - Artificial Bee Colony")
        plt.xlabel("Ciklus")
        plt.ylabel("Najbolji fitness")
        plt.tight_layout()
        putanja = output_dir / "konvergencija_abc.png"
        plt.savefig(putanja, dpi=150)
        plt.close()
        poruke.append(str(putanja))

    return poruke


def napravi_tekst_izvjestaja(
    stat_sa,
    stat_abc,
    p_vrijednost,
    rezultati_putanja,
    statistika_putanja,
    grafici,
    broj_pokretanja,
    sa_iteracija,
    abc_ciklusa,
    abc_izvora,
    abc_limit
):
    bolji_po_prosjeku = "SA"
    if float(stat_abc["prosjek"]) < float(stat_sa["prosjek"]):
        bolji_po_prosjeku = "ABC"

    bolji_najbolji = "SA"
    if float(stat_abc["najbolji"]) < float(stat_sa["najbolji"]):
        bolji_najbolji = "ABC"

    linije = []
    linije.append("=== EKSPERIMENTI ===")
    linije.append(
        "Pokrenuto je " + str(broj_pokretanja) +
        " nezavisnih pokretanja za SA i " + str(broj_pokretanja) +
        " za ABC."
    )
    linije.append(
        "Parametri su isti kao kod pojedinacnih algoritama: " +
        str(sa_iteracija) + " SA iteracija po pokretanju, " +
        str(abc_ciklusa) + " ABC ciklusa, " +
        str(abc_izvora) + " ABC izvora i limit " +
        str(abc_limit) + "."
    )
    linije.append("")
    linije.append("Rezultati su sacuvani u: " + str(rezultati_putanja))
    linije.append("Statistika je sacuvana u: " + str(statistika_putanja))
    linije.append("")
    linije.append("SA statistika:")
    linije.append("- najbolji: " + str(stat_sa["najbolji"]))
    linije.append("- najgori: " + str(stat_sa["najgori"]))
    linije.append("- prosjek: " + str(stat_sa["prosjek"]))
    linije.append("- medijan: " + str(stat_sa["medijan"]))
    linije.append("- std: " + str(stat_sa["std"]))
    linije.append("")
    linije.append("ABC statistika:")
    linije.append("- najbolji: " + str(stat_abc["najbolji"]))
    linije.append("- najgori: " + str(stat_abc["najgori"]))
    linije.append("- prosjek: " + str(stat_abc["prosjek"]))
    linije.append("- medijan: " + str(stat_abc["medijan"]))
    linije.append("- std: " + str(stat_abc["std"]))
    linije.append("")
    linije.append("Bolji po prosjeku: " + bolji_po_prosjeku)
    linije.append("Bolji najbolji rezultat: " + bolji_najbolji)
    linije.append("Permutacijski test p-vrijednost: " + str(p_vrijednost))
    linije.append("")
    linije.append("Tumacenje p-vrijednosti:")
    if p_vrijednost < 0.05:
        linije.append("Razlika izmedju algoritama je statisticki uocljiva za prag 0.05.")
    else:
        linije.append("Razlika nije dovoljno jaka za prag 0.05, ali se algoritmi i dalje mogu porediti po prosjeku i minimumu.")

    if len(grafici) > 0:
        linije.append("")
        linije.append("Grafici:")
        for g in grafici:
            linije.append("- " + g)

    return "\n".join(linije)


def pokreni_eksperimente(
    pocetni_raspored,
    dogadjaji,
    termini,
    ucionice,
    osoblje,
    processed_dir,
    output_dir,
    broj_pokretanja=BROJ_POKRETANJA_EKSPERIMENTA,
    sa_iteracija=SA_BROJ_ITERACIJA,
    abc_ciklusa=ABC_BROJ_CIKLUSA,
    abc_izvora=ABC_BROJ_IZVORA,
    abc_limit=ABC_LIMIT
):
    processed_dir = Path(processed_dir)
    output_dir = Path(output_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    rezultati = []
    sa_vrijednosti = []
    abc_vrijednosti = []

    najbolji_sa_fitness = None
    najbolji_sa_raspored = None
    najbolja_sa_historija = None

    najbolji_abc_fitness = None
    najbolji_abc_raspored = None
    najbolja_abc_historija = None

    for run_id in range(1, broj_pokretanja + 1):
        seed = 1000 + run_id
        start = time.time()
        raspored, fitness, historija = simulirano_kaljenje(
            pocetni_raspored,
            dogadjaji,
            termini,
            ucionice,
            osoblje,
            broj_iteracija=sa_iteracija,
            pocetna_temperatura=SA_POCETNA_TEMPERATURA,
            hladjenje=SA_HLADJENJE,
            seed=seed
        )
        kraj = time.time()
        hard_greske = provjeri_raspored(raspored, ucionice, osoblje)
        sa_vrijednosti.append(fitness)
        rezultati.append({
            "algoritam": "SA",
            "run_id": run_id,
            "seed": seed,
            "najbolji_fitness": fitness,
            "vrijeme_sekundi": round(kraj - start, 3),
            "broj_hard_gresaka": len(hard_greske),
            "broj_iteracija_ili_ciklusa": sa_iteracija,
            "broj_izvora": "",
            "limit": ""
        })

        if najbolji_sa_fitness is None or fitness < najbolji_sa_fitness:
            najbolji_sa_fitness = fitness
            najbolji_sa_raspored = raspored
            najbolja_sa_historija = historija

    for run_id in range(1, broj_pokretanja + 1):
        seed = 2000 + run_id
        start = time.time()
        raspored, fitness, historija = artificial_bee_colony(
            pocetni_raspored,
            dogadjaji,
            termini,
            ucionice,
            osoblje,
            broj_ciklusa=abc_ciklusa,
            broj_izvora=abc_izvora,
            limit=abc_limit,
            seed=seed
        )
        kraj = time.time()
        hard_greske = provjeri_raspored(raspored, ucionice, osoblje)
        abc_vrijednosti.append(fitness)
        rezultati.append({
            "algoritam": "ABC",
            "run_id": run_id,
            "seed": seed,
            "najbolji_fitness": fitness,
            "vrijeme_sekundi": round(kraj - start, 3),
            "broj_hard_gresaka": len(hard_greske),
            "broj_iteracija_ili_ciklusa": abc_ciklusa,
            "broj_izvora": abc_izvora,
            "limit": abc_limit
        })

        if najbolji_abc_fitness is None or fitness < najbolji_abc_fitness:
            najbolji_abc_fitness = fitness
            najbolji_abc_raspored = raspored
            najbolja_abc_historija = historija

    stat_sa = napravi_statistiku("SA", sa_vrijednosti)
    stat_abc = napravi_statistiku("ABC", abc_vrijednosti)
    statistike = [stat_sa, stat_abc]

    p_vrijednost = permutacijski_test(sa_vrijednosti, abc_vrijednosti, broj_permutacija=1000)

    rezultati_putanja = processed_dir / "eksperimenti_rezultati.csv"
    statistika_putanja = processed_dir / "eksperimenti_statistika.csv"
    izvjestaj_putanja = processed_dir / "eksperimenti_izvjestaj.txt"

    sacuvaj_rezultate(rezultati, rezultati_putanja)
    sacuvaj_statistiku(statistike, statistika_putanja)

    if najbolji_sa_raspored is not None:
        sacuvaj_raspored(najbolji_sa_raspored, processed_dir / "eksperimenti_najbolji_sa_raspored.csv")
        sacuvaj_konvergenciju(najbolja_sa_historija, processed_dir / "eksperimenti_najbolja_sa_konvergencija.csv", "SA")

    if najbolji_abc_raspored is not None:
        sacuvaj_raspored(najbolji_abc_raspored, processed_dir / "eksperimenti_najbolji_abc_raspored.csv")
        sacuvaj_konvergenciju(najbolja_abc_historija, processed_dir / "eksperimenti_najbolja_abc_konvergencija.csv", "ABC")

    grafici = napravi_grafove(rezultati, statistike, najbolja_sa_historija, najbolja_abc_historija, output_dir / "grafici")
    tekst = napravi_tekst_izvjestaja(
        stat_sa,
        stat_abc,
        p_vrijednost,
        rezultati_putanja,
        statistika_putanja,
        grafici,
        broj_pokretanja,
        sa_iteracija,
        abc_ciklusa,
        abc_izvora,
        abc_limit
    )

    with open(izvjestaj_putanja, "w", encoding="utf-8") as f:
        f.write(tekst)

    return tekst
