import random

from parametri import ABC_BROJ_CIKLUSA
from parametri import ABC_BROJ_IZVORA
from parametri import ABC_LIMIT

from fitness import izracunaj_fitness
from simulirano_kaljenje import kopiraj_raspored
from simulirano_kaljenje import napravi_susjeda


def napravi_pocetni_izvor(pocetni_raspored, dogadjaji, termini, ucionice, osoblje, broj_poteza):
    raspored = kopiraj_raspored(pocetni_raspored)

    for i in range(broj_poteza):
        susjed = napravi_susjeda(raspored, termini, ucionice, osoblje)
        if susjed is not None:
            raspored = susjed

    fitness, _, _ = izracunaj_fitness(raspored, dogadjaji, ucionice, osoblje)

    return {
        "raspored": raspored,
        "fitness": fitness,
        "pokusaji_bez_popravke": 0
    }


def napravi_populaciju(pocetni_raspored, dogadjaji, termini, ucionice, osoblje, broj_izvora):
    populacija = []

    for i in range(broj_izvora):
        izvor = napravi_pocetni_izvor(
            pocetni_raspored,
            dogadjaji,
            termini,
            ucionice,
            osoblje,
            broj_poteza=i + 1
        )
        populacija.append(izvor)

    return populacija


def popravi_izvor(izvor, dogadjaji, termini, ucionice, osoblje):
    kandidat = napravi_susjeda(izvor["raspored"], termini, ucionice, osoblje)

    if kandidat is None:
        izvor["pokusaji_bez_popravke"] += 1
        return izvor

    kandidat_fitness, _, _ = izracunaj_fitness(kandidat, dogadjaji, ucionice, osoblje)

    if kandidat_fitness < izvor["fitness"]:
        return {
            "raspored": kandidat,
            "fitness": kandidat_fitness,
            "pokusaji_bez_popravke": 0
        }

    izvor["pokusaji_bez_popravke"] += 1
    return izvor


def nadji_najbolji(populacija):
    najbolji = populacija[0]

    for izvor in populacija:
        if izvor["fitness"] < najbolji["fitness"]:
            najbolji = izvor

    return {
        "raspored": kopiraj_raspored(najbolji["raspored"]),
        "fitness": najbolji["fitness"],
        "pokusaji_bez_popravke": najbolji["pokusaji_bez_popravke"]
    }


def izaberi_izvor(populacija):
    # Manji fitness je bolji, pa bolji rasporedi dobijaju vecu sansu.
    tezine = []
    suma = 0.0

    for izvor in populacija:
        tezina = 1.0 / (1.0 + izvor["fitness"])
        tezine.append(tezina)
        suma += tezina

    if suma == 0:
        return random.randrange(len(populacija))

    vrijednost = random.random() * suma
    trenutno = 0.0

    for i in range(len(populacija)):
        trenutno += tezine[i]
        if trenutno >= vrijednost:
            return i

    return len(populacija) - 1


def zamijeni_lose_izvore(populacija, pocetni_raspored, dogadjaji, termini, ucionice, osoblje, limit):
    for i in range(len(populacija)):
        if populacija[i]["pokusaji_bez_popravke"] >= limit:
            populacija[i] = napravi_pocetni_izvor(
                pocetni_raspored,
                dogadjaji,
                termini,
                ucionice,
                osoblje,
                broj_poteza=random.randint(1, 10)
            )


def artificial_bee_colony(pocetni_raspored, dogadjaji, termini, ucionice, osoblje, broj_ciklusa=ABC_BROJ_CIKLUSA, broj_izvora=ABC_BROJ_IZVORA, limit=ABC_LIMIT, seed=42):
    random.seed(seed)

    populacija = napravi_populaciju(pocetni_raspored, dogadjaji, termini, ucionice, osoblje, broj_izvora)
    najbolji = nadji_najbolji(populacija)

    historija = []
    historija.append({
        "ciklus": 0,
        "najbolji_fitness": najbolji["fitness"],
        "prosjek_fitness": prosjek_fitnessa(populacija)
    })

    for ciklus in range(1, broj_ciklusa + 1):
        # 1. Employed bees - svaka pcela pokusava popraviti svoj raspored.
        for i in range(len(populacija)):
            populacija[i] = popravi_izvor(populacija[i], dogadjaji, termini, ucionice, osoblje)

        # 2. Onlooker bees - vise paznje dobijaju bolji rasporedi.
        for i in range(len(populacija)):
            indeks = izaberi_izvor(populacija)
            populacija[indeks] = popravi_izvor(populacija[indeks], dogadjaji, termini, ucionice, osoblje)

        # 3. Scout bees - ako se neki raspored dugo ne popravi, zamijeni ga novim.
        zamijeni_lose_izvore(populacija, pocetni_raspored, dogadjaji, termini, ucionice, osoblje, limit)

        trenutni_najbolji = nadji_najbolji(populacija)
        if trenutni_najbolji["fitness"] < najbolji["fitness"]:
            najbolji = trenutni_najbolji

        if ciklus % 10 == 0 or ciklus == broj_ciklusa:
            historija.append({
                "ciklus": ciklus,
                "najbolji_fitness": najbolji["fitness"],
                "prosjek_fitness": prosjek_fitnessa(populacija)
            })

    return najbolji["raspored"], najbolji["fitness"], historija


def prosjek_fitnessa(populacija):
    if len(populacija) == 0:
        return 0

    suma = 0
    for izvor in populacija:
        suma += izvor["fitness"]

    return round(suma / len(populacija), 2)
