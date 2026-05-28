from pathlib import Path

from hard_constraints import napravi_mapu_redovnih
from hard_constraints import provjeri_raspored
from hard_constraints import satni_opseg
from hard_constraints import student_kljucevi
from parser import sat_iz_teksta
from parser import osoba_kljuc


DANI_REDOSLIJED = {
    "PONEDJELJAK": 1,
    "UTORAK": 2,
    "SRIJEDA": 3,
    "CETVRTAK": 4,
    "PETAK": 5
}


def vrijeme_broj(stavka):
    dan_broj = DANI_REDOSLIJED.get(stavka.dan, 0)
    sat = sat_iz_teksta(stavka.pocetak)
    return dan_broj * 100 + sat


def dodaj_penal(detalji, naziv, broj, tezina):
    ukupno = broj * tezina

    if naziv not in detalji:
        detalji[naziv] = {
            "broj": 0,
            "tezina": tezina,
            "ukupno": 0
        }

    detalji[naziv]["broj"] += broj
    detalji[naziv]["ukupno"] += ukupno

    return ukupno


def zauzeti_sati(stavka):
    sati = []
    opseg = satni_opseg(stavka.pocetak, stavka.trajanje_sati)

    for sat in opseg:
        sati.append(sat)

    return sati


def broj_rupa_u_danu(sati):
    if len(sati) <= 1:
        return 0

    sati = sorted(list(set(sati)))
    prvi = min(sati)
    zadnji = max(sati)
    rupe = 0

    for sat in range(prvi, zadnji + 1):
        if sat not in sati:
            rupe += 1

    return rupe


def najduzi_niz(sati):
    if len(sati) == 0:
        return 0

    sati = sorted(list(set(sati)))
    najbolji = 1
    trenutni = 1

    for i in range(1, len(sati)):
        if sati[i] == sati[i - 1] + 1:
            trenutni += 1
        else:
            trenutni = 1

        if trenutni > najbolji:
            najbolji = trenutni

    return najbolji


def penal_za_rupe_studentima(raspored, detalji):
    penal = 0
    mapa = {}

    for stavka in raspored:
        for student_kljuc in student_kljucevi(stavka):
            kljuc = (student_kljuc, stavka.dan)

            if kljuc not in mapa:
                mapa[kljuc] = []

            for sat in zauzeti_sati(stavka):
                mapa[kljuc].append(sat)

    for kljuc in mapa:
        rupe = broj_rupa_u_danu(mapa[kljuc])
        if rupe > 0:
            penal += dodaj_penal(detalji, "rupe_studentima", rupe, 20)

    return penal


def penal_za_previse_uzastopnih_studentima(raspored, detalji):
    penal = 0
    mapa = {}

    for stavka in raspored:
        for student_kljuc in student_kljucevi(stavka):
            kljuc = (student_kljuc, stavka.dan)

            if kljuc not in mapa:
                mapa[kljuc] = []

            for sat in zauzeti_sati(stavka):
                mapa[kljuc].append(sat)

    for kljuc in mapa:
        niz = najduzi_niz(mapa[kljuc])
        if niz > 5:
            visak = niz - 5
            penal += dodaj_penal(detalji, "vise_od_5_uzastopnih_studentima", visak, 50)

    return penal


def penal_za_neravnomjernost_studentima(raspored, detalji):
    penal = 0
    mapa = {}

    for stavka in raspored:
        for student_kljuc in student_kljucevi(stavka):
            if student_kljuc not in mapa:
                mapa[student_kljuc] = {}

            if stavka.dan not in mapa[student_kljuc]:
                mapa[student_kljuc][stavka.dan] = 0

            mapa[student_kljuc][stavka.dan] += stavka.trajanje_sati

    for kljuc in mapa:
        sati_po_danu = []

        for dan in DANI_REDOSLIJED:
            sati_po_danu.append(mapa[kljuc].get(dan, 0))

        najveci = max(sati_po_danu)
        najmanji = min(sati_po_danu)

        # Ako je razlika velika, raspored je previse koncentrisan u neke dane.
        if najveci - najmanji > 4:
            penal += dodaj_penal(detalji, "neravnomjerno_po_danima", najveci - najmanji - 4, 15)

    return penal


def penal_za_master_prerano(raspored, detalji):
    penal = 0

    for stavka in raspored:
        if stavka.ciklus.lower() == "master":
            pocetak = sat_iz_teksta(stavka.pocetak)

            if pocetak < 14:
                penal += dodaj_penal(detalji, "master_prije_14h", 1, 30)

    return penal


def penal_za_vjezbe_prije_predavanja(raspored, detalji):
    penal = 0
    predavanja = {}

    for stavka in raspored:
        if stavka.tip == "P":
            kljuc = (stavka.predmet, stavka.ciklus, stavka.semestar, stavka.smjerovi)
            vrijeme = vrijeme_broj(stavka)

            if kljuc not in predavanja or vrijeme < predavanja[kljuc]:
                predavanja[kljuc] = vrijeme

    for stavka in raspored:
        if stavka.tip == "AV" or stavka.tip == "LV":
            kljuc = (stavka.predmet, stavka.ciklus, stavka.semestar, stavka.smjerovi)

            if kljuc in predavanja:
                if vrijeme_broj(stavka) < predavanja[kljuc]:
                    penal += dodaj_penal(detalji, "vjezbe_prije_predavanja", 1, 40)

    return penal


def penal_za_rupe_nastavnicima(raspored, detalji):
    penal = 0
    mapa = {}

    for stavka in raspored:
        kljuc = (osoba_kljuc(stavka.nastavnik), stavka.dan)

        if kljuc not in mapa:
            mapa[kljuc] = []

        for sat in zauzeti_sati(stavka):
            mapa[kljuc].append(sat)

    for kljuc in mapa:
        rupe = broj_rupa_u_danu(mapa[kljuc])
        if rupe > 0:
            penal += dodaj_penal(detalji, "rupe_nastavnicima", rupe, 10)

    return penal


def penal_za_spoljne_saradnike_prerano(raspored, osoblje, detalji):
    penal = 0
    redovni = napravi_mapu_redovnih(osoblje)

    for stavka in raspored:
        pocetak = sat_iz_teksta(stavka.pocetak)
        osoba = osoba_kljuc(stavka.nastavnik)

        if redovni.get(osoba, 1) == 0 and pocetak < 16:
            penal += dodaj_penal(detalji, "spoljni_saradnik_prije_16h", 1, 50)

    return penal


def ima_ime(stavka, tekst):
    return tekst.lower() in osoba_kljuc(stavka.nastavnik)


def penal_za_individualne_zelje(raspored, detalji):
    # Ovdje su samo jednostavne zelje koje se mogu lako provjeriti iz ogranicenja.csv.
    # Tezina je manja od hard constraints jer ovo nisu obavezna pravila.
    penal = 0

    dani_po_nastavniku = {}

    for stavka in raspored:
        osoba = osoba_kljuc(stavka.nastavnik)
        if osoba not in dani_po_nastavniku:
            dani_po_nastavniku[osoba] = []
        if stavka.dan not in dani_po_nastavniku[osoba]:
            dani_po_nastavniku[osoba].append(stavka.dan)

        sat = sat_iz_teksta(stavka.pocetak)

        if ima_ime(stavka, "senada"):
            if stavka.dan not in ["UTORAK", "SRIJEDA"] or sat >= 12:
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)

        if ima_ime(stavka, "esmir"):
            if sat >= 14 or stavka.dan == "PETAK":
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)

        if ima_ime(stavka, "fikret"):
            if sat >= 14 or stavka.dan == "PETAK":
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)

        if ima_ime(stavka, "franjo"):
            if sat >= 15 or stavka.dan == "PONEDJELJAK":
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)

        if ima_ime(stavka, "amil"):
            if sat < 10 or sat > 15 or stavka.dan == "PETAK":
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)

        if ima_ime(stavka, "zenan"):
            if sat < 9 or stavka.dan not in ["SRIJEDA", "CETVRTAK"]:
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)

        if ima_ime(stavka, "vedad"):
            if sat < 16:
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)

        if ima_ime(stavka, "eldina"):
            if sat < 14:
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)

        if ima_ime(stavka, "imrana"):
            if sat < 15:
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)

        if ima_ime(stavka, "elmedin"):
            if sat < 9:
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)
            if stavka.ucionica_id == "VRC":
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)
            if stavka.predmet == "Kompjuterska grafika" and stavka.dan != "CETVRTAK":
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)

        if ima_ime(stavka, "sead"):
            if sat < 12:
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)
            if stavka.ucionica_id not in ["ABG", "VRC"]:
                penal += dodaj_penal(detalji, "individualne_zelje", 1, 15)

    # Zelje tipa jedan dan ili maksimalno dva dana.
    for osoba in dani_po_nastavniku:
        broj_dana = len(dani_po_nastavniku[osoba])

        if "aleksandra" in osoba or "emil" in osoba:
            if broj_dana > 1:
                penal += dodaj_penal(detalji, "individualne_zelje", broj_dana - 1, 15)

        if "hasnija" in osoba or "damir" in osoba or "lejla" in osoba or "samir" in osoba:
            if broj_dana > 2:
                penal += dodaj_penal(detalji, "individualne_zelje", broj_dana - 2, 15)

    return penal


def izracunaj_fitness(raspored, dogadjaji, ucionice, osoblje):
    detalji = {}
    ukupno = 0

    hard_greske = provjeri_raspored(raspored, ucionice, osoblje)
    ukupno += dodaj_penal(detalji, "hard_constraint_greske", len(hard_greske), 1000000)

    rasporedjeni = {}
    for stavka in raspored:
        rasporedjeni[stavka.dogadjaj_id] = True

    nerasporedjeni = 0
    for dogadjaj in dogadjaji:
        if dogadjaj.dogadjaj_id not in rasporedjeni:
            nerasporedjeni += 1

    ukupno += dodaj_penal(detalji, "nerasporedjeni_dogadjaji", nerasporedjeni, 100000)

    ukupno += penal_za_rupe_studentima(raspored, detalji)
    ukupno += penal_za_previse_uzastopnih_studentima(raspored, detalji)
    ukupno += penal_za_neravnomjernost_studentima(raspored, detalji)
    ukupno += penal_za_master_prerano(raspored, detalji)
    ukupno += penal_za_vjezbe_prije_predavanja(raspored, detalji)
    ukupno += penal_za_rupe_nastavnicima(raspored, detalji)
    ukupno += penal_za_spoljne_saradnike_prerano(raspored, osoblje, detalji)
    ukupno += penal_za_individualne_zelje(raspored, detalji)

    return ukupno, detalji, hard_greske


def napravi_tekstualni_izvjestaj(ukupno, detalji, hard_greske):
    linije = []
    linije.append("=== FITNESS RASPOREDA ===")
    linije.append("Ukupni fitness: " + str(ukupno))
    linije.append("")
    linije.append("Manji fitness znaci bolji raspored.")
    linije.append("")
    linije.append("Detalji penala:")

    for naziv in sorted(detalji.keys()):
        d = detalji[naziv]
        linije.append("- " + naziv + ": broj=" + str(d["broj"]) + ", tezina=" + str(d["tezina"]) + ", penal=" + str(d["ukupno"]))

    linije.append("")
    linije.append("Broj hard constraint gresaka: " + str(len(hard_greske)))

    if len(hard_greske) > 0:
        linije.append("")
        linije.append("Hard constraint greske:")
        for greska in hard_greske[:100]:
            linije.append("- " + greska)

    return "\n".join(linije)


def sacuvaj_fitness_izvjestaj(putanja, ukupno, detalji, hard_greske):
    putanja = Path(putanja)
    putanja.parent.mkdir(parents=True, exist_ok=True)

    tekst = napravi_tekstualni_izvjestaj(ukupno, detalji, hard_greske)

    with open(putanja, "w", encoding="utf-8") as f:
        f.write(tekst)

    return tekst
