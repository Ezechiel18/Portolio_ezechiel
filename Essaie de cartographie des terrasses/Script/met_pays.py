# =========================
# SCRIPT PYQGIS - TERRASSES
# =========================
# Auteur : Ezéchiel
# But : Identifier les patchs de pente faible propices aux terrasses
# Version : 1.1 (compatible QGIS 3.4)
# =========================

import processing

# =========================
# 1. PARAMÈTRES
# =========================

WORKDIR = "H:/M2_Avignon/Cours/Atelier_pro/SIG_2/data"

MNT = WORKDIR + "/entre/pentemethamis.tif"

PENTE_FAIBLE_MAX = 15
PENTE_FORTE_MIN = 25

BUFFER_DISTANCE = 20
DENSITE_RAYON = 10
SURFACE_MIN = 5

# =========================
# 2. CALCUL DE LA PENTE
# =========================

pente = processing.run(
    "gdal:slope",
    {
        'INPUT': MNT,
        'BAND': 1,
        'SCALE': 1,
        'AS_PERCENT': False,
        'COMPUTE_EDGES': True,
        'ZEVENBERGEN': False,
        'OUTPUT': WORKDIR + "/sortie/pente_deg_meth3.tif"
    }
)['OUTPUT']

# =========================
# 3. RECLASSIFICATION DES PENTES (RASTER CALCULATOR)
# =========================

# --- PENTES FAIBLES ---
pente_faible = processing.run(
    "qgis:rastercalculator",
    {
        'EXPRESSION': f'("{pente}@1" <= {PENTE_FAIBLE_MAX}) * 1',
        'LAYERS': [pente],
        'OUTPUT': WORKDIR + "/sortie/pente_faible_meth3.tif"
    }
)['OUTPUT']

# --- PENTES FORTES ---
pente_forte = processing.run(
    "qgis:rastercalculator",
    {
        'EXPRESSION': f'("{pente}@1" >= {PENTE_FORTE_MIN}) * 1',
        'LAYERS': [pente],
        'OUTPUT': WORKDIR + "/sortie/pente_forte_meth3.tif"
    }
)['OUTPUT']

# =========================
# 4. VECTORISATION DES PENTES FAIBLES
# =========================

patchs_faibles = processing.run(
    "gdal:polygonize",
    {
        'INPUT': pente_faible,
        'BAND': 1,
        'FIELD': 'value',
        'OUTPUT': WORKDIR + "/sortie/patchs_pente_faible_meth3.gpkg"
    }
)['OUTPUT']

# =========================
# 5. SUPPRESSION DES MICRO-PATCHS
# =========================

# =========================
# 5A. EXTRACTION DES PENTES FAIBLES UNIQUEMENT (value = 1)
# =========================
# On élimine les polygones "value = 0"
# pour ne garder QUE les vraies pentes faibles

patchs_faibles_only = processing.run(
    "native:extractbyexpression",
    {
        'INPUT': patchs_faibles,
        'EXPRESSION': '"value" = 1',
        'OUTPUT': WORKDIR + "/sortie/patchs_pente_faible_only_meth3.gpkg"
    }
)['OUTPUT']

# =========================
# 5B. REPRPOJECTION DE LA COUCHE pentfaible only
# =========================
patchs_faible_proj = processing.run(
    "native:reprojectlayer",
    {
        'INPUT': patchs_faibles_only,
        'TARGET_CRS': 'EPSG:2154',  # Lambert-93 (France, mètres)
        'OUTPUT': WORKDIR + "/sortie/patchs_faible_proj_meth3.gpkg"
    }
)['OUTPUT']

# =========================
# 5C. SUPPRESSION DES MICRO-PATCHS (SUR PENTES FAIBLES SEULEMENT)
# =========================

patchs_faibles_net = processing.run(
    "native:extractbyexpression",
    {
        'INPUT': patchs_faible_proj,   # 
        'EXPRESSION': f"$area >= {SURFACE_MIN}",
        'OUTPUT': WORKDIR + "/sortie/patchs_pente_faible_net_meth3.gpkg"
    }
)['OUTPUT']


# =========================
# 6 A. VECTORISATION DES PENTES FORTES
# =========================

pente_forte_vect = processing.run(
    "gdal:polygonize",
    {
        'INPUT': pente_forte,
        'BAND': 1,
        'FIELD': 'value',
        'OUTPUT': WORKDIR + "/sortie/pente_forte_meth3.gpkg"
    }
)['OUTPUT']

# 6B. EXTRACTION DES PENTES FORTES UNIQUEMENT (value = 1)
# =========================
# On élimine les polygones "value = 0"
# pour ne garder QUE les vraies pentes fortes

patchs_forte_only = processing.run(
    "native:extractbyexpression",
    {
        'INPUT': pente_forte_vect,
        'EXPRESSION': '"value" = 1',
        'OUTPUT': WORKDIR + "/sortie/patchs_pente_forte_only_meth3.gpkg"
    }
)['OUTPUT']

# 6C. REPROJECTION DE LA COUCHE penteforte only
# =========================
patchs_fort_proj = processing.run(
    "native:reprojectlayer",
    {
        'INPUT': patchs_forte_only,
        'TARGET_CRS': 'EPSG:2154',  # Lambert-93 (France, mètres)
        'OUTPUT': WORKDIR + "/sortie/patchs_fort_proj_meth3.gpkg"
    }
)['OUTPUT']
# =========================
# 7. BUFFER AUTOUR DES PENTES FORTES
# =========================

buffer_forte = processing.run(
    "native:buffer",
    {
        'INPUT': patchs_fort_proj,
        'DISTANCE': BUFFER_DISTANCE,
        'DISSOLVE': True,
        'OUTPUT': WORKDIR + "/sortie/buffer_pente_forte_meth3.gpkg"
    }
)['OUTPUT']

# =========================
# 8. PATCHS FAIBLES PROCHES DES PENTES FORTES
# =========================

patchs_proches = processing.run(
    "native:extractbylocation",
    {
        'INPUT': patchs_faibles_net,
        'PREDICATE': [0],  # intersect
        'INTERSECT': buffer_forte,
        'OUTPUT': WORKDIR + "/sortie/patchs_pente_faible_proches_meth3.gpkg"
    }
)['OUTPUT']

# =========================
# =========================
# =========================
# 9. DENSITÉ LOCALE DES PENTES FORTES (QGIS 3.4)
# =========================
# Calcul de la moyenne locale des pixels "pente forte"
# Fenêtre mobile centrée sur chaque pixel

# Estimation de la taille de la fenêtre (en pixels)
taille = int((DENSITE_RAYON * 2) / 0.5)  # ~ résolution 0.5 m

# La taille DOIT être impaire (obligation mathématique)
if taille % 2 == 0:
    taille += 1

densite = processing.run(
    "grass7:r.neighbors",
    {
        'input': pente_forte,
        'method': 0,   # 0 = average (moyenne)
        'size': taille,
        'output': WORKDIR + "/sortie/densite_pente_forte_meth3.tif",
        'GRASS_REGION_PARAMETER': None,
        'GRASS_REGION_CELLSIZE_PARAMETER': 0,
        'GRASS_RASTER_FORMAT_OPT': '',
        'GRASS_RASTER_FORMAT_META': ''
    }
)['output']



# =========================
# 10. STATISTIQUES ZONALES
# =========================

processing.run(
    "qgis:zonalstatistics",
    {
        'INPUT_VECTOR': patchs_proches,
        'INPUT_RASTER': densite,
        'RASTER_BAND': 1,
        'COLUMN_PREFIX': 'dens_'
    }
)

# 11. SÉLECTION DES PATCHS AVEC 0.3 ≤ dens_mean ≤ 0.6
# =========================

patchs_optimaux = processing.run(
    "native:extractbyexpression",
    {
        'INPUT': patchs_proches,
        'EXPRESSION': '"dens_mean" >= 0.3 AND "dens_mean" <= 0.6',
        'OUTPUT': WORKDIR + "/sortie/patchs_terrasses_optimaux_meth3.gpkg"
    }
)['OUTPUT']

# =========================
# FIN DU SCRIPT
# =========================

print("✅ Script terminé sans erreur.")
print("➡ Résultat final :")
print(WORKDIR + "/sortie/patchs_terrasses_optimaux_meth3.gpkg")