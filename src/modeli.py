from dataclasses import dataclass


@dataclass
class Predmet:
    predmet: str
    smjer: str
    ciklus: str
    semestar: int
    p: int
    av: int
    lv: int
    tip: str


@dataclass
class Osoba:
    ime: str
    predmet: str
    tip: str
    redovni: int


@dataclass
class Ucionica:
    ucionica_id: str
    lab: int
    kapacitet: int


@dataclass
class StudentskaGrupa:
    smjer: str
    ciklus: str
    godina: str
    broj_studenata: int


@dataclass
class Termin:
    termin_id: str
    dan: str
    pocetak: str
    kraj: str
    trajanje_minuta: int
    slot: int


@dataclass
class Ogranicenje:
    tip: str
    oznaka: str
    opis: str


@dataclass
class NastavniDogadjaj:
    dogadjaj_id: str
    predmet: str
    tip: str
    trajanje_sati: int
    trajanje_minuta: int
    nastavnik: str
    smjerovi: str
    ciklus: str
    semestar: int
    godina: str
    broj_studenata: int
    treba_lab: int
    grupa: str


@dataclass
class StavkaRasporeda:
    dogadjaj_id: str
    predmet: str
    tip: str
    nastavnik: str
    smjerovi: str
    ciklus: str
    semestar: int
    godina: str
    grupa: str
    broj_studenata: int
    ucionica_id: str
    dan: str
    pocetak: str
    kraj: str
    trajanje_sati: int
