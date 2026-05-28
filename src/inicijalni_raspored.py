import csv
import random
from pathlib import Path

from modeli import StavkaRasporeda
from parser import osoba_kljuc
from parser import sat_iz_teksta
from hard_constraints import napravi_mapu_redovnih
from hard_constraints import lv_dozvoljena_ucionica
from hard_constraints import satni_opseg
from hard_constraints import student_kljucevi
from hard_constraints import termin_staje_u_radno_vrijeme


def broj_mogucih_ucionica(dogadjaj, ucionice):
    broj = 0

    for ucionica in ucionice:
        if ucionica.kapacitet < dogadjaj.broj_studenata:
            continue

        if not lv_dozvoljena_ucionica(dogadjaj, ucionica):
            continue

        broj += 1

    return broj


def sortiraj_dogadjaje(dogadjaji, ucionice=None, seed=0, rng=None):
    # Koristi se multistart greedy pristup.
    # Ne rasporedjujemo uvijek istim redoslijedom, jer jedan los greedy redoslijed
    # moze ostaviti validne dogadjaje nerasporedjene.
    if rng is None:
        rng = random.Random(seed)
    rezim = seed % 5

    def kljuc(d):
        treba_lab = 0
        if d.treba_lab == 1:
            treba_lab = 1

        lv_prioritet = 0
        if d.tip == "LV":
            lv_prioritet = 1

        opcije_ucionica = 99
        if ucionice is not None:
            opcije_ucionica = broj_mogucih_ucionica(d, ucionice)

        # D0091 je kritican dogadjaj jer ima 105 studenata i prakticno moze stati samo u ABG.
        # Ako dodje kasno, ABG se moze isfragmentirati tako da ostanu samo pojedinacni prazni sati.
        prisiljeni_prioritet = 0
        if d.dogadjaj_id == "D0091":
            prisiljeni_prioritet = 1

        # Dogadjaji koji imaju vrlo malo mogucih ucionica moraju ici sto ranije.
        # To posebno cuva velike ABG blokove od fragmentacije.
        ogranicenost_ucionica = 100 - opcije_ucionica

        if rezim == 0:
            osnovni = (prisiljeni_prioritet, ogranicenost_ucionica, d.trajanje_sati, d.broj_studenata, treba_lab, lv_prioritet)
        elif rezim == 1:
            osnovni = (prisiljeni_prioritet, ogranicenost_ucionica, d.broj_studenata, d.trajanje_sati, treba_lab, lv_prioritet)
        elif rezim == 2:
            osnovni = (prisiljeni_prioritet, d.trajanje_sati, ogranicenost_ucionica, d.broj_studenata, treba_lab, lv_prioritet)
        elif rezim == 3:
            osnovni = (prisiljeni_prioritet, treba_lab, d.trajanje_sati, ogranicenost_ucionica, d.broj_studenata, lv_prioritet)
        else:
            osnovni = (prisiljeni_prioritet, ogranicenost_ucionica, d.trajanje_sati, d.broj_studenata, treba_lab, lv_prioritet)

        # Mala deterministicka random komponenta razbija izjednacene prioritete.
        return (osnovni, rng.random())

    return sorted(dogadjaji, key=kljuc, reverse=True)


def sortiraj_ucionice(ucionice, dogadjaj):
    rezultat = []

    if dogadjaj.tip == "LV" and dogadjaj.predmet == "Programiranje I":
        for ucionica in ucionice:
            if ucionica.ucionica_id == "ABG":
                rezultat.append(ucionica)

    if dogadjaj.tip == "LV":
        labovi = []
        for ucionica in ucionice:
            if ucionica.lab == 1:
                labovi.append(ucionica)
        labovi = sorted(labovi, key=lambda u: u.kapacitet)
        for u in labovi:
            if u not in rezultat:
                rezultat.append(u)
        return rezultat

    obicne = []
    labovi = []

    for ucionica in ucionice:
        if ucionica.lab == 1:
            labovi.append(ucionica)
        else:
            obicne.append(ucionica)

    obicne = sorted(obicne, key=lambda u: u.kapacitet)
    labovi = sorted(labovi, key=lambda u: u.kapacitet)

    return obicne + labovi


def moguci_poceci(termini, trajanje_sati):
    po_danu = {}

    for termin in termini:
        if termin.dan not in po_danu:
            po_danu[termin.dan] = []
        po_danu[termin.dan].append(termin)

    poceci = []

    for dan in po_danu:
        lista = sorted(po_danu[dan], key=lambda t: t.slot)

        for termin in lista:
            if termin_staje_u_radno_vrijeme(termin.pocetak, trajanje_sati):
                poceci.append(termin)

    return poceci


def moze_staviti(dogadjaj, ucionica, termin, zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti, mapa_redovnih):
    if not termin_staje_u_radno_vrijeme(termin.pocetak, dogadjaj.trajanje_sati):
        return False

    if ucionica.kapacitet < dogadjaj.broj_studenata:
        return False

    if not lv_dozvoljena_ucionica(dogadjaj, ucionica):
        return False

    sati = satni_opseg(termin.pocetak, dogadjaj.trajanje_sati)

    if termin.dan == "CETVRTAK":
        redovni = mapa_redovnih.get(osoba_kljuc(dogadjaj.nastavnik), 0)
        if redovni == 1 and 13 in sati:
            return False

    for sat in sati:
        kljuc_nastavnik = (osoba_kljuc(dogadjaj.nastavnik), termin.dan, sat)
        kljuc_ucionica = (ucionica.ucionica_id, termin.dan, sat)

        if kljuc_nastavnik in zauzeti_nastavnici:
            return False

        if kljuc_ucionica in zauzete_ucionice:
            return False

        for student_kljuc in student_kljucevi(dogadjaj):
            kljuc_studenti_sat = (student_kljuc, termin.dan, sat)

            if kljuc_studenti_sat in zauzeti_studenti:
                return False

    return True


def oznaci_zauzeto(dogadjaj, ucionica, termin, zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti):
    sati = satni_opseg(termin.pocetak, dogadjaj.trajanje_sati)

    for sat in sati:
        zauzeti_nastavnici[(osoba_kljuc(dogadjaj.nastavnik), termin.dan, sat)] = dogadjaj.dogadjaj_id
        zauzete_ucionice[(ucionica.ucionica_id, termin.dan, sat)] = dogadjaj.dogadjaj_id

        for student_kljuc in student_kljucevi(dogadjaj):
            zauzeti_studenti[(student_kljuc, termin.dan, sat)] = dogadjaj.dogadjaj_id


def napravi_stavku(dogadjaj, ucionica, termin):
    return StavkaRasporeda(
        dogadjaj_id=dogadjaj.dogadjaj_id,
        predmet=dogadjaj.predmet,
        tip=dogadjaj.tip,
        nastavnik=dogadjaj.nastavnik,
        smjerovi=dogadjaj.smjerovi,
        ciklus=dogadjaj.ciklus,
        semestar=dogadjaj.semestar,
        godina=dogadjaj.godina,
        grupa=dogadjaj.grupa,
        broj_studenata=dogadjaj.broj_studenata,
        ucionica_id=ucionica.ucionica_id,
        dan=termin.dan,
        pocetak=termin.pocetak,
        kraj=str(sat_iz_teksta(termin.pocetak) + dogadjaj.trajanje_sati).zfill(2) + ":00",
        trajanje_sati=dogadjaj.trajanje_sati
    )


def poredaj_poceke_za_pokusaj(poceci, seed, rng):
    rezim = (seed // 5) % 5
    lista = list(poceci)

    if rezim == 0:
        return lista

    if rezim == 1:
        rng.shuffle(lista)
        return lista

    if rezim == 2:
        po_danu = {}
        for termin in lista:
            if termin.dan not in po_danu:
                po_danu[termin.dan] = []
            po_danu[termin.dan].append(termin)

        dani = list(po_danu.keys())
        rng.shuffle(dani)

        rezultat = []
        for dan in dani:
            rezultat += sorted(po_danu[dan], key=lambda t: t.slot)

        return rezultat

    if rezim == 3:
        return sorted(lista, key=lambda t: t.slot, reverse=True)

    return sorted(lista, key=lambda t: abs(t.slot - 5))


def napravi_greedy_raspored_za_pokusaj(dogadjaji, termini, ucionice, osoblje, seed):
    raspored = []
    nerasporedjeni = []

    zauzeti_nastavnici = {}
    zauzete_ucionice = {}
    zauzeti_studenti = {}
    mapa_redovnih = napravi_mapu_redovnih(osoblje)

    rng = random.Random(seed)
    dogadjaji_redoslijed = sortiraj_dogadjaje(dogadjaji, ucionice, seed, rng)

    for dogadjaj in dogadjaji_redoslijed:
        smjesten = False
        poceci = poredaj_poceke_za_pokusaj(
            moguci_poceci(termini, dogadjaj.trajanje_sati),
            seed,
            rng
        )
        moguce_ucionice = sortiraj_ucionice(ucionice, dogadjaj)

        for termin in poceci:
            if smjesten:
                break

            for ucionica in moguce_ucionice:
                if moze_staviti(dogadjaj, ucionica, termin, zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti, mapa_redovnih):
                    stavka = napravi_stavku(dogadjaj, ucionica, termin)
                    raspored.append(stavka)
                    oznaci_zauzeto(dogadjaj, ucionica, termin, zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti)
                    smjesten = True
                    break

        if not smjesten:
            nerasporedjeni.append(dogadjaj)

    return raspored, nerasporedjeni


def napravi_mape_zauzetosti_iz_rasporeda(raspored):
    zauzeti_nastavnici = {}
    zauzete_ucionice = {}
    zauzeti_studenti = {}

    for stavka in raspored:
        sati = satni_opseg(stavka.pocetak, stavka.trajanje_sati)

        for sat in sati:
            zauzeti_nastavnici[(osoba_kljuc(stavka.nastavnik), stavka.dan, sat)] = stavka.dogadjaj_id
            zauzete_ucionice[(stavka.ucionica_id, stavka.dan, sat)] = stavka.dogadjaj_id

            for student_kljuc in student_kljucevi(stavka):
                zauzeti_studenti[(student_kljuc, stavka.dan, sat)] = stavka.dogadjaj_id

    return zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti


def sati_se_preklapaju(pocetak_1, trajanje_1, pocetak_2, trajanje_2):
    sati_1 = set(satni_opseg(pocetak_1, trajanje_1))
    sati_2 = set(satni_opseg(pocetak_2, trajanje_2))
    return len(sati_1.intersection(sati_2)) > 0


def imaju_zajednicke_studente(a, b):
    kljucevi_a = set(student_kljucevi(a))
    kljucevi_b = set(student_kljucevi(b))
    return len(kljucevi_a.intersection(kljucevi_b)) > 0


def konfliktne_stavke_za_poziciju(dogadjaj, ucionica, termin, raspored, mapa_redovnih):
    if not termin_staje_u_radno_vrijeme(termin.pocetak, dogadjaj.trajanje_sati):
        return None

    if ucionica.kapacitet < dogadjaj.broj_studenata:
        return None

    if not lv_dozvoljena_ucionica(dogadjaj, ucionica):
        return None

    sati = satni_opseg(termin.pocetak, dogadjaj.trajanje_sati)

    if termin.dan == "CETVRTAK":
        redovni = mapa_redovnih.get(osoba_kljuc(dogadjaj.nastavnik), 0)
        if redovni == 1 and 13 in sati:
            return None

    konflikti = []

    for stavka in raspored:
        if stavka.dan != termin.dan:
            continue

        if not sati_se_preklapaju(termin.pocetak, dogadjaj.trajanje_sati, stavka.pocetak, stavka.trajanje_sati):
            continue

        isti_nastavnik = osoba_kljuc(stavka.nastavnik) == osoba_kljuc(dogadjaj.nastavnik)
        ista_ucionica = stavka.ucionica_id == ucionica.ucionica_id
        isti_studenti = imaju_zajednicke_studente(dogadjaj, stavka)

        if isti_nastavnik or ista_ucionica or isti_studenti:
            konflikti.append(stavka)

    return konflikti


def pokusaj_smjestiti_jedan(dogadjaj, raspored, termini, ucionice, osoblje, seed):
    mapa_redovnih = napravi_mapu_redovnih(osoblje)
    zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti = napravi_mape_zauzetosti_iz_rasporeda(raspored)
    rng = random.Random(seed)

    poceci = poredaj_poceke_za_pokusaj(
        moguci_poceci(termini, dogadjaj.trajanje_sati),
        seed,
        rng
    )

    for termin in poceci:
        for ucionica in sortiraj_ucionice(ucionice, dogadjaj):
            if moze_staviti(dogadjaj, ucionica, termin, zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti, mapa_redovnih):
                stavka = napravi_stavku(dogadjaj, ucionica, termin)
                raspored.append(stavka)
                oznaci_zauzeto(dogadjaj, ucionica, termin, zauzeti_nastavnici, zauzete_ucionice, zauzeti_studenti)
                return True

    return False


def pokusaj_popraviti_jednog_nerasporedjenog(dogadjaj, raspored, svi_dogadjaji, termini, ucionice, osoblje):
    # Ako greedy ostavi jedan validan dogadjaj nerasporedjen, pokusavamo napraviti
    # malu lokalnu popravku: ubacimo taj dogadjaj, privremeno izbacimo samo stavke
    # koje mu direktno smetaju, pa onda pokusamo ponovo smjestiti izbacene stavke.
    # Ovo sprjecava situaciju da veliki predmet kao Linearna algebra AV ostane vani
    # samo zato sto je raniji greedy izbor zauzeo jedini pogodan blok.
    dogadjaj_po_id = {}
    for d in svi_dogadjaji:
        dogadjaj_po_id[d.dogadjaj_id] = d

    mapa_redovnih = napravi_mapu_redovnih(osoblje)

    for seed in range(80):
        rng = random.Random(10000 + seed)
        poceci = poredaj_poceke_za_pokusaj(
            moguci_poceci(termini, dogadjaj.trajanje_sati),
            seed,
            rng
        )

        for termin in poceci:
            for ucionica in sortiraj_ucionice(ucionice, dogadjaj):
                konflikti = konfliktne_stavke_za_poziciju(
                    dogadjaj,
                    ucionica,
                    termin,
                    raspored,
                    mapa_redovnih
                )

                if konflikti is None:
                    continue

                # Ne zelimo previse nasilnu popravku. U praksi su dovoljna 1-4 konflikta.
                if len(konflikti) > 4:
                    continue

                konflikt_ids = set()
                for stavka in konflikti:
                    konflikt_ids.add(stavka.dogadjaj_id)

                novi_raspored = []
                for stavka in raspored:
                    if stavka.dogadjaj_id not in konflikt_ids:
                        novi_raspored.append(stavka)

                nova_stavka = napravi_stavku(dogadjaj, ucionica, termin)
                novi_raspored.append(nova_stavka)

                izbaceni_dogadjaji = []
                for stavka in konflikti:
                    if stavka.dogadjaj_id in dogadjaj_po_id:
                        izbaceni_dogadjaji.append(dogadjaj_po_id[stavka.dogadjaj_id])

                izbaceni_dogadjaji = sortiraj_dogadjaje(izbaceni_dogadjaji, ucionice, seed, rng)

                uspjelo = True
                for izbaceni in izbaceni_dogadjaji:
                    if not pokusaj_smjestiti_jedan(izbaceni, novi_raspored, termini, ucionice, osoblje, seed):
                        uspjelo = False
                        break

                if uspjelo:
                    return novi_raspored, True

    return raspored, False


def popravi_nerasporedjene(raspored, nerasporedjeni, dogadjaji, termini, ucionice, osoblje):
    popravljeni_raspored = list(raspored)
    preostali = list(nerasporedjeni)

    promjena = True
    while promjena and len(preostali) > 0:
        promjena = False
        novi_preostali = []

        for dogadjaj in preostali:
            smjesten_direktno = False
            for seed in range(20):
                if pokusaj_smjestiti_jedan(dogadjaj, popravljeni_raspored, termini, ucionice, osoblje, seed):
                    smjesten_direktno = True
                    promjena = True
                    break

            if smjesten_direktno:
                continue

            popravljeni, uspjelo = pokusaj_popraviti_jednog_nerasporedjenog(
                dogadjaj,
                popravljeni_raspored,
                dogadjaji,
                termini,
                ucionice,
                osoblje
            )

            if uspjelo:
                popravljeni_raspored = popravljeni
                promjena = True
            else:
                novi_preostali.append(dogadjaj)

        preostali = novi_preostali

    return popravljeni_raspored, preostali


def napravi_inicijalni_raspored(dogadjaji, termini, ucionice, osoblje):
    # Pokrecemo vise brzih greedy pokusaja i uzimamo onaj koji rasporedi najvise dogadjaja.
    # Nakon toga postoji i mala lokalna popravka za validne dogadjaje koje greedy
    # slucajno ostavi nerasporedjene.
    najbolji_raspored = []
    najbolji_nerasporedjeni = list(dogadjaji)

    broj_pokusaja = 100

    for seed in range(broj_pokusaja):
        raspored, nerasporedjeni = napravi_greedy_raspored_za_pokusaj(
            dogadjaji,
            termini,
            ucionice,
            osoblje,
            seed
        )

        if len(nerasporedjeni) < len(najbolji_nerasporedjeni):
            najbolji_raspored = raspored
            najbolji_nerasporedjeni = nerasporedjeni

        if len(najbolji_nerasporedjeni) == 0:
            break

    if len(najbolji_nerasporedjeni) > 0:
        najbolji_raspored, najbolji_nerasporedjeni = popravi_nerasporedjene(
            najbolji_raspored,
            najbolji_nerasporedjeni,
            dogadjaji,
            termini,
            ucionice,
            osoblje
        )

    return najbolji_raspored, najbolji_nerasporedjeni


def sacuvaj_raspored(raspored, putanja):
    putanja = Path(putanja)
    putanja.parent.mkdir(parents=True, exist_ok=True)

    kolone = [
        "dogadjaj_id",
        "predmet",
        "tip",
        "nastavnik",
        "smjerovi",
        "ciklus",
        "semestar",
        "godina",
        "grupa",
        "broj_studenata",
        "ucionica_id",
        "dan",
        "pocetak",
        "kraj",
        "trajanje_sati"
    ]

    with open(putanja, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(kolone)

        for s in raspored:
            writer.writerow([
                s.dogadjaj_id,
                s.predmet,
                s.tip,
                s.nastavnik,
                s.smjerovi,
                s.ciklus,
                s.semestar,
                s.godina,
                s.grupa,
                s.broj_studenata,
                s.ucionica_id,
                s.dan,
                s.pocetak,
                s.kraj,
                s.trajanje_sati
            ])


def sacuvaj_nerasporedjene(nerasporedjeni, putanja):
    putanja = Path(putanja)
    putanja.parent.mkdir(parents=True, exist_ok=True)

    kolone = [
        "dogadjaj_id",
        "predmet",
        "tip",
        "trajanje_sati",
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

        for d in nerasporedjeni:
            writer.writerow([
                d.dogadjaj_id,
                d.predmet,
                d.tip,
                d.trajanje_sati,
                d.nastavnik,
                d.smjerovi,
                d.ciklus,
                d.semestar,
                d.godina,
                d.broj_studenata,
                d.treba_lab,
                d.grupa
            ])
