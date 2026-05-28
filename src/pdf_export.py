import csv
import unicodedata
from pathlib import Path

from parametri import NAJKASNIJI_KRAJ_NASTAVE
from fitness import izracunaj_fitness
from parser import ucitaj_raspored
from parser import sat_iz_teksta
from hard_constraints import smjerovi_lista

DANI = ["PONEDJELJAK", "UTORAK", "SRIJEDA", "CETVRTAK", "PETAK"]
DANI_PRIKAZ = ["PONEDJELJAK", "UTORAK", "SRIJEDA", "CETVRTAK", "PETAK"]
SATI = list(range(8, NAJKASNIJI_KRAJ_NASTAVE))


def ascii_tekst(tekst):
    tekst = str(tekst)
    tekst = unicodedata.normalize("NFKD", tekst)
    tekst = tekst.encode("ascii", "ignore").decode("ascii")
    return tekst


def nadji_grupe(raspored):
    # Jedan PDF raspored treba predstavljati cijeli smjer/semestar,
    # a ne odvojeno G1 i G2. Zato grupa vise nije dio kljuca.
    grupe = {}

    for stavka in raspored:
        for smjer in smjerovi_lista(stavka.smjerovi):
            kljuc = (smjer, stavka.ciklus, stavka.godina, stavka.semestar)
            grupe[kljuc] = True

    rezultat = list(grupe.keys())
    rezultat.sort(key=lambda x: (x[0], x[1], x[3]))
    return rezultat


def stavka_pripada_grupi(stavka, grupa):
    smjer, ciklus, godina, semestar = grupa

    if ciklus != stavka.ciklus:
        return False
    if godina != stavka.godina:
        return False
    if int(semestar) != int(stavka.semestar):
        return False
    if smjer not in smjerovi_lista(stavka.smjerovi):
        return False

    # LV zadrzava oznaku G1/G2 u tekstu celije, ali vise ne pravi
    # poseban raspored po grupi. Jedna stranica sada prikazuje obje grupe.
    return True


def normalizuj_trajanje(stavka):
    trajanje = int(stavka.trajanje_sati)
    if trajanje < 1:
        return 1
    return trajanje


def vrijeme_prikaz(sat):
    pocetak = str(sat).zfill(2) + ":15"
    kraj = str(sat + 1).zfill(2) + ":00"
    return pocetak + " - " + kraj


def naziv_tipa(stavka):
    if stavka.tip == "P":
        return "P"
    if stavka.tip == "AV":
        return "AV"
    if stavka.tip == "LV":
        return "LV " + stavka.grupa
    return stavka.tip


def tekst_stavke(stavka):
    # Format slican zvanicnim rasporedima:
    # Predmet
    # (P/AV/LV G1)
    # Ucionica
    return ascii_tekst(
        stavka.predmet + "\n" +
        "(" + naziv_tipa(stavka) + ")\n" +
        stavka.ucionica_id
    )


def napravi_tabelu_za_grupu(raspored, grupa):
    podaci = [["SATNICA"] + DANI_PRIKAZ]

    for sat in SATI:
        red = [vrijeme_prikaz(sat)]
        for dan in DANI:
            red.append("")
        podaci.append(red)

    # Celije se prvo grupisu po pocetnom satu i danu. Tako jedna celija moze
    # prikazati npr. LV G1 i LV G2, ali i dalje ostaje u jednom rasporedu.
    celije = {}

    for stavka in raspored:
        if not stavka_pripada_grupi(stavka, grupa):
            continue

        sat = sat_iz_teksta(stavka.pocetak)
        if sat not in SATI:
            continue
        if stavka.dan not in DANI:
            continue

        red = SATI.index(sat) + 1
        kolona = DANI.index(stavka.dan) + 1
        kljuc = (red, kolona)

        if kljuc not in celije:
            celije[kljuc] = {
                "stavke": [],
                "trajanje": 1
            }

        celije[kljuc]["stavke"].append(stavka)
        trajanje = normalizuj_trajanje(stavka)
        if trajanje > celije[kljuc]["trajanje"]:
            celije[kljuc]["trajanje"] = trajanje

    spanovi = []
    zauzete_span_celije = {}

    for kljuc in sorted(celije.keys()):
        red, kolona = kljuc
        podatak = celije[kljuc]

        tekstovi = []
        for stavka in sorted(podatak["stavke"], key=lambda s: (s.tip, s.grupa, s.predmet)):
            tekstovi.append(tekst_stavke(stavka))

        trajanje = podatak["trajanje"]
        zadnji_red = min(red + trajanje - 1, len(podaci) - 1)

        # Ako su dvije grupe nekad preklopljene u istoj koloni, ne pravimo
        # nevalidne preklopljene SPAN-ove. Tekst ubacimo u pocetnu celiju
        # prvog bloka koji vec pokriva taj termin.
        if (red, kolona) in zauzete_span_celije:
            pocetni_red = zauzete_span_celije[(red, kolona)]
            if podaci[pocetni_red][kolona] == "":
                podaci[pocetni_red][kolona] = "\n---\n".join(tekstovi)
            else:
                podaci[pocetni_red][kolona] = podaci[pocetni_red][kolona] + "\n---\n" + "\n---\n".join(tekstovi)
            continue

        podaci[red][kolona] = "\n---\n".join(tekstovi)

        if zadnji_red > red:
            spanovi.append((kolona, red, kolona, zadnji_red))
            for pokriveni_red in range(red, zadnji_red + 1):
                zauzete_span_celije[(pokriveni_red, kolona)] = red

    return podaci, spanovi


def napravi_naslov_grupe(grupa):
    smjer, ciklus, godina, semestar = grupa
    return ascii_tekst(
        "Raspored - " + smjer +
        " | " + ciklus +
        " | " + godina +
        " | semestar " + str(semestar) +
        " | G1 i G2"
    )


def dodaj_stranicu_rasporeda(elementi, raspored, grupa, dodaj_page_break):
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, PageBreak
    except Exception as e:
        raise RuntimeError("ReportLab nije instaliran. Pokreni: pip install reportlab") from e

    if dodaj_page_break:
        elementi.append(PageBreak())

    styles = getSampleStyleSheet()
    naslov_style = ParagraphStyle(
        "NaslovRasporeda",
        parent=styles["Heading2"],
        fontName="Times-Bold",
        fontSize=12,
        leading=14,
        alignment=1,
        spaceAfter=8
    )

    elementi.append(Paragraph(napravi_naslov_grupe(grupa), naslov_style))
    elementi.append(Spacer(1, 4))

    podaci, spanovi = napravi_tabelu_za_grupu(raspored, grupa)

    sirine = [92, 128, 128, 128, 128, 128]
    visine = [18] + [39 for _ in SATI]

    tabela = Table(
        podaci,
        colWidths=sirine,
        rowHeights=visine,
        repeatRows=1
    )

    stil = [
        ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
        ("BOX", (0, 0), (-1, -1), 1.4, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Times-Bold"),
        ("FONTNAME", (1, 1), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),
        ("FONTSIZE", (0, 1), (0, -1), 10),
        ("FONTSIZE", (1, 1), (-1, -1), 8),
        ("LEADING", (1, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]

    for kol1, red1, kol2, red2 in spanovi:
        stil.append(("SPAN", (kol1, red1), (kol2, red2)))

    tabela.setStyle(TableStyle(stil))
    elementi.append(tabela)


def napravi_jedan_pdf_za_sve_grupe(raspored, grupe, putanja):
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate
    except Exception as e:
        raise RuntimeError("ReportLab nije instaliran. Pokreni: pip install reportlab") from e

    putanja = Path(putanja)
    putanja.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(putanja),
        pagesize=landscape(A4),
        rightMargin=28,
        leftMargin=28,
        topMargin=24,
        bottomMargin=24
    )

    elementi = []
    for i, grupa in enumerate(grupe):
        dodaj_stranicu_rasporeda(
            elementi,
            raspored,
            grupa,
            dodaj_page_break=(i > 0)
        )

    doc.build(elementi)


def izaberi_najbolji_raspored(processed_dir, dogadjaji, ucionice, osoblje):
    processed_dir = Path(processed_dir)
    kandidati = [
        ("eksperimenti_najbolji_sa", processed_dir / "eksperimenti_najbolji_sa_raspored.csv"),
        ("eksperimenti_najbolji_abc", processed_dir / "eksperimenti_najbolji_abc_raspored.csv"),
        ("sa", processed_dir / "sa_raspored.csv"),
        ("abc", processed_dir / "abc_raspored.csv"),
        ("inicijalni", processed_dir / "inicijalni_raspored.csv"),
    ]

    najbolji_naziv = None
    najbolji_raspored = None
    najbolji_fitness = None

    for naziv, putanja in kandidati:
        if not putanja.exists():
            continue
        raspored = ucitaj_raspored(putanja)
        fitness, _, _ = izracunaj_fitness(raspored, dogadjaji, ucionice, osoblje)
        if najbolji_fitness is None or fitness < najbolji_fitness:
            najbolji_fitness = fitness
            najbolji_naziv = naziv
            najbolji_raspored = raspored

    return najbolji_naziv, najbolji_raspored, najbolji_fitness


def exportuj_pdf_rasporede(raspored, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    grupe = nadji_grupe(raspored)
    pdf_putanja = output_dir / "svi_rasporedi.pdf"
    napravi_jedan_pdf_za_sve_grupe(raspored, grupe, pdf_putanja)

    redovi_index = []
    for grupa in grupe:
        smjer, ciklus, godina, semestar = grupa
        redovi_index.append({
            "smjer": smjer,
            "ciklus": ciklus,
            "godina": godina,
            "semestar": semestar,
            "grupe": "G1 i G2",
            "pdf": str(pdf_putanja)
        })

    index_putanja = output_dir / "rasporedi_index.csv"
    with open(index_putanja, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["smjer", "ciklus", "godina", "semestar", "grupe", "pdf"])
        writer.writeheader()
        for red in redovi_index:
            writer.writerow(red)

    return redovi_index, pdf_putanja
