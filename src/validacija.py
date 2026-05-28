from parser import predmet_kljuc
from parser import smjer_kljuc
from parser import godina_iz_semestra
from generator_dogadjaja import generisi_dogadjaje
from parametri import NAJKASNIJI_KRAJ_NASTAVE
from parser import sat_iz_teksta


def dodaj(lista, poruka):
    lista.append(poruka)


def validiraj_podatke(predmeti, osoblje, ucionice, studenti, termini):
    greske = []
    upozorenja = []

    if len(predmeti) == 0:
        dodaj(greske, "Nema predmeta.")

    if len(osoblje) == 0:
        dodaj(greske, "Nema osoblja.")

    if len(ucionice) == 0:
        dodaj(greske, "Nema ucionica.")

    if len(studenti) == 0:
        dodaj(greske, "Nema studentskih grupa.")

    if len(termini) == 0:
        dodaj(greske, "Nema termina.")

    mapa_osoblja = {}

    for osoba in osoblje:
        kljuc = (predmet_kljuc(osoba.predmet), osoba.tip)
        mapa_osoblja[kljuc] = True

    for predmet in predmeti:
        if predmet.p > 0:
            kljuc = (predmet_kljuc(predmet.predmet), "P")
            if kljuc not in mapa_osoblja:
                dodaj(greske, "Nema nastavnika za P: " + predmet.predmet)

        if predmet.av > 0:
            kljuc = (predmet_kljuc(predmet.predmet), "AV")
            if kljuc not in mapa_osoblja:
                dodaj(greske, "Nema asistenta za AV: " + predmet.predmet)

        if predmet.lv > 0:
            kljuc = (predmet_kljuc(predmet.predmet), "LV")
            if kljuc not in mapa_osoblja:
                dodaj(greske, "Nema asistenta za LV: " + predmet.predmet)

    mapa_studenata = {}

    for grupa in studenti:
        kljuc = (smjer_kljuc(grupa.smjer), grupa.ciklus.lower(), grupa.godina.lower())
        mapa_studenata[kljuc] = True

    vec_prijavljeno = {}

    for predmet in predmeti:
        godina = godina_iz_semestra(predmet.semestar)
        kljuc = (smjer_kljuc(predmet.smjer), predmet.ciklus.lower(), godina.lower())

        if kljuc not in mapa_studenata and kljuc not in vec_prijavljeno:
            dodaj(greske, "Nema broja studenata za: " + predmet.smjer + ", " + predmet.ciklus + ", " + godina)
            vec_prijavljeno[kljuc] = True

    ocekivani_broj_termina = 5 * (NAJKASNIJI_KRAJ_NASTAVE - 8)
    if len(termini) != ocekivani_broj_termina:
        dodaj(
            upozorenja,
            "Termin fajl bi trebao imati " + str(ocekivani_broj_termina) +
            " termina ako se koristi 1h slot od 08:00 do " +
            str(NAJKASNIJI_KRAJ_NASTAVE).zfill(2) + ":00 za 5 dana."
        )

    for termin in termini:
        if termin.trajanje_minuta != 60:
            dodaj(upozorenja, "Termin nije 1h: " + termin.termin_id)

        if sat_iz_teksta(termin.kraj) > NAJKASNIJI_KRAJ_NASTAVE:
            dodaj(greske, "Termin zavrsava poslije 19:00: " + termin.termin_id)

    dogadjaji = generisi_dogadjaje(predmeti, osoblje, studenti, ucionice)

    najveci_kapacitet = 0
    for ucionica in ucionice:
        if ucionica.kapacitet > najveci_kapacitet:
            najveci_kapacitet = ucionica.kapacitet

    for d in dogadjaji:
        if d.broj_studenata > najveci_kapacitet:
            dodaj(greske, "Nijedna ucionica nema kapacitet za: " + d.predmet)

    return greske, upozorenja


def ispisi_validaciju(predmeti, osoblje, ucionice, studenti, termini, ogranicenja):
    greske, upozorenja = validiraj_podatke(predmeti, osoblje, ucionice, studenti, termini)

    print("=== VALIDACIJA PODATAKA ===")
    print("Predmeti:", len(predmeti))
    print("Osoblje:", len(osoblje))
    print("Ucionice:", len(ucionice))
    print("Studentske grupe:", len(studenti))
    print("Termini:", len(termini))
    print("Ogranicenja:", len(ogranicenja))
    print()

    if len(greske) == 0:
        print("Greske: 0")
    else:
        print("Greske:", len(greske))
        for greska in greske:
            print("-", greska)

    print()

    if len(upozorenja) == 0:
        print("Upozorenja: 0")
    else:
        print("Upozorenja:", len(upozorenja))
        for upozorenje in upozorenja:
            print("-", upozorenje)

    return greske, upozorenja
