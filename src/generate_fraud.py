"""Génère transactions.csv et labels.csv : données synthétiques de fraude bancaire."""

import csv
import random
from datetime import datetime, timedelta

# Graine fixe pour obtenir les mêmes données à chaque exécution
random.seed(23)

N_CARDS = 2000
N_TX = 36000

cats = [
    "alimentation",
    "carburant",
    "restaurant",
    "vetements",
    "high-tech",
    "voyage",
    "sante"
]

foreign = ["ES", "IT", "DE", "GB", "US", "MA"]
start = datetime(2025, 9, 1)

# Montant médian de référence pour chaque carte
median = {
    c: random.choice([18, 25, 35, 50, 70])
    for c in range(1, N_CARDS + 1)
}

tx = []
tid = 0


def add(card, ts, country, amount, cat=None, channel=None, fraud=""):
    global tid

    tid += 1

    tx.append({
        "tx_id": tid,
        "card_id": card,
        "ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "merchant_cat": cat or random.choice(cats),
        "country": country,
        "amount": round(amount, 2),
        "channel": channel or random.choices(
            ["magasin", "en_ligne"],
            [75, 25]
        )[0],
        "fraud": fraud
    })


# 1. Génération des transactions légitimes
for _ in range(N_TX):
    c = random.randint(1, N_CARDS)

    ts = start + timedelta(
        seconds=random.randint(0, 30 * 86400)
    )

    amt = random.lognormvariate(0, 0.5) * median[c]

    country = "FR" if random.random() < 0.94 else random.choice(foreign)

    # Achats exceptionnels mais légitimes
    if random.random() < 0.004:
        amt *= random.uniform(6, 12)

    add(c, ts, country, amt)


# 2. Génération des fraudes par rafale
# 60 séries de 6 achats en ligne en moins de 8 minutes
for _ in range(60):
    c = random.randint(1, N_CARDS)

    t0 = start + timedelta(
        seconds=random.randint(0, 29 * 86400)
    )

    for k in range(6):
        add(
            c,
            t0 + timedelta(seconds=k * random.randint(40, 90)),
            "FR",
            random.uniform(5, 40),
            "high-tech",
            "en_ligne",
            "rafale"
        )


# 3. Génération des fraudes par voyage impossible
# Achat en France puis à l'étranger 20 minutes plus tard
for _ in range(40):
    c = random.randint(1, N_CARDS)

    t0 = start + timedelta(
        seconds=random.randint(0, 29 * 86400)
    )

    add(
        c,
        t0,
        "FR",
        random.lognormvariate(0, 0.4) * median[c]
    )

    add(
        c,
        t0 + timedelta(minutes=20),
        random.choice(foreign),
        random.uniform(80, 300),
        "voyage",
        "en_ligne",
        "voyage_impossible"
    )


# 4. Génération des fraudes par montant anormal
for _ in range(80):
    c = random.randint(1, N_CARDS)

    t0 = start + timedelta(
        seconds=random.randint(0, 29 * 86400)
    )

    add(
        c,
        t0,
        "FR",
        median[c] * random.uniform(10, 25),
        "high-tech",
        "en_ligne",
        "montant_anormal"
    )


# 5. Création de la vérité terrain
labels = [
    {
        "tx_id": r["tx_id"],
        "fraud_type": r["fraud"]
    }
    for r in tx
    if r["fraud"]
]


# On retire l'information de fraude des transactions
for r in tx:
    del r["fraud"]


# 6. Injection de défauts de qualité
# 80 montants manquants
for r in random.sample(tx, 80):
    r["amount"] = ""

# 200 codes pays en minuscules
for r in random.sample(tx, 200):
    r["country"] = r["country"].lower()

# 150 doublons
tx += random.sample(tx, 150)

# Mélange des transactions
random.shuffle(tx)


# 7. Écriture des fichiers CSV
with open("transactions.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(tx[0]))
    writer.writeheader()
    writer.writerows(tx)

with open("labels.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["tx_id", "fraud_type"]
    )
    writer.writeheader()
    writer.writerows(labels)


print(len(tx), "transactions,", len(labels), "fraudes")
print("Fichiers transactions.csv et labels.csv générés avec succès.")
