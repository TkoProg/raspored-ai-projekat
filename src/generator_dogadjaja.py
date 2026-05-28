import csv
import math
from pathlib import Path

from modeli import NastavniDogadjaj
from parser import predmet_kljuc
from parser import smjer_kljuc
from parser import godina_iz_semestra


def napravi_mapu_osoblja(osoblje):
    mapa = {}

    for osoba in osoblje:
        kljuc = (predmet_kljuc(osoba.predmet), osoba.tip)
        if kljuc not in mapa:
            mapa[kljuc] = []

        mapa[kljuc].append(osoba.ime)

    return mapa


def napravi_mapu_studenata(studenti):
    mapa = {}

    for grupa in studenti:
        kljuc = (smjer_kljuc(grupa.smjer), grupa.ciklus.lower(), grupa.godina.lower())
        mapa[kljuc] = grupa.broj_studenata

    return mapa


def rastavi_fond_sati(fond):
    # Fond sati predstavlja trajanje jednog nastavnog bloka.
    # Ako predmet ima 3 casa P/AV/LV, to mora ostati jedan blok od 3 casa,
    # a ne dva odvojena dogadjaja 2 + 1.
    blokovi = []

    if fond <= 0:
        return blokovi

    if fond <= 3:
        return [fond]

    # Za fond 4 zadrzavamo dva bloka po 2 casa, sto je najprirodnije
    # za raspored. Ako se nekad pojavi veci fond, izbjegavamo blok od 1 casa
    # kada god je moguce.
    while fond > 0:
        if fond == 3:
            blokovi.append(3)
            fond -= 3
        elif fond >= 2:
            blokovi.append(2)
            fond -= 2
        else:
            blokovi.append(1)
            fond -= 1

    return blokovi


def najveci_lab_kapacitet(ucionice):
    najveci = 0

    for ucionica in ucionice:
        if ucionica.lab == 1 and ucionica.kapacitet > najveci:
            najveci = ucionica.kapacitet

    return najveci


def grupisi_predmete(predmeti, studenti):
    mapa_studenata = napravi_mapu_studenata(studenti)
    grupe = {}

    for predmet in predmeti:
        godina = godina_iz_semestra(predmet.semestar)

        kljuc_studenata = (
            smjer_kljuc(predmet.smjer),
            predmet.ciklus.lower(),
            godina.lower()
        )

        broj_studenata = 0
        if kljuc_studenata in mapa_studenata:
            broj_studenata = mapa_studenata[kljuc_studenata]

        tipovi = [
            ("P", predmet.p),
            ("AV", predmet.av),
            ("LV", predmet.lv)
        ]

        for tip, fond in tipovi:
            if fond <= 0:
                continue

            kljuc = (
                predmet.predmet,
                predmet.ciklus,
                predmet.semestar,
                tip
            )

            if kljuc not in grupe:
                grupe[kljuc] = {
                    "predmet": predmet.predmet,
                    "ciklus": predmet.ciklus,
                    "semestar": predmet.semestar,
                    "tip": tip,
                    "fond": fond,
                    "smjerovi": [],
                    "broj_studenata": 0
                }

            if predmet.smjer not in grupe[kljuc]["smjerovi"]:
                grupe[kljuc]["smjerovi"].append(predmet.smjer)

            grupe[kljuc]["broj_studenata"] += broj_studenata

    return grupe


def generisi_dogadjaje(predmeti, osoblje, studenti, ucionice):
    dogadjaji = []
    mapa_osoblja = napravi_mapu_osoblja(osoblje)
    grupe = grupisi_predmete(predmeti, studenti)
    max_lab = najveci_lab_kapacitet(ucionice)

    brojac = 1

    for kljuc in sorted(grupe.keys()):
        grupa_podatak = grupe[kljuc]

        predmet = grupa_podatak["predmet"]
        ciklus = grupa_podatak["ciklus"]
        semestar = grupa_podatak["semestar"]
        tip = grupa_podatak["tip"]
        fond = grupa_podatak["fond"]
        ukupno_studenata = grupa_podatak["broj_studenata"]

        broj_grupa = 1

        # Za sada dijelimo samo LV, jer laboratorijske vjezbe stvarno zavise od kapaciteta laba.
        if tip == "LV" and max_lab > 0 and ukupno_studenata > max_lab:
            broj_grupa = math.ceil(ukupno_studenata / max_lab)

        broj_po_grupi = math.ceil(ukupno_studenata / broj_grupa)

        kljuc_osoblja = (predmet_kljuc(predmet), tip)
        nastavnici = mapa_osoblja.get(kljuc_osoblja, [])

        if len(nastavnici) == 0:
            nastavnici = ["NEPOZNATO"]

        for broj_grupe in range(1, broj_grupa + 1):
            blokovi = rastavi_fond_sati(fond)
            indeks_nastavnika = 0

            for trajanje_sati in blokovi:
                nastavnik = nastavnici[indeks_nastavnika % len(nastavnici)]
                indeks_nastavnika += 1

                dogadjaj = NastavniDogadjaj(
                    dogadjaj_id="D" + str(brojac).zfill(4),
                    predmet=predmet,
                    tip=tip,
                    trajanje_sati=trajanje_sati,
                    trajanje_minuta=trajanje_sati * 60,
                    nastavnik=nastavnik,
                    smjerovi=" | ".join(sorted(grupa_podatak["smjerovi"])),
                    ciklus=ciklus,
                    semestar=semestar,
                    godina=godina_iz_semestra(semestar),
                    broj_studenata=broj_po_grupi,
                    treba_lab=1 if tip == "LV" else 0,
                    grupa="G" + str(broj_grupe)
                )

                dogadjaji.append(dogadjaj)
                brojac += 1

    return dogadjaji


def sacuvaj_dogadjaje(dogadjaji, putanja):
    putanja = Path(putanja)
    putanja.parent.mkdir(parents=True, exist_ok=True)

    kolone = [
        "dogadjaj_id",
        "predmet",
        "tip",
        "trajanje_sati",
        "trajanje_minuta",
        "nastavnik",
        "smjerovi",
        "ciklus",
        "semestar",
        "godina",
        "broj_studenata",
        "treba_lab",
        "grupa"
    ]

    with open(putanja, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(kolone)

        for d in dogadjaji:
            writer.writerow([
                d.dogadjaj_id,
                d.predmet,
                d.tip,
                d.trajanje_sati,
                d.trajanje_minuta,
                d.nastavnik,
                d.smjerovi,
                d.ciklus,
                d.semestar,
                d.godina,
                d.broj_studenata,
                d.treba_lab,
                d.grupa
            ])
