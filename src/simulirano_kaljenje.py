import math
import random

from parametri import SA_BROJ_ITERACIJA
from parametri import SA_POCETNA_TEMPERATURA
from parametri import SA_HLADJENJE

from modeli import StavkaRasporeda
from fitness import izracunaj_fitness
from hard_constraints import lv_dozvoljena_ucionica
from hard_constraints import napravi_mapu_redovnih
from hard_constraints import satni_opseg
from hard_constraints import student_kljucevi
from hard_constraints import termin_staje_u_radno_vrijeme
from parser import sat_iz_teksta
from parser import osoba_kljuc


def kopiraj_stavku(stavka):
    return StavkaRasporeda(
        dogadjaj_id=stavka.dogadjaj_id,
        predmet=stavka.predmet,
        tip=stavka.tip,
        nastavnik=stavka.nastavnik,
        smjerovi=stavka.smjerovi,
        ciklus=stavka.ciklus,
        semestar=stavka.semestar,
        godina=stavka.godina,
        grupa=stavka.grupa,
        broj_studenata=stavka.broj_studenata,
        ucionica_id=stavka.ucionica_id,
        dan=stavka.dan,
        pocetak=stavka.pocetak,
        kraj=stavka.kraj,
        trajanje_sati=stavka.trajanje_sati
    )


def kopiraj_raspored(raspored):
    kopija = []
    for stavka in raspored:
        kopija.append(kopiraj_stavku(stavka))
    return kopija


def termin_odgovara(stavka, termin):
    return termin_staje_u_radno_vrijeme(termin.pocetak, stavka.trajanje_sati)


def ucionica_odgovara(stavka, ucionica):
    if ucionica.kapacitet < stavka.broj_studenata:
        return False

    if not lv_dozvoljena_ucionica(stavka, ucionica):
        return False

    return True


def napravi_premjestenu_stavku(stavka, termin, ucionica):
    nova = kopiraj_stavku(stavka)
    nova.ucionica_id = ucionica.ucionica_id
    nova.dan = termin.dan
    nova.pocetak = termin.pocetak
    nova.kraj = str(sat_iz_teksta(termin.pocetak) + stavka.trajanje_sati).zfill(2) + ":00"
    return nova


def napravi_mape_zauzetosti(raspored, preskoci_indeks):
    zauzeti_nastavnici = {}
    zauzete_ucionice = {}
    zauzeti_studenti = {}

    for i in range(len(raspored)):
        if i == preskoci_indeks:
            continue

        stavka = raspored[i]
        sati = satni_opseg(stavka.pocetak, stavka.trajanje_sati)

        for sat in sati:
            zauzeti_nastavnici[(osoba_kljuc(stavka.nastavnik), stavka.dan, sat)] = stavka.dogadjaj_id
            zauzete_ucionice[(stavka.ucionica_id, stavka.dan, sat)] = stavka.dogadjaj_id
            for student_kljuc in student_kljucevi(stavka):
                zauzeti_studenti[(student_kljuc, stavka.dan, sat)] = stavka.dogadjaj_id

    return zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti


def moze_premjestiti(stavka, mapa_redovnih, zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti):
    if not termin_staje_u_radno_vrijeme(stavka.pocetak, stavka.trajanje_sati):
        return False

    sati = satni_opseg(stavka.pocetak, stavka.trajanje_sati)

    if stavka.dan == "CETVRTAK":
        redovni = mapa_redovnih.get(osoba_kljuc(stavka.nastavnik), 0)
        if redovni == 1 and 13 in sati:
            return False

    for sat in sati:
        if (osoba_kljuc(stavka.nastavnik), stavka.dan, sat) in zauzeti_nastavnici:
            return False

        if (stavka.ucionica_id, stavka.dan, sat) in zauzete_ucionice:
            return False

        for student_kljuc in student_kljucevi(stavka):
            if (student_kljuc, stavka.dan, sat) in zauzeti_studenti:
                return False

    return True


def napravi_susjeda(raspored, termini, ucionice, osoblje):
    if len(raspored) == 0:
        return None

    mapa_redovnih = napravi_mapu_redovnih(osoblje)

    # Prvo biramo jednu stavku koju cemo pomjeriti, pa onda trazimo validan novi termin/ucionicu.
    for pokusaj_stavke in range(20):
        indeks = random.randrange(len(raspored))
        stara_stavka = raspored[indeks]

        zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti = napravi_mape_zauzetosti(raspored, indeks)

        for pokusaj in range(40):
            termin = random.choice(termini)
            ucionica = random.choice(ucionice)

            if not termin_odgovara(stara_stavka, termin):
                continue

            if not ucionica_odgovara(stara_stavka, ucionica):
                continue

            nova_stavka = napravi_premjestenu_stavku(stara_stavka, termin, ucionica)

            if moze_premjestiti(nova_stavka, mapa_redovnih, zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti):
                novi_raspored = kopiraj_raspored(raspored)
                novi_raspored[indeks] = nova_stavka
                return novi_raspored

    return None


def vjerovatnoca_prihvatanja(razlika, temperatura):
    if razlika < 0:
        return 1.0

    if temperatura <= 0:
        return 0.0

    return math.exp(-razlika / temperatura)


def simulirano_kaljenje(raspored, dogadjaji, termini, ucionice, osoblje, broj_iteracija=SA_BROJ_ITERACIJA, pocetna_temperatura=SA_POCETNA_TEMPERATURA, hladjenje=SA_HLADJENJE, seed=42):
    random.seed(seed)

    trenutni = kopiraj_raspored(raspored)
    najbolji = kopiraj_raspored(raspored)

    trenutni_fitness, _, _ = izracunaj_fitness(trenutni, dogadjaji, ucionice, osoblje)
    najbolji_fitness = trenutni_fitness

    temperatura = pocetna_temperatura
    historija = []

    historija.append({
        "iteracija": 0,
        "trenutni_fitness": trenutni_fitness,
        "najbolji_fitness": najbolji_fitness,
        "temperatura": round(temperatura, 4)
    })

    for iteracija in range(1, broj_iteracija + 1):
        kandidat = napravi_susjeda(trenutni, termini, ucionice, osoblje)

        if kandidat is not None:
            kandidat_fitness, _, _ = izracunaj_fitness(kandidat, dogadjaji, ucionice, osoblje)
            razlika = kandidat_fitness - trenutni_fitness
            vjerovatnoca = vjerovatnoca_prihvatanja(razlika, temperatura)

            if random.random() < vjerovatnoca:
                trenutni = kandidat
                trenutni_fitness = kandidat_fitness

                if trenutni_fitness < najbolji_fitness:
                    najbolji = kopiraj_raspored(trenutni)
                    najbolji_fitness = trenutni_fitness

        temperatura = temperatura * hladjenje

        if iteracija % 50 == 0 or iteracija == broj_iteracija:
            historija.append({
                "iteracija": iteracija,
                "trenutni_fitness": trenutni_fitness,
                "najbolji_fitness": najbolji_fitness,
                "temperatura": round(temperatura, 4)
            })

    return najbolji, najbolji_fitness, historija
