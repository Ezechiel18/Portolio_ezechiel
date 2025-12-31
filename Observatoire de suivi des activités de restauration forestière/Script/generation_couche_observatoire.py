import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
import random
from datetime import datetime, timedelta

# =========================
# PARAMÈTRES
# =========================
EPSG = 32631
NB_ZONES_PAR_SITE = 5
NB_LIGNES_CSV = 10  # nombre minimum de lignes par table CSV

# =========================
# 1. SITE À RESTAURER (EXISTANT)
# =========================
site = gpd.read_file(
    "sitearestaurer.gpkg",
    layer="sitearestaurer"
).to_crs(EPSG)

# =========================
# 2. COUCHE SIG : ZONEPLANTATION
# =========================
zones = []
zone_id = 1

for i, row in site.iterrows():
    minx, miny, maxx, maxy = row.geometry.bounds
    width = maxx - minx
    height = maxy - miny
    
    for j in range(NB_ZONES_PAR_SITE):
        zone_width = width * 0.2
        zone_height = height * 0.2
        offset_x = random.uniform(0, width - zone_width)
        offset_y = random.uniform(0, height - zone_height)
        
        poly = Polygon([
            (minx + offset_x, miny + offset_y),
            (minx + offset_x + zone_width, miny + offset_y),
            (minx + offset_x + zone_width, miny + offset_y + zone_height),
            (minx + offset_x, miny + offset_y + zone_height)
        ])
        
        poly = poly.intersection(row.geometry)
        
        if not poly.is_empty:
            zones.append({
                "idzone": zone_id,
                "nomzone": f"Zone_{zone_id}",
                "idsite": row.idsite,
                "geometry": poly
            })
            zone_id += 1

zoneplantation = gpd.GeoDataFrame(zones, crs=EPSG)
zoneplantation.to_file("zoneplantation.gpkg", layer="zoneplantation", driver="GPKG")

# =========================
# 3. TABLE TYPEACTIVITE
# =========================
typeactivite = pd.DataFrame([
    (i, f"Activite_{i}", random.choice(["Restauration", "Social", "Maintenance"]))
    for i in range(1, NB_LIGNES_CSV + 1)
], columns=["idtacti", "nom", "categorie"])
typeactivite.to_csv("typeactivite.csv", index=False)

# =========================
# 4. TABLE PLANTATION
# =========================
plantation = pd.DataFrame([
    (i, f"Plantation_{i}", random.randint(1, NB_LIGNES_CSV))
    for i in range(1, NB_LIGNES_CSV + 1)
], columns=["idplantation", "nomplantation", "idtacti"])
plantation.to_csv("plantation.csv", index=False)

# =========================
# 5. TABLE ENTRETIEN
# =========================
entretien = pd.DataFrame([
    (i, (datetime.today() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
     random.choice(["Arrosage", "Taille", "Fertilisation"]),
     random.randint(1, NB_LIGNES_CSV))
    for i in range(1, NB_LIGNES_CSV + 1)
], columns=["identretien", "dateentretien", "typeentretien", "idtacti"])
entretien.to_csv("entretien.csv", index=False)

# =========================
# 6. TABLE INDICATEUR
# =========================
indicateur = pd.DataFrame([
    (i, f"Indic_{i}", f"Description_{i}", "unité", 0, random.choice(["Quantitatif", "Qualitatif"]))
    for i in range(1, NB_LIGNES_CSV + 1)
], columns=["idindic", "nomindic", "descriptionindic", "uniteindic", "unite", "typeindic"])
indicateur.to_csv("indicateur.csv", index=False)

# =========================
# 7. TABLE CIBLE
# =========================
cible = pd.DataFrame([
    (i, random.randint(10, 10000), str(2026 + i % 3),
     random.randint(1, NB_LIGNES_CSV), random.randint(1, len(site)))
    for i in range(1, NB_LIGNES_CSV + 1)
], columns=["idcible", "valeur", "annee", "idindic", "idsite"])
cible.to_csv("cible.csv", index=False)

# =========================
# 8. TABLE BASELINE
# =========================
baseline = pd.DataFrame([
    (i, random.randint(0, 5000), (datetime.today() - timedelta(days=random.randint(365, 2000))).strftime("%Y-%m-%d"),
     random.randint(1, NB_LIGNES_CSV), random.randint(1, len(site)))
    for i in range(1, NB_LIGNES_CSV + 1)
], columns=["idbaseline", "valeur", "datereference", "idindic", "idsite"])
baseline.to_csv("baseline.csv", index=False)

# =========================
# 9. TABLE REALISATION
# =========================
realisation = pd.DataFrame([
    (i, (datetime.today() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
     random.randint(0, 10000), random.randint(1, len(zoneplantation)),
     random.randint(1, NB_LIGNES_CSV), random.randint(1, NB_LIGNES_CSV))
    for i in range(1, NB_LIGNES_CSV + 1)
], columns=["idrealisation", "daterealisation", "valeurealise", "idzone", "idindic", "idtacti"])
realisation.to_csv("realisation.csv", index=False)

# =========================
# 10. TABLE SENSIBILISATION
# =========================
sensibilisation = pd.DataFrame([
    (i, random.randint(10, 200), random.choice(["Satisfaisant", "Moyen", "Insuffisant"]),
     random.randint(1, 20), random.randint(1, NB_LIGNES_CSV))
    for i in range(1, NB_LIGNES_CSV + 1)
], columns=["idsens", "nbparticipant", "satisfaction", "idlocalite", "idtacti"])
sensibilisation.to_csv("sensibilisation.csv", index=False)

# =========================
# 11. TABLE EFFECTUER
# =========================
effectuer = pd.DataFrame([
    (i, random.randint(1, NB_LIGNES_CSV), random.choice(["Exécutant", "Superviseur"]))
    for i in range(1, NB_LIGNES_CSV + 1)
], columns=["idacteur", "idrealisation", "role"])
effectuer.to_csv("effectuer.csv", index=False)

# =========================
# 12. TABLE SE_TROUVER
# =========================
se_trouver = pd.DataFrame([
    (i, random.randint(1, 10))
    for i in range(1, NB_LIGNES_CSV + 1)
], columns=["idlocalite", "idap"])
se_trouver.to_csv("se_trouver.csv", index=False)

# =========================
# 13. TABLE UTILISER
# =========================
utiliser = pd.DataFrame([
    (random.randint(1, NB_LIGNES_CSV), random.randint(1, NB_LIGNES_CSV), random.randint(100, 1000))
    for i in range(NB_LIGNES_CSV)
], columns=["idplantation", "idespece", "quantite"])
utiliser.to_csv("utiliser.csv", index=False)

# =========================
# 14. TABLE RATTACHER
# =========================
rattacher = pd.DataFrame([
    (random.randint(1, len(site)), random.randint(1, 20))
    for i in range(NB_LIGNES_CSV)
], columns=["idsite", "idlocalite"])
rattacher.to_csv("rattacher.csv", index=False)

print(f"✅ Tous les fichiers ont été générés avec au moins {NB_LIGNES_CSV} lignes chacun")



#### Garder que les polygones qui ne chevauchent pas déjà un autre polygone
import geopandas as gpd

# Lire le fichier existant
zoneplantation = gpd.read_file("zoneplantation.gpkg", layer="zoneplantation")

# Liste pour stocker les polygones sans chevauchement
selected = []

for idx, row in zoneplantation.iterrows():
    # vérifier si ce polygone intersecte un polygone déjà sélectionné
    if not any(row.geometry.intersects(r.geometry) for r in selected):
        selected.append(row)

# Créer un GeoDataFrame à partir des lignes sélectionnées
zoneplantation_no_overlap = gpd.GeoDataFrame(selected, crs=zoneplantation.crs)

# Enregistrer le résultat
zoneplantation_no_overlap.to_file("zoneplantation_no_overlap.gpkg", layer="zoneplantation", driver="GPKG")

print(f"✅ {len(zoneplantation_no_overlap)} polygones sans chevauchement avec attributs conservés")
