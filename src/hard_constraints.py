from parser import osoba_kljuc
from parser import sat_iz_teksta
from parametri import NAJKASNIJI_KRAJ_NASTAVE


def napravi_mapu_ucionica(ucionice):
    mapa = {}
    for ucionica in ucionice:
        mapa[ucionica.ucionica_id] = ucionica
    return mapa


def napravi_mapu_redovnih(osoblje):
    mapa = {}
    for osoba in osoblje:
        mapa[osoba_kljuc(osoba.ime)] = osoba.redovni
    return mapa


def satni_opseg(pocetak, trajanje_sati):
    prvi_sat = sat_iz_teksta(pocetak)
    sati = []

    for i in range(trajanje_sati):
        sati.append(prvi_sat + i)

    return sati


def termin_staje_u_radno_vrijeme(pocetak, trajanje_sati):
    return sat_iz_teksta(pocetak) + trajanje_sati <= NAJKASNIJI_KRAJ_NASTAVE


def smjerovi_lista(smjerovi):
    lista = []

    for dio in str(smjerovi).split("|"):
        dio = dio.strip()
        if dio != "":
            lista.append(dio)

    return lista


def student_kljucevi(stavka):
    kljucevi = []

    for smjer in smjerovi_lista(stavka.smjerovi):
        kljuc = smjer + "|" + stavka.ciklus + "|" + str(stavka.semestar) + "|" + stavka.godina
        kljucevi.append(kljuc)

    return kljucevi


def lv_dozvoljena_ucionica(stavka, ucionica):
    if stavka.tip != "LV":
        return True

    if ucionica.lab == 1:
        return True

    # Zbog soft pravila u ogranicenjima: Programiranje I po mogucnosti u ABG.
    # ABG u CSV-u nije oznacen kao lab, ali ga ovdje dozvoljavamo samo za taj predmet.
    if stavka.predmet == "Programiranje I" and ucionica.ucionica_id == "ABG":
        return True

    return False


def provjeri_stavku(stavka, ucionice, osoblje):
    greske = []
    mapa_ucionica = napravi_mapu_ucionica(ucionice)
    mapa_redovnih = napravi_mapu_redovnih(osoblje)

    if stavka.ucionica_id not in mapa_ucionica:
        greske.append("Nepoznata ucionica: " + stavka.ucionica_id)
        return greske

    ucionica = mapa_ucionica[stavka.ucionica_id]

    if ucionica.kapacitet < stavka.broj_studenata:
        greske.append("Kapacitet ucionice je premali za " + stavka.dogadjaj_id)

    if not lv_dozvoljena_ucionica(stavka, ucionica):
        greske.append("LV nije u lab ucionici: " + stavka.dogadjaj_id)

    if not termin_staje_u_radno_vrijeme(stavka.pocetak, stavka.trajanje_sati):
        greske.append("Nastava zavrsava poslije 19:00: " + stavka.dogadjaj_id)

    if stavka.dan == "CETVRTAK":
        sati = satni_opseg(stavka.pocetak, stavka.trajanje_sati)
        redovni = mapa_redovnih.get(osoba_kljuc(stavka.nastavnik), 0)

        if redovni == 1 and 13 in sati:
            greske.append("Redovno zaposlen ima nastavu cetvrtkom 13-14: " + stavka.nastavnik)

    return greske


def provjeri_raspored(raspored, ucionice, osoblje):
    greske = []

    zauzeti_nastavnici = {}
    zauzete_ucionice = {}
    zauzeti_studenti = {}

    for stavka in raspored:
        lokalne_greske = provjeri_stavku(stavka, ucionice, osoblje)
        for greska in lokalne_greske:
            greske.append(greska)

        sati = satni_opseg(stavka.pocetak, stavka.trajanje_sati)

        for sat in sati:
            kljuc_nastavnik = (osoba_kljuc(stavka.nastavnik), stavka.dan, sat)
            kljuc_ucionica = (stavka.ucionica_id, stavka.dan, sat)

            if kljuc_nastavnik in zauzeti_nastavnici:
                greske.append("Nastavnik ima sudar: " + stavka.nastavnik + " u " + stavka.dan + " " + str(sat))
            else:
                zauzeti_nastavnici[kljuc_nastavnik] = stavka.dogadjaj_id

            if kljuc_ucionica in zauzete_ucionice:
                greske.append("Ucionica ima sudar: " + stavka.ucionica_id + " u " + stavka.dan + " " + str(sat))
            else:
                zauzete_ucionice[kljuc_ucionica] = stavka.dogadjaj_id

            for student_kljuc_pojedinacni in student_kljucevi(stavka):
                kljuc_studenti = (student_kljuc_pojedinacni, stavka.dan, sat)

                if kljuc_studenti in zauzeti_studenti:
                    greske.append("Studenti imaju sudar: " + student_kljuc_pojedinacni + " u " + stavka.dan + " " + str(sat))
                else:
                    zauzeti_studenti[kljuc_studenti] = stavka.dogadjaj_id

    return greske

