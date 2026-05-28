# Zajednicki parametri za pojedinacne algoritme i eksperimente.
#
# Ideja je da SA/ABC komande i eksperimenti koriste iste vrijednosti.
# Eksperimenti samo ponavljaju algoritam 30 puta, ne koriste posebne "jace" parametre.

BROJ_POKRETANJA_EKSPERIMENTA = 30

SA_BROJ_ITERACIJA = 600
SA_POCETNA_TEMPERATURA = 800.0
SA_HLADJENJE = 0.995

ABC_BROJ_CIKLUSA = 40
ABC_BROJ_IZVORA = 4
ABC_LIMIT = 10

# Nastava smije zavrsiti najkasnije u 19:00.
# Termin 19:00-20:00 se ne koristi.
NAJKASNIJI_KRAJ_NASTAVE = 19
