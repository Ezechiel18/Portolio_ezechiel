# =============================================================================
#  quality_spatiale.py — Contrôles de qualité topologique — V9
#
#  CORRECTIONS V9 :
#    - verifier_noeuds_milieu_troncon : logique mutuellement exclusive
#      Chaque nœud appartient à UNE SEULE catégorie :
#        1. Raccordé     : proche d'une extrémité
#        2. Au milieu    : proche d'un tronçon mais pas d'une extrémité
#        3. Non raccordé : loin de tout
#      Méthode : distance géométrique réelle au lieu de buffer fixe
#
#  RAPPEL V8 :
#    - Gestion MultiLineString
#    - Jointures spatiales vectorisées (performance)
#    - Reprojection systématique en EPSG:2154
# =============================================================================

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import SNAP_TOLERANCE
from analysis.quality_attributaire import arrondi_pct


def _get_sous_lignes(geom):
    """
    Retourne la liste des sous-lignes d'une géométrie.
    - LineString      → [geom]
    - MultiLineString → liste de toutes les lignes composantes
    - Autre           → [] (ignoré)
    """
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "LineString":
        return [geom]
    elif geom.geom_type == "MultiLineString":
        return list(geom.geoms)
    return []


def _extraire_extremites(gdf_troncons):
    """
    Extrait les extrémités de chaque tronçon sous forme de points.
    Pour un MultiLineString : ext1 = début de la 1ère sous-ligne,
                              ext2 = fin de la dernière sous-ligne.
    Retourne un GeoDataFrame avec colonnes : troncon_idx, ext, geometry.
    """
    lignes = []
    for idx, row in gdf_troncons.iterrows():
        sous_lignes = _get_sous_lignes(row.geometry)
        if not sous_lignes:
            continue
        coords_debut = list(sous_lignes[0].coords)
        coords_fin   = list(sous_lignes[-1].coords)
        lignes.append({"troncon_idx": idx, "ext": "ext1",
                        "geometry": Point(coords_debut[0])})
        lignes.append({"troncon_idx": idx, "ext": "ext2",
                        "geometry": Point(coords_fin[-1])})

    if not lignes:
        return gpd.GeoDataFrame(
            columns=["troncon_idx", "ext", "geometry"],
            crs=gdf_troncons.crs)
    return gpd.GeoDataFrame(lignes, crs=gdf_troncons.crs)


def verifier_noeuds_connectes(gdf_noeuds, gdf_troncons, tolerance=SNAP_TOLERANCE):
    """
    Vérifie si chaque nœud est raccordé à au moins un tronçon.
    Méthode : jointure spatiale vectorisée entre nœuds tamponnés
    et extrémités de tronçons.
    Ajoute "connecte" = "oui"/"non" dans la couche nœuds.
    """
    extremites = _extraire_extremites(gdf_troncons)
    gdf_noeuds = gdf_noeuds.copy()

    if extremites.empty:
        gdf_noeuds["connecte"] = "non"
        return gdf_noeuds

    noeuds_buf = gdf_noeuds.copy()
    noeuds_buf["geometry"] = noeuds_buf.geometry.buffer(tolerance)

    jointure = gpd.sjoin(
        noeuds_buf,
        extremites[["geometry"]],
        how="left",
        predicate="intersects"
    )
    connectes = set(jointure[jointure["index_right"].notna()].index)

    gdf_noeuds["connecte"] = gdf_noeuds.index.map(
        lambda i: "oui" if i in connectes else "non"
    )
    return gdf_noeuds


def verifier_noeuds_milieu_troncon(gdf_noeuds, gdf_troncons, tolerance=SNAP_TOLERANCE):
    """
    Détecte les nœuds au milieu d'un tronçon avec catégories MUTUELLEMENT EXCLUSIVES.

    Chaque nœud appartient à UNE SEULE catégorie :

      1. Raccordé (connecte = "oui")
         → distance à une extrémité < tolerance
         → au_milieu_troncon = "non"
         → déjà traité par verifier_noeuds_connectes avant cet appel

      2. Au milieu (au_milieu_troncon = "oui")
         → connecte = "non" (pas aux extrémités)
         → distance au tronçon (géométrie complète) < tolerance
         → le nœud colle à un tronçon en son milieu

      3. Non raccordé (connecte = "non", au_milieu_troncon = "non")
         → distance aux extrémités > tolerance
         → distance au tronçon > tolerance
         → nœud isolé du réseau

    IMPORTANT : cette fonction est appelée APRÈS verifier_noeuds_connectes.
    Elle ne traite que les nœuds avec connecte = "non".

    Méthode :
      - Calcul de la distance géométrique réelle nœud → union des tronçons
      - Plus précis qu'un buffer fixe (mesure l'écart exact)
      - Tolérance = SNAP_TOLERANCE = 0.5 m
    """
    gdf_noeuds = gdf_noeuds.copy()
    # Initialiser le champ pour tous les nœuds
    gdf_noeuds["au_milieu_troncon"] = "non"

    # Ne traiter que les nœuds NON raccordés
    # Les nœuds raccordés sont déjà aux extrémités — ils ne peuvent pas être au milieu
    non_raccordes = gdf_noeuds[gdf_noeuds["connecte"] == "non"]

    if non_raccordes.empty:
        # Tous les nœuds sont raccordés — rien à faire
        return gdf_noeuds, 0

    # Créer l'union géométrique de tous les tronçons
    # Permet de calculer la distance en une seule opération par nœud
    # plutôt que de comparer avec chaque tronçon individuellement
    try:
        troncons_union = gdf_troncons.geometry.unary_union
    except Exception as e:
        print(f"  [AVERTISSEMENT] Calcul milieu tronçon impossible : {e}")
        return gdf_noeuds, 0

    indices_milieu = []

    for idx, row in non_raccordes.iterrows():
        # Distance réelle du nœud à la géométrie la plus proche
        # distance = 0 si le nœud est exactement sur un tronçon
        # distance > 0 si le nœud est à côté
        dist = row.geometry.distance(troncons_union)

        if dist < tolerance:
            # Nœud proche d'un tronçon mais pas à ses extrémités
            # → il est au milieu d'un tronçon
            indices_milieu.append(idx)

    # Mettre à jour uniquement les nœuds au milieu
    if indices_milieu:
        gdf_noeuds.loc[indices_milieu, "au_milieu_troncon"] = "oui"

    return gdf_noeuds, len(indices_milieu)


def verifier_delimitation_troncons(gdf_troncons, gdf_noeuds, tolerance=SNAP_TOLERANCE):
    """
    Vérifie si les deux extrémités de chaque tronçon sont proches d'un nœud.
    Méthode : jointure spatiale vectorisée — rapide sur grands volumes.

    Ajoute : borde_ext1, borde_ext2, statut_delimitation
    """
    extremites = _extraire_extremites(gdf_troncons)

    noeuds_buf = gdf_noeuds.copy()
    noeuds_buf["geometry"] = noeuds_buf.geometry.buffer(tolerance)

    jointure = gpd.sjoin(
        extremites,
        noeuds_buf[["geometry"]],
        how="left",
        predicate="within"
    )

    reliees = jointure[jointure["index_right"].notna()]
    paires_reliees = set(zip(reliees["troncon_idx"], reliees["ext"]))

    resultat = gdf_troncons.copy()
    resultat["borde_ext1"] = "non"
    resultat["borde_ext2"] = "non"

    for troncon_idx, ext in paires_reliees:
        if ext == "ext1":
            resultat.at[troncon_idx, "borde_ext1"] = "oui"
        else:
            resultat.at[troncon_idx, "borde_ext2"] = "oui"

    def statut(row):
        if row["borde_ext1"] == "oui" and row["borde_ext2"] == "oui":
            return "deux_cotes"
        elif row["borde_ext1"] == "oui" or row["borde_ext2"] == "oui":
            return "un_cote_seul"
        return "non_delimite"

    resultat["statut_delimitation"] = resultat.apply(statut, axis=1)
    return resultat


def run_quality_spatiale(gdf_troncons, gdf_noeuds):
    """
    Point d'entrée principal des contrôles topologiques.
    """
    # --- Gestion du CRS ---
    if gdf_troncons.crs is None:
        print("  [AVERTISSEMENT] Tronçon : CRS absent — contrôles potentiellement incorrects")
    else:
        gdf_troncons = gdf_troncons.to_crs(epsg=2154)

    if gdf_noeuds.crs is None:
        print("  [AVERTISSEMENT] Nœud : CRS absent — contrôles potentiellement incorrects")
    else:
        gdf_noeuds = gdf_noeuds.to_crs(epsg=2154)

    # --- 1. Connectivité des nœuds ---
    print("    Raccordement des nœuds ...")
    noeuds_enrichis = verifier_noeuds_connectes(gdf_noeuds, gdf_troncons)
    n_noeuds        = len(noeuds_enrichis)
    n_connectes     = int((noeuds_enrichis["connecte"] == "oui").sum())
    n_non_connectes = int((noeuds_enrichis["connecte"] == "non").sum())
    pct_connectes   = arrondi_pct(n_connectes / n_noeuds * 100) if n_noeuds else 0.0

    # --- 2. Nœuds au milieu des tronçons ---
    # Appelé APRES verifier_noeuds_connectes pour garantir l'exclusivité
    # des catégories : un nœud raccordé ne peut pas être "au milieu"
    print("    Nœuds au milieu des tronçons ...")
    noeuds_enrichis, n_milieu = verifier_noeuds_milieu_troncon(
        noeuds_enrichis, gdf_troncons
    )

    # --- 3. Délimitation des tronçons ---
    print("    Délimitation des tronçons ...")
    troncons_enrichis = verifier_delimitation_troncons(gdf_troncons, gdf_noeuds)
    vc             = troncons_enrichis["statut_delimitation"].value_counts()
    n_deux_cotes   = int(vc.get("deux_cotes",   0))
    n_un_cote      = int(vc.get("un_cote_seul", 0))
    n_non_delimite = int(vc.get("non_delimite", 0))
    n_troncons     = len(troncons_enrichis)

    # --- Taux de conformité topologique ---
    # arrondi_pct évite d'afficher 100% si la valeur réelle est < 100%
    objets_ko    = n_non_connectes + n_milieu + n_un_cote + n_non_delimite
    objets_total = n_noeuds + n_troncons
    taux_topo    = arrondi_pct(
        (1 - objets_ko / objets_total) * 100
    ) if objets_total else 0.0

    return {
        "taux_conformite_topo": taux_topo,
        "noeuds": {
            "total":            n_noeuds,
            "connectes":        n_connectes,
            "non_connectes":    n_non_connectes,
            "pct_connectes":    pct_connectes,
            "au_milieu":        n_milieu,
            "gdf":              noeuds_enrichis,
        },
        "troncons": {
            "total":            n_troncons,
            "deux_cotes":       n_deux_cotes,
            "un_cote_seul":     n_un_cote,
            "non_delimite":     n_non_delimite,
            "gdf":              troncons_enrichis,
        },
    }
