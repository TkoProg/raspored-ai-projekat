import csv
from pathlib import Path

from modeli import Predmet
from modeli import Osoba
from modeli import Ucionica
from modeli import StudentskaGrupa
from modeli import Termin
from modeli import Ogranicenje
from modeli import NastavniDogadjaj
from modeli import StavkaRasporeda


def citaj_csv(putanja):
    redovi = []
    with open(putanja, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for red in reader:
            redovi.append(red)
    return redovi


def ocisti_tekst(vrijednost):
    return str(vrijednost).strip()


def normalizuj_smjer(smjer):
    smjer = ocisti_tekst(smjer)

    if smjer == "Primjenjena matematika":
        return "Primijenjena matematika"

    if smjer == "Nastavnički smjer (matematika I informatika)":
        return "Nastavnički smjer (matematika i informatika)"

    return smjer


def smjer_kljuc(smjer):
    smjer = ocisti_tekst(smjer).lower()

    if smjer == "primjenjena matematika":
        return "primijenjena matematika"

    if smjer == "nastavnički smjer (matematika i informatika)":
        return "nastavnički smjer (matematika i informatika)"

    return smjer


def predmet_kljuc(predmet):
    return ocisti_tekst(predmet).lower()


def osoba_kljuc(ime):
    return ocisti_tekst(ime).lower()


def godina_iz_semestra(semestar):
    semestar = int(semestar)

    if semestar == 1 or semestar == 2:
        return "I godina"

    if semestar == 3 or semestar == 4:
        return "II godina"

    if semestar == 5 or semestar == 6:
        return "III godina"

    if semestar == 7 or semestar == 8:
        return "IV godina"

    return "Nepoznata godina"


def sat_iz_teksta(vrijeme):
    tekst = ocisti_tekst(vrijeme)
    return int(tekst.split(":")[0])


def ucitaj_predmete(data_dir):
    redovi = citaj_csv(Path(data_dir) / "predmeti.csv")
    predmeti = []

    for red in redovi:
        predmet = Predmet(
            predmet=ocisti_tekst(red["predmet"]),
            smjer=normalizuj_smjer(red["smjer"]),
            ciklus=ocisti_tekst(red["ciklus"]),
            semestar=int(red["semestar"]),
            p=int(red["P"]),
            av=int(red["AV"]),
            lv=int(red["LV"]),
            tip=ocisti_tekst(red["tip"])
        )
        predmeti.append(predmet)

    return predmeti


def ucitaj_osoblje(data_dir):
    redovi = citaj_csv(Path(data_dir) / "osoblje.csv")
    osoblje = []

    for red in redovi:
        osoba = Osoba(
            ime=ocisti_tekst(red["ime"]),
            predmet=ocisti_tekst(red["predmet"]),
            tip=ocisti_tekst(red["tip"]),
            redovni=int(red["redovni"])
        )
        osoblje.append(osoba)

    return osoblje


def ucitaj_ucionice(data_dir):
    redovi = citaj_csv(Path(data_dir) / "ucionice.csv")
    ucionice = []

    for red in redovi:
        ucionica = Ucionica(
            ucionica_id=ocisti_tekst(red["ucionica_id"]),
            lab=int(red["lab"]),
            kapacitet=int(red["kapacitet"])
        )
        ucionice.append(ucionica)

    return ucionice


def ucitaj_studente(data_dir):
    redovi = citaj_csv(Path(data_dir) / "studenti.csv")
    studenti = []

    for red in redovi:
        grupa = StudentskaGrupa(
            smjer=normalizuj_smjer(red["smjer"]),
            ciklus=ocisti_tekst(red["ciklus"]),
            godina=ocisti_tekst(red["godina"]),
            broj_studenata=int(red["broj_studenata"])
        )
        studenti.append(grupa)

    return studenti


def ucitaj_termine(data_dir):
    redovi = citaj_csv(Path(data_dir) / "termini.csv")
    termini = []

    for red in redovi:
        termin = Termin(
            termin_id=ocisti_tekst(red["termin_id"]),
            dan=ocisti_tekst(red["dan"]),
            pocetak=ocisti_tekst(red["pocetak"]),
            kraj=ocisti_tekst(red["kraj"]),
            trajanje_minuta=int(red["trajanje_minuta"]),
            slot=int(red["slot"])
        )
        termini.append(termin)

    return termini


def ucitaj_ogranicenja(data_dir):
    redovi = citaj_csv(Path(data_dir) / "ogranicenja.csv")
    ogranicenja = []

    for red in redovi:
        ogranicenje = Ogranicenje(
            tip=ocisti_tekst(red["Tip"]),
            oznaka=ocisti_tekst(red["ID"]),
            opis=ocisti_tekst(red["Opis"])
        )
        ogranicenja.append(ogranicenje)

    return ogranicenja


def ucitaj_dogadjaje(putanja):
    redovi = citaj_csv(putanja)
    dogadjaji = []

    for red in redovi:
        dogadjaj = NastavniDogadjaj(
            dogadjaj_id=ocisti_tekst(red["dogadjaj_id"]),
            predmet=ocisti_tekst(red["predmet"]),
            tip=ocisti_tekst(red["tip"]),
            trajanje_sati=int(red["trajanje_sati"]),
            trajanje_minuta=int(red["trajanje_minuta"]),
            nastavnik=ocisti_tekst(red["nastavnik"]),
            smjerovi=ocisti_tekst(red["smjerovi"]),
            ciklus=ocisti_tekst(red["ciklus"]),
            semestar=int(red["semestar"]),
            godina=ocisti_tekst(red["godina"]),
            broj_studenata=int(red["broj_studenata"]),
            treba_lab=int(red["treba_lab"]),
            grupa=ocisti_tekst(red.get("grupa", "G1"))
        )
        dogadjaji.append(dogadjaj)

    return dogadjaji


def ucitaj_raspored(putanja):
    redovi = citaj_csv(putanja)
    raspored = []

    for red in redovi:
        stavka = StavkaRasporeda(
            dogadjaj_id=ocisti_tekst(red["dogadjaj_id"]),
            predmet=ocisti_tekst(red["predmet"]),
            tip=ocisti_tekst(red["tip"]),
            nastavnik=ocisti_tekst(red["nastavnik"]),
            smjerovi=ocisti_tekst(red["smjerovi"]),
            ciklus=ocisti_tekst(red["ciklus"]),
            semestar=int(red["semestar"]),
            godina=ocisti_tekst(red["godina"]),
            grupa=ocisti_tekst(red["grupa"]),
            broj_studenata=int(red["broj_studenata"]),
            ucionica_id=ocisti_tekst(red["ucionica_id"]),
            dan=ocisti_tekst(red["dan"]),
            pocetak=ocisti_tekst(red["pocetak"]),
            kraj=ocisti_tekst(red["kraj"]),
            trajanje_sati=int(red["trajanje_sati"])
        )
        raspored.append(stavka)

    return raspored
