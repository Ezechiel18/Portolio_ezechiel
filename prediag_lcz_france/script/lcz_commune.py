# -*- coding: utf-8 -*-
"""
Pré-diagnostic de la surchauffe urbaine par les zones climatiques locales (LCZ)
===============================================================================

Méthode inspirée du Cerema (guide technique, juin 2026), appliquée commune par
commune en France métropolitaine, sur une grille régulière de 200 m.

COMMENT LANCER LE SCRIPT
------------------------
Ouvre l'invite Anaconda, active l'environnement, place-toi dans le dossier du
script, puis tape une des commandes suivantes :

    conda activate qual_env

    Une commune (code INSEE) :
        python lcz_commune.py 34023

    Plusieurs communes (codes séparés par un espace) :
        python lcz_commune.py 34023 34172 34129

    Toutes les communes d'un département :
        python lcz_commune.py --departement 34

Chaque commune est calculée séparément et reçoit son propre dossier de résultats.
Si une commune échoue, le script le signale et passe à la suivante.

DÉROULÉ POUR CHAQUE COMMUNE (identique au texte de méthode)
-----------------------------------------------------------
    Étape 1  Récupérer le contour de la commune (flux BD TOPO)
    Étape 2  Construire la grille de 200 m (mailles entières qui touchent la commune)
             et mesurer la surface de chaque maille située dans la commune
    Étape 3  Récupérer les bâtiments (flux BD TOPO) et appliquer le filtre du Cerema
    Étape 4  Lire l'OCS GE du département et la reclasser en 6 classes
    Étape 5  Calculer les indicateurs de forme urbaine : HRE et ARE
    Étape 6  Calculer les indicateurs d'occupation du sol : BuR, RoR, BsR, WaR, VeR, VHR
    Étape 7  Attribuer la classe LCZ (arbre de décision, Figure 5 du guide Cerema)
    Étape 8  Contrôles qualité
    Étape 9  Sorties : GeoPackage, cartes, graphique, rapport

Toutes les données sont reprojetées en Lambert-93 (EPSG:2154) avant l'analyse.
"""

# =============================================================================
# ÉTAPE 0 : VÉRIFIER LES BIBLIOTHÈQUES
# =============================================================================
# Avant tout, on vérifie que toutes les bibliothèques utilisées sont installées
# dans l'environnement. Sinon, le script s'arrêterait au milieu du calcul avec
# une erreur peu claire. Ici, il s'arrête tout de suite et dit ce qui manque.
import importlib.util
import sys

BIBLIOTHEQUES = ["numpy", "pandas", "geopandas", "shapely", "pyogrio", "requests", "matplotlib"]
manquantes = [b for b in BIBLIOTHEQUES if importlib.util.find_spec(b) is None]
if manquantes:
    sys.exit(
        "Bibliothèques manquantes dans l'environnement : " + ", ".join(manquantes)
        + "\nInstalle-les dans qual_env (par exemple : conda install -c conda-forge "
        + " ".join(manquantes) + "), puis relance le script."
    )

import argparse                       # lecture des arguments tapés dans l'invite de commande
import time                           # pauses entre deux tentatives de requête
from pathlib import Path              # manipulation des chemins de fichiers et dossiers

import matplotlib
matplotlib.use("Agg")                 # crée les images sans ouvrir de fenêtre
import matplotlib.pyplot as plt       # cartes et graphiques
from matplotlib.patches import Patch  # carrés de couleur des légendes
import numpy as np                    # calcul numérique
import pandas as pd                   # tableaux de données
import geopandas as gpd               # tableaux de données avec géométries
import pyogrio                        # lecture et écriture des fichiers SIG
import requests                       # requêtes vers le flux WFS
from shapely.geometry import box      # création de rectangles (mailles, emprises)

# On lit et on écrit les fichiers avec pyogrio (et jamais avec fiona).
gpd.options.io_engine = "pyogrio"


# =============================================================================
# PARAMÈTRES : tout ce que tu peux avoir besoin de modifier est ici
# =============================================================================

# Dossier racine de l'OCS GE. Il contient un sous-dossier par
# département, par exemple OCS-GE_2-0__GPKG_LAMB93_D034_2024-01-01.
RACINE_OCSGE = Path(r"H:\M2_Avignon\Cours\stage\mes_travaux_en _stage\wetransfer_projet_lcz_2026-09-29_1442\projet_lcz\data")
# Nom du fichier OCS GE à chercher dans le dossier de chaque département.
NOM_FICHIER_OCSGE = "OCCUPATION_SOL.gpkg"

# Dossier où sont écrits les résultats. Par défaut : un dossier "sorties" placé
# à côté du script, avec un sous-dossier par commune.
# Pour choisir un autre emplacement, remplace la ligne par exemple par :
#     DOSSIER_SORTIES = Path(r"C:\projets\lcz\resultats")
DOSSIER_SORTIES = Path(__file__).resolve().parent / "sorties"

# Adresse du flux WFS de la Géoplateforme et noms des couches utilisées.
URL_WFS = "https://data.geopf.fr/wfs/ows"
COUCHE_COMMUNE = "BDTOPO_V3:commune"
COUCHE_BATIMENT = "BDTOPO_V3:batiment"

# Système de coordonnées de travail : Lambert-93.
CRS_TRAVAIL = "EPSG:2154"

# Grille : mailles carrées de 200 m de côté, donc 40 000 m² chacune.
# Les mailles ne sont jamais découpées par la limite communale : elles font
# toutes 40 000 m², et c'est cette surface qui sert à calculer les taux.
TAILLE_MAILLE = 200.0
SURFACE_MAILLE = TAILLE_MAILLE ** 2

# Contrôle qualité n°1 : tolérance sur la somme des taux.
# Dans une maille, BuR + RoR + BsR + WaR + VeR doit faire 100 %, puisque l'OCS GE
# recouvre tout le sol. En pratique, les calculs de surface donnent 99,9 % ou
# 100,1 %. La tolérance fixe l'écart accepté avant de signaler la maille :
# avec 1.0, une somme entre 99 % et 101 % est normale ; en dehors, la maille est
# signalée (trou dans l'OCS GE, polygones qui se chevauchent, bord de mer...).
TOLERANCE_SOMME = 1.0

# Paramètres des requêtes WFS.
# Le serveur ne renvoie pas tous les bâtiments d'un coup : il les envoie par
# paquets appelés "pages". TAILLE_PAGE est le nombre de bâtiments demandés par
# page. Le script enchaîne les pages jusqu'à avoir tout reçu.
TAILLE_PAGE = 1000
# Le serveur de l'IGN a parfois des pannes passagères. En cas d'échec, le script
# réessaie. Cette liste donne l'attente avant chaque tentative, en secondes :
# 1re tentative tout de suite (0), 2e après 10 s, 3e après 30 s, 4e après 60 s.
# Après 4 échecs, la commune est abandonnée et le script passe à la suivante.
DELAIS_REESSAI = [0, 10, 30, 60]
# Temps maximal d'attente d'une réponse du serveur, en secondes. Au-delà, la
# tentative est considérée comme un échec (et une nouvelle tentative est lancée).
DELAI_REPONSE = 120

# -----------------------------------------------------------------------------
# Reclassement OCS GE (champ code_cs) vers les 6 classes de la méthode
# -----------------------------------------------------------------------------
# Les 6 classes sont numérotées de 1 à 6.
BATI, ROUTE, SOL_NU, EAU, ARBORE, HERBACE = 1, 2, 3, 4, 5, 6

# Table de correspondance : à chaque code de couverture OCS GE, sa classe.
RECLASSEMENT_OCSGE = {
    "CS1.1.1.1": BATI,      # Zones bâties
    "CS1.1.1.2": ROUTE,     # Zones non bâties
    "CS1.1.2.1": SOL_NU,    # Zones à matériaux minéraux
    "CS1.1.2.2": SOL_NU,    # Zones à autres matériaux composites
    "CS1.2.1": SOL_NU,      # Sols nus
    "CS1.2.2": EAU,         # Surfaces d'eau
    "CS1.2.3": EAU,         # Névés et glaciers
    "CS2.1.1.1": ARBORE,    # Peuplements de feuillus
    "CS2.1.1.2": ARBORE,    # Peuplements de conifères
    "CS2.1.1.3": ARBORE,    # Peuplements mixtes
    "CS2.1.2": HERBACE,     # Formations arbustives et sous-arbrisseaux
    "CS2.1.3": HERBACE,     # Autres formations ligneuses
    "CS2.2.1": HERBACE,     # Formations herbacées
    "CS2.2.2": HERBACE,     # Autres formations non ligneuses
}
# Règle des voies ferrées (appliquée avant la table) : les catégories
# (couverture CS1.1.2.1 et usage US4.1.2) vont en "route et surface imperméable",
# comme dans la méthode du Cerema.
CODE_CS_BALLAST = "CS1.1.2.1"
CODE_US_FERRE = "US4.1.2"

# -----------------------------------------------------------------------------
# Classes LCZ : libellés Cartagène et couleurs de la carte
# -----------------------------------------------------------------------------
LCZ_INFO = {
    "1": ("Ensemble compact de tours", "#8C0000"),
    "2": ("Ensemble compact d'immeubles", "#D10000"),
    "3": ("Ensemble compact de maisons", "#FF0000"),
    "4": ("Ensemble de tours espacées", "#BF4D00"),
    "5": ("Ensemble d'immeubles espacés", "#FF6600"),
    "6": ("Ensemble de maisons espacées", "#FF9955"),
    "7": ("Ensemble dense de constructions légères", "#FAEE05"),
    "8/10": ("Bâtiments de grande emprise", "#BCBCBC"),
    "9": ("Implantation diffuse de maisons", "#FFCCAA"),
    "A": ("Espace densément arboré", "#006A00"),
    "B": ("Espace arboré clairsemé", "#00AA00"),
    "C": ("Espace végétalisé hétérogène", "#648525"),
    "D": ("Végétation basse", "#B9DB79"),
    "E": ("Sol imperméable naturel ou artificiel", "#000000"),
    "F": ("Sol nu perméable", "#FBF7AE"),
    "G": ("Surface en eau", "#6A6AFF"),
}

# Degrés de sensibilité à l'îlot de chaleur, repris de la légende Cartagène du Cerema.
SENSIBILITE = {
    "1": "Très forte", "2": "Très forte",
    "3": "Forte",
    "4": "Moyenne", "5": "Moyenne",
    "6": "Faible", "9": "Faible",
    "7": "Variable", "8/10": "Variable", "E": "Variable",
    "A": "Faible à nulle", "B": "Faible à nulle", "C": "Faible à nulle",
    "D": "Faible à nulle", "F": "Faible à nulle", "G": "Faible à nulle",
}
# Couleurs de la carte de sensibilité (le Cerema n'en fixe pas : choix d'affichage).
COULEURS_SENSIBILITE = {
    "Très forte": "#7F0000",
    "Forte": "#D7301F",
    "Moyenne": "#FC8D59",
    "Faible": "#FDD49E",
    "Variable": "#9E9E9E",
    "Faible à nulle": "#C7E9C0",
}


class ErreurCommune(Exception):
    """Erreur qui arrête le calcul d'UNE commune (le script passe à la suivante)."""


def etape(numero, texte):
    """Affiche le titre d'une étape dans la console, pour suivre l'avancement."""
    print(f"\n=== Étape {numero} : {texte}")


# =============================================================================
# OUTILS WFS : dialogue avec le flux de la Géoplateforme
# =============================================================================
def requete_wfs(parametres):
    """Envoie UNE requête au flux WFS et renvoie la réponse.

    En cas d'échec (serveur en panne, réponse trop lente), la requête est
    retentée selon DELAIS_REESSAI. Après le dernier échec, la commune est
    abandonnée.
    """
    # Paramètres communs à toutes les requêtes :
    #   GetFeature : on demande des objets géographiques
    #   SRSNAME    : on veut les coordonnées en Lambert-93
    #   OUTPUTFORMAT : réponse au format GeoJSON, facile à lire en Python
    base = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "SRSNAME": CRS_TRAVAIL,
        "OUTPUTFORMAT": "application/json",
    }
    base.update(parametres)
    derniere_erreur = None
    for attente in DELAIS_REESSAI:
        if attente:
            print(f"    nouvelle tentative dans {attente} s...")
            time.sleep(attente)
        try:
            reponse = requests.get(URL_WFS, params=base, timeout=DELAI_REPONSE)
            reponse.raise_for_status()      # déclenche une erreur si le serveur répond "erreur"
            return reponse.json()
        except (requests.RequestException, ValueError) as erreur:
            derniere_erreur = erreur
            print(f"    échec de la requête : {erreur}")
    raise ErreurCommune(f"Le flux WFS ne répond pas après plusieurs tentatives : {derniere_erreur}")


def telecharger_wfs(couche, filtre=None, emprise=None, tri=None):
    """Télécharge TOUS les objets d'une couche WFS, page par page.

    couche  : nom de la couche, par exemple "BDTOPO_V3:batiment"
    filtre  : filtre CQL (texte), par exemple "code_insee='34023'"
    emprise : rectangle (xmin, ymin, xmax, ymax) en Lambert-93 : seuls les objets
              qui touchent ce rectangle sont demandés
    tri     : champ de tri. Indispensable quand il y a plusieurs pages : sans tri,
              le serveur peut renvoyer les objets dans un ordre différent d'une
              page à l'autre, et on risquerait d'en perdre ou d'en avoir en double.
    """
    objets = []            # tous les objets reçus
    debut = 0              # position du premier objet de la page demandée
    total_annonce = None   # nombre total d'objets annoncé par le serveur
    while True:
        parametres = {"TYPENAMES": couche, "COUNT": TAILLE_PAGE, "STARTINDEX": debut}
        if filtre:
            parametres["CQL_FILTER"] = filtre
        if emprise:
            parametres["BBOX"] = ",".join(f"{v:.2f}" for v in emprise) + "," + CRS_TRAVAIL
        if tri:
            parametres["SORTBY"] = tri
        page = requete_wfs(parametres)
        if total_annonce is None:
            total_annonce = page.get("numberMatched")
        recus = page.get("features", [])
        if not recus:                        # page vide : tout a été reçu
            break
        objets.extend(recus)
        debut += len(recus)                  # la page suivante commence après ceux reçus
        print(f"    {couche} : {len(objets)} objets reçus")
        if isinstance(total_annonce, int) and len(objets) >= total_annonce:
            break                            # total annoncé atteint : inutile de continuer

    # Sécurité : on prévient si le nombre reçu ne correspond pas au total annoncé.
    if isinstance(total_annonce, int) and len(objets) != total_annonce:
        print(f"    ATTENTION : {len(objets)} objets reçus pour {total_annonce} annoncés par le serveur")

    if not objets:
        return gpd.GeoDataFrame(geometry=[], crs=CRS_TRAVAIL)
    return gpd.GeoDataFrame.from_features(objets, crs=CRS_TRAVAIL)


def verifier_champs(table, champs, origine):
    """Arrête le calcul de la commune si des champs attendus sont absents,
    en affichant les champs réellement disponibles."""
    absents = [c for c in champs if c not in table.columns]
    if absents:
        raise ErreurCommune(
            f"Champs absents dans {origine} : {', '.join(absents)}\n"
            f"Champs disponibles : {', '.join(map(str, table.columns))}"
        )


def communes_du_departement(code_dep):
    """Liste les codes INSEE de toutes les communes d'un département (flux BD TOPO).

    Le filtre "code_insee LIKE '34%'" sélectionne les codes qui commencent par 34.
    """
    print(f"Recherche des communes du département {code_dep}...")
    communes = telecharger_wfs(COUCHE_COMMUNE, filtre=f"code_insee LIKE '{code_dep}%'", tri="code_insee")
    if communes.empty or "code_insee" not in communes.columns:
        sys.exit(f"Aucune commune trouvée pour le département {code_dep}.")
    codes = sorted(communes["code_insee"].astype(str).unique())
    print(f"{len(codes)} communes trouvées.")
    return codes


# =============================================================================
# ÉTAPE 1 : CONTOUR DE LA COMMUNE
# =============================================================================
def charger_commune(code_insee):
    """Récupère le contour de la commune dans le flux BD TOPO, à partir de son code INSEE."""
    etape(1, f"contour de la commune {code_insee} (flux BD TOPO)")
    commune = telecharger_wfs(COUCHE_COMMUNE, filtre=f"code_insee='{code_insee}'")
    if commune.empty:
        raise ErreurCommune(f"Aucune commune trouvée avec le code INSEE {code_insee}.")
    verifier_champs(commune, ["code_insee"], "la couche commune")
    # Nom de la commune, utilisé seulement pour les titres et le nom du dossier.
    # On cherche le champ du nom ; s'il n'existe pas, on garde le code INSEE.
    nom = code_insee
    for champ in ("nom_officiel", "nom"):
        if champ in commune.columns and pd.notna(commune[champ].iloc[0]):
            nom = str(commune[champ].iloc[0])
            break
    # Si la commune est en plusieurs morceaux, on les réunit en un seul objet.
    commune = commune[["geometry"]].dissolve()
    print(f"    commune : {nom}")
    return commune, nom


# =============================================================================
# ÉTAPE 2 : GRILLE DE 200 M
# =============================================================================
def construire_grille(commune):
    """Construit la grille de 200 m sur la commune.

    1. On prend le rectangle qui englobe la commune.
    2. On cale son coin en bas à gauche sur un multiple de 200 m (par exemple
       x = 700 000 plutôt que 700 037), pour que les grilles de deux communes
       voisines tombent exactement sur les mêmes mailles.
    3. On remplit le rectangle de carrés de 200 m.
    4. On garde les mailles ENTIÈRES qui touchent la commune, sans les découper.
       Les indicateurs et la classe LCZ sont toujours calculés sur la maille
       entière (40 000 m²).
    5. Pour les statistiques communales uniquement, on mesure la surface EXACTE
       de chaque maille située à l'intérieur de la limite communale
       (colonne surface_commune, en m²). Une maille entièrement dans la commune
       vaut 40 000 m² ; une maille de bord vaut la surface réelle de sa partie
       dans la commune, calculée par intersection avec le contour.
    """
    etape(2, "grille de 200 m")
    xmin, ymin, xmax, ymax = commune.total_bounds
    x0 = np.floor(xmin / TAILLE_MAILLE) * TAILLE_MAILLE      # coin calé sur 200 m
    y0 = np.floor(ymin / TAILLE_MAILLE) * TAILLE_MAILLE
    xs = np.arange(x0, xmax, TAILLE_MAILLE)                   # abscisses des colonnes
    ys = np.arange(y0, ymax, TAILLE_MAILLE)                   # ordonnées des lignes
    carres = [box(x, y, x + TAILLE_MAILLE, y + TAILLE_MAILLE) for x in xs for y in ys]
    grille = gpd.GeoDataFrame(geometry=carres, crs=CRS_TRAVAIL)
    grille = grille[grille.intersects(commune.geometry.iloc[0])].reset_index(drop=True)
    grille["id_maille"] = np.arange(1, len(grille) + 1)       # identifiant unique

    # Surface exacte de chaque maille à l'intérieur de la commune (intersection
    # de la maille avec le contour communal). Sert seulement aux statistiques.
    contour = commune.geometry.iloc[0]
    grille["surface_commune"] = grille.geometry.intersection(contour).area

    # Vérification : la somme de ces surfaces doit être égale à la surface de la
    # commune, puisque les mailles recouvrent toute la commune sans se superposer.
    surface_contour = contour.area
    ecart = grille["surface_commune"].sum() - surface_contour
    print(f"    {len(grille)} mailles")
    print(f"    surface de la commune : {surface_contour / 10000:.2f} ha ; "
          f"somme des surfaces des mailles dans la commune : "
          f"{grille['surface_commune'].sum() / 10000:.2f} ha (écart : {ecart:.2f} m²)")
    return grille[["id_maille", "surface_commune", "geometry"]]


# =============================================================================
# ÉTAPE 3 : BÂTIMENTS BD TOPO ET FILTRE DU CEREMA
# =============================================================================
def charger_batiments(grille):
    """Récupère les bâtiments de l'emprise de la grille et applique le filtre du Cerema."""
    etape(3, "bâtiments (flux BD TOPO) et filtre du Cerema")
    emprise = tuple(grille.total_bounds)       # rectangle qui englobe toute la grille
    bati = telecharger_wfs(COUCHE_BATIMENT, emprise=emprise, tri="cleabs")
    if bati.empty:
        print("    aucun bâtiment dans l'emprise")
        return gpd.GeoDataFrame({"hauteur": [], "surface_bati": []}, geometry=[], crs=CRS_TRAVAIL)

    verifier_champs(
        bati,
        ["hauteur", "construction_legere", "etat_de_l_objet", "precision_altimetrique"],
        "la couche bâtiment",
    )
    nb_avant = len(bati)

    # Filtre du guide technique Cerema (section 3.2) :
    #   hauteur IS NOT NULL AND hauteur >= 3 AND construction_legere IS false
    #   AND etat_de_l_objet = 'En service' AND precision_altimetrique != 9999
    # Traduction fidèle de la logique SQL : une valeur vide ne passe jamais un
    # test. Un bâtiment sans précision altimétrique renseignée est donc exclu,
    # exactement comme avec la requête SQL.
    hauteur = pd.to_numeric(bati["hauteur"], errors="coerce")
    precision = pd.to_numeric(bati["precision_altimetrique"], errors="coerce")
    garde = (
        hauteur.notna()                                   # hauteur renseignée
        & (hauteur >= 3)                                  # au moins 3 m
        & bati["construction_legere"].eq(False)           # pas une construction légère
        & bati["etat_de_l_objet"].eq("En service")        # bâtiment en service
        & precision.notna()                               # précision renseignée
        & (precision != 9999)                             # précision différente de 9999
    )
    bati = bati.loc[garde, ["geometry"]].copy()
    bati["hauteur"] = hauteur[garde].values
    # Surface ENTIÈRE du bâtiment, calculée avant tout croisement avec la grille.
    bati["surface_bati"] = bati.geometry.area
    print(f"    {nb_avant} bâtiments reçus, {len(bati)} retenus après filtre")
    return bati.reset_index(drop=True)


# =============================================================================
# ÉTAPE 4 : OCS GE DU DÉPARTEMENT, RECLASSÉE EN 6 CLASSES
# =============================================================================
def trouver_fichier_ocsge(code_dep):
    """Trouve le fichier OCCUPATION_SOL.gpkg du département sur le serveur.

    Le dossier du département contient le code sur trois caractères : D034 pour
    l'Hérault, D02A pour la Corse-du-Sud. S'il y a zéro ou plusieurs fichiers,
    le calcul s'arrête : le script ne choisit jamais un fichier à ta place.
    """
    code3 = code_dep.zfill(3)                                  # "34" devient "034"
    dossiers = [d for d in RACINE_OCSGE.glob(f"*_D{code3}_*") if d.is_dir()]
    fichiers = [f for d in dossiers for f in d.rglob(NOM_FICHIER_OCSGE)]
    if len(fichiers) != 1:
        detail = "\n".join(f"  {f}" for f in fichiers) or "  aucun"
        raise ErreurCommune(
            f"Il faut exactement un fichier {NOM_FICHIER_OCSGE} pour le département "
            f"{code_dep} dans {RACINE_OCSGE}. Trouvés :\n{detail}"
        )
    return fichiers[0]


def lire_ocsge_departement(fichier, grille):
    """Lit l'OCS GE, uniquement sur l'emprise de la grille, puis la passe en Lambert-93."""
    # 1. Trouver, dans le GeoPackage, la couche qui contient le champ code_cs.
    couches = [c[0] for c in pyogrio.list_layers(fichier)]
    candidates = [c for c in couches if "code_cs" in pyogrio.read_info(fichier, layer=c)["fields"]]
    if len(candidates) != 1:
        raise ErreurCommune(f"Impossible d'identifier la couche OCS GE dans {fichier}. Couches : {couches}")
    couche = candidates[0]
    if "code_us" not in pyogrio.read_info(fichier, layer=couche)["fields"]:
        raise ErreurCommune(f"Champ code_us absent dans {fichier} (couche {couche}).")

    # 2. Détecter le système de coordonnées du fichier, et y convertir l'emprise
    #    de la grille, pour ne lire que les polygones utiles (lecture rapide).
    crs_fichier = pyogrio.read_info(fichier, layer=couche)["crs"]
    emprise = gpd.GeoSeries([box(*grille.total_bounds)], crs=CRS_TRAVAIL).to_crs(crs_fichier).total_bounds
    ocs = gpd.read_file(fichier, layer=couche, columns=["code_cs", "code_us"], bbox=tuple(emprise))
    print(f"    {len(ocs)} polygones lus (système du fichier : {crs_fichier})")

    # 3. Reprojeter en Lambert-93.
    return ocs.to_crs(CRS_TRAVAIL)


def reclasser_ocsge(ocs):
    """Reclasse l'OCS GE en 6 classes.

    Contrôle qualité n°4 : si un code n'est pas dans la table de reclassement,
    le calcul est arrêté. Aucune zone n'est classée au hasard.
    """
    codes = ocs["code_cs"]
    inconnus = sorted(set(codes.dropna().astype(str)) - set(RECLASSEMENT_OCSGE))
    if codes.isna().any():
        inconnus.append("(code vide)")
    if inconnus:
        raise ErreurCommune(
            "Contrôle n°4 : codes OCS GE absents de la table de reclassement : "
            + ", ".join(inconnus)
            + "\nLe calcul est arrêté : aucune zone n'est classée au hasard."
        )
    ocs = ocs.copy()
    ocs["classe"] = codes.map(RECLASSEMENT_OCSGE)              # application de la table
    ballast = codes.eq(CODE_CS_BALLAST) & ocs["code_us"].eq(CODE_US_FERRE)
    ocs.loc[ballast, "classe"] = ROUTE                         # règle des voies ferrées
    print(f"    {int(ballast.sum())} polygones de voies ferrées reclassés en surface imperméable")
    return ocs[["classe", "geometry"]]


def charger_ocsge(grille, code_insee):
    """Charge et reclasse l'OCS GE du département de la commune.

    Le département est donné par les deux premiers caractères du code INSEE
    (34 pour 34023, 2A ou 2B pour la Corse).
    """
    etape(4, "OCS GE du département, reclassée en 6 classes")
    code_dep = code_insee[:2]
    ocs = lire_ocsge_departement(trouver_fichier_ocsge(code_dep), grille)
    # Les géométries invalides (polygone qui se recoupe...) font échouer les
    # intersections : on les répare avant de continuer.
    invalides = ~ocs.geometry.is_valid
    if invalides.any():
        ocs.loc[invalides, "geometry"] = ocs.loc[invalides, "geometry"].make_valid()
        print(f"    {int(invalides.sum())} géométries invalides réparées")
    return reclasser_ocsge(ocs)


# =============================================================================
# ÉTAPE 5 : INDICATEURS DE FORME URBAINE (HRE, ARE)
# =============================================================================
def indicateurs_forme(grille, bati):
    """HRE = hauteur moyenne des bâtiments de la maille (m).
    ARE = surface moyenne des bâtiments de la maille (m²), calculée sur la
          surface entière de chaque bâtiment, sans découpage par la maille.

    Un bâtiment est rattaché à toutes les mailles qu'il touche.
    Une maille sans bâtiment reçoit 0 pour HRE et ARE.
    """
    etape(5, "indicateurs de forme urbaine (HRE, ARE)")
    # Jointure spatiale : pour chaque bâtiment, la ou les mailles qu'il touche.
    lien = gpd.sjoin(bati, grille, how="inner", predicate="intersects")
    # Par maille : moyenne des hauteurs, moyenne des surfaces, nombre de bâtiments.
    stats = lien.groupby("id_maille").agg(
        hre=("hauteur", "mean"), are=("surface_bati", "mean"), nb_bati=("hauteur", "size"))
    # On rattache ces valeurs à toutes les mailles ; celles sans bâtiment reçoivent 0.
    res = grille.merge(stats, on="id_maille", how="left")
    res[["hre", "are"]] = res[["hre", "are"]].fillna(0.0)
    res["nb_bati"] = res["nb_bati"].fillna(0).astype(int)
    print(f"    {int((res['nb_bati'] > 0).sum())} mailles contiennent au moins un bâtiment retenu")
    return res


# =============================================================================
# ÉTAPE 6 : INDICATEURS D'OCCUPATION DU SOL
# =============================================================================
def indicateurs_occupation(mailles, ocs):
    """Taux = surface de la classe dans la maille / surface de la maille x 100.
    VeR regroupe végétation arborée et herbacée.
    VHR = végétation arborée / (arborée + herbacée) x 100 ; non défini si VeR = 0.
    """
    etape(6, "indicateurs d'occupation du sol (BuR, RoR, BsR, WaR, VeR, VHR)")
    # 1. Découper l'OCS GE par les mailles : chaque morceau appartient à une maille.
    morceaux = gpd.overlay(ocs, mailles[["id_maille", "geometry"]], how="intersection",
                           keep_geom_type=True)
    morceaux["surface"] = morceaux.geometry.area
    # 2. Tableau des surfaces : une ligne par maille, une colonne par classe.
    surfaces = morceaux.pivot_table(index="id_maille", columns="classe", values="surface",
                                    aggfunc="sum", fill_value=0.0)
    surfaces = surfaces.reindex(columns=[BATI, ROUTE, SOL_NU, EAU, ARBORE, HERBACE], fill_value=0.0)
    # 3. Taux en % de la surface de la maille (40 000 m²).
    taux = pd.DataFrame({
        "bur": surfaces[BATI],
        "ror": surfaces[ROUTE],
        "bsr": surfaces[SOL_NU],
        "war": surfaces[EAU],
        "ver": surfaces[ARBORE] + surfaces[HERBACE],
    }) / SURFACE_MAILLE * 100
    # 4. VHR : part d'arbres dans la végétation (vide si la maille n'a aucune végétation).
    vegetation = surfaces[ARBORE] + surfaces[HERBACE]
    taux["vhr"] = np.where(vegetation > 0, surfaces[ARBORE] / vegetation.where(vegetation > 0) * 100, np.nan)
    # 5. Rattacher les taux aux mailles ; une maille sans OCS GE reçoit 0 partout.
    res = mailles.merge(taux, left_on="id_maille", right_index=True, how="left")
    res[["bur", "ror", "bsr", "war", "ver"]] = res[["bur", "ror", "bsr", "war", "ver"]].fillna(0.0)
    return res


# =============================================================================
# ÉTAPE 7 : ARBRE DE DÉCISION (FIGURE 5 DU GUIDE CEREMA)
# =============================================================================
def classer(m):
    """Renvoie (classe LCZ, VHR forcé à 0) pour une maille.

    Lecture de haut en bas : la première condition vérifiée attribue la classe.
    Taux en %, HRE en m, ARE en m².
    """
    bur, ror, bsr, war, ver = m["bur"], m["ror"], m["bsr"], m["war"], m["ver"]

    # --- Branche bâtie : BuR > 10 % (BuR = 10 % exactement part en non bâti)
    if bur > 10:
        # LCZ 8/10, testée en premier
        if m["hre"] <= 21 and m["are"] > 700 and (bur + ror) > 40:
            return "8/10", False
        # Tours : HRE > 30 m
        if m["hre"] > 30:
            return ("1" if bur > 40 else "4"), False
        # Immeubles : 9 < HRE <= 30 m
        if m["hre"] > 9:
            return ("2" if bur > 40 else "5"), False
        # Maisons : HRE <= 9 m. LCZ 7 testée en premier
        if bur > 60 and bsr > (ror + war + ver):
            return "7", False
        if bur > 40:
            return "3", False
        if bur > 20:
            return "6", False
        return "9", False

    # --- Branche non bâtie : comparaisons strictes, dans l'ordre G, F, E
    if war > ror and war > bsr and war > ver:
        return "G", False
    if bsr > ror and bsr > war and bsr > ver:
        return "F", False
    if ror > bsr and ror > war and ror > ver:
        return "E", False

    # --- LCZ A à D : sortie par défaut, y compris en cas d'égalité.
    # Convention propre à la méthode : si VeR = 0, VHR est fixé à 0 et la maille est marquée.
    force = ver == 0
    vhr = 0.0 if force else m["vhr"]
    if vhr > 50:
        return "A", force
    if vhr > 25:
        return "B", force
    if vhr > 10:
        return "C", force
    return "D", force


def attribuer_lcz(mailles):
    """Applique l'arbre de décision à chaque maille, puis ajoute libellé et sensibilité."""
    etape(7, "attribution de la classe LCZ (Figure 5 du guide Cerema)")
    resultat = mailles.apply(classer, axis=1, result_type="expand")
    mailles = mailles.copy()
    mailles["lcz"] = resultat[0]
    mailles["ctrl_vhr_force"] = resultat[1].astype(bool)
    mailles["libelle"] = mailles["lcz"].map(lambda c: LCZ_INFO[c][0])
    mailles["sensibilite"] = mailles["lcz"].map(SENSIBILITE)
    return mailles


# =============================================================================
# ÉTAPE 8 : CONTRÔLES QUALITÉ
# =============================================================================
def controles(mailles):
    """Le contrôle n°4 (codes inconnus) est fait à l'étape 4 : il arrête le calcul.
    Les trois autres ne corrigent rien : ils marquent les mailles concernées par
    une colonne vrai/faux, visible dans QGIS.
    """
    etape(8, "contrôles qualité")
    mailles = mailles.copy()
    # Contrôle n°1 : la somme des taux doit être proche de 100 % (voir TOLERANCE_SOMME).
    mailles["somme_taux"] = mailles[["bur", "ror", "bsr", "war", "ver"]].sum(axis=1)
    mailles["ctrl_somme"] = (mailles["somme_taux"] - 100).abs() > TOLERANCE_SOMME
    # Contrôle n°2 : maille bâtie (BuR > 10 %) sans aucun bâtiment BD TOPO retenu.
    mailles["ctrl_bati_sans_bdtopo"] = (mailles["bur"] > 10) & (mailles["nb_bati"] == 0)
    # Contrôle n°3 : VHR forcé à 0 (colonne ctrl_vhr_force, remplie à l'étape 7).
    for col in ("ctrl_somme", "ctrl_bati_sans_bdtopo", "ctrl_vhr_force"):
        print(f"    {col} : {int(mailles[col].sum())} mailles")
    return mailles


# =============================================================================
# ÉTAPE 9 : SORTIES
# =============================================================================
def carte(mailles, commune, colonne, couleurs, titre, fichier, ordre):
    """Dessine une carte des mailles colorées selon une colonne, avec légende.

    ordre : liste de (valeur, texte de légende), dans l'ordre d'affichage.
    Seules les valeurs présentes dans la commune apparaissent dans la légende.
    """
    fig, ax = plt.subplots(figsize=(10, 10))
    mailles.plot(ax=ax, color=mailles[colonne].map(couleurs), edgecolor="white", linewidth=0.2)
    commune.boundary.plot(ax=ax, color="#1C2130", linewidth=1.2)     # limite communale
    presentes = [c for c in ordre if c[0] in set(mailles[colonne])]
    legende = [Patch(facecolor=couleurs[c], edgecolor="#999999", label=etiquette)
               for c, etiquette in presentes]
    ax.legend(handles=legende, loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False, fontsize=9)
    ax.set_title(titre, fontsize=13, loc="left")
    ax.set_axis_off()
    fig.savefig(fichier, dpi=200, bbox_inches="tight")
    plt.close(fig)


def parts_surface_commune(mailles):
    """Part de la surface COMMUNALE occupée par chaque classe LCZ, en %.

    Pour chaque classe : somme des surfaces "dans la commune" des mailles de
    cette classe, divisée par la surface totale de la commune, fois 100.
    Une maille de bord ne compte que pour la surface exacte de sa partie située
    dans la commune. Renvoie un tableau (classe, surface en m², part en %),
    dans l'ordre des classes LCZ, sans les classes absentes.
    """
    surfaces = mailles.groupby("lcz")["surface_commune"].sum()
    surfaces = surfaces[surfaces > 0].reindex(list(LCZ_INFO)).dropna()
    total = mailles["surface_commune"].sum()
    return pd.DataFrame({"surface": surfaces, "part": surfaces / total * 100})


def graphique_repartition(mailles, titre, fichier):
    """Graphique en barres : part de la surface communale par classe LCZ
    (calcul détaillé dans parts_surface_commune)."""
    parts = parts_surface_commune(mailles)["part"]
    fig, ax = plt.subplots(figsize=(10, 5))
    barres = ax.bar(parts.index, parts.values, color=[LCZ_INFO[c][1] for c in parts.index],
                    edgecolor="#666666", linewidth=0.5)
    ax.bar_label(barres, labels=[f"{v:.1f} %" for v in parts.values], fontsize=8, padding=2)
    ax.set_xlabel("Classe LCZ")
    ax.set_ylabel("Part de la surface communale (%)")
    ax.set_title(titre, fontsize=13, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(fichier, dpi=200, bbox_inches="tight")
    plt.close(fig)


def rapport(mailles, code_insee, nom, nb_bati, fichier):
    """Écrit un rapport texte : répartition des classes et résultats des contrôles."""
    n = len(mailles)
    surface_ha = mailles["surface_commune"].sum() / 10000
    lignes = [
        f"Pré-diagnostic LCZ : {nom} ({code_insee})",
        "",
        f"Mailles analysées : {n}",
        f"Surface de la commune : {surface_ha:.2f} ha",
        f"Bâtiments BD TOPO retenus après filtre : {nb_bati}",
        "",
        "Répartition des classes LCZ sur la surface de la commune",
        "(les mailles de bord comptent pour leur seule partie située dans la commune) :",
    ]
    for code, ligne in parts_surface_commune(mailles).iterrows():
        lignes.append(f"  LCZ {code:<5} {LCZ_INFO[code][0]:<42} "
                      f"{ligne['surface'] / 10000:9.2f} ha  ({ligne['part']:5.1f} %)")
    lignes += [
        "",
        "Contrôles qualité (mailles marquées dans le GeoPackage) :",
        f"  1. Somme des taux écartée de plus de {TOLERANCE_SOMME} point de 100 % : "
        f"{int(mailles['ctrl_somme'].sum())}",
        f"  2. Mailles bâties (BuR > 10 %) sans bâtiment BD TOPO retenu : "
        f"{int(mailles['ctrl_bati_sans_bdtopo'].sum())}",
        f"  3. Mailles avec VHR forcé à 0 : {int(mailles['ctrl_vhr_force'].sum())}",
        "  4. Codes OCS GE inconnus : aucun (sinon le calcul aurait été arrêté)",
        "",
        "Lecture : pré-diagnostic de la surchauffe urbaine, pas une carte d'îlot de chaleur.",
    ]
    Path(fichier).write_text("\n".join(lignes), encoding="utf-8")


def sorties(mailles, commune, code_insee, nom, nb_bati):
    """Écrit tous les résultats dans le dossier de la commune."""
    etape(9, "sorties")
    # Dossier de la commune, par exemple sorties\34023-Assas
    dossier = DOSSIER_SORTIES / f"{code_insee}-{nom}".replace(" ", "-").replace("/", "-")
    dossier.mkdir(parents=True, exist_ok=True)

    # 1. GeoPackage des mailles, à ouvrir dans QGIS.
    colonnes = ["id_maille", "lcz", "libelle", "sensibilite", "surface_commune", "hre", "are", "nb_bati",
                "bur", "ror", "bsr", "war", "ver", "vhr", "somme_taux",
                "ctrl_somme", "ctrl_bati_sans_bdtopo", "ctrl_vhr_force", "geometry"]
    mailles[colonnes].to_file(dossier / "mailles-lcz.gpkg", layer="mailles_lcz", driver="GPKG")

    # 2. Carte LCZ.
    carte(mailles, commune, "lcz", {c: v[1] for c, v in LCZ_INFO.items()},
          f"Zones climatiques locales : {nom}", dossier / "carte-lcz.png",
          [(c, f"LCZ {c} : {v[0]}") for c, v in LCZ_INFO.items()])
    # 3. Carte de sensibilité.
    carte(mailles, commune, "sensibilite", COULEURS_SENSIBILITE,
          f"Sensibilité à l'îlot de chaleur (degrés Cerema) : {nom}", dossier / "carte-sensibilite.png",
          [(s, s) for s in COULEURS_SENSIBILITE])
    # 4. Graphique de répartition (sur la surface de la commune).
    graphique_repartition(mailles, f"Répartition des classes LCZ : {nom}", dossier / "repartition-lcz.png")
    # 5. Rapport des contrôles.
    rapport(mailles, code_insee, nom, nb_bati, dossier / "rapport-controles.txt")
    print(f"    résultats écrits dans {dossier}")
    return dossier


# =============================================================================
# CALCUL COMPLET POUR UNE COMMUNE
# =============================================================================
def traiter_commune(code_insee):
    """Enchaîne les étapes 1 à 9 pour une commune."""
    commune, nom = charger_commune(code_insee)
    grille = construire_grille(commune)
    bati = charger_batiments(grille)
    ocs = charger_ocsge(grille, code_insee)
    mailles = indicateurs_forme(grille, bati)
    mailles = indicateurs_occupation(mailles, ocs)
    mailles = attribuer_lcz(mailles)
    mailles = controles(mailles)
    sorties(mailles, commune, code_insee, nom, len(bati))


# =============================================================================
# PROGRAMME PRINCIPAL
# =============================================================================
def main():
    # Lecture de ce que tu as tapé dans l'invite de commande :
    #   des codes INSEE (un ou plusieurs), OU l'option --departement.
    parser = argparse.ArgumentParser(description="Pré-diagnostic LCZ de communes.")
    parser.add_argument("codes_insee", nargs="*", help="un ou plusieurs codes INSEE, par exemple 34023 34172")
    parser.add_argument("--departement", help="code d'un département, par exemple 34 ou 2A")
    args = parser.parse_args()

    if args.departement:
        codes = communes_du_departement(args.departement.strip().upper())
    elif args.codes_insee:
        codes = [c.strip().upper() for c in args.codes_insee]
    else:
        parser.error("indique au moins un code INSEE, ou --departement suivi d'un code de département.")

    # Chaque commune est calculée séparément. Si une commune échoue, on note
    # l'erreur et on passe à la suivante, sans arrêter tout le traitement.
    reussies, echouees = [], []
    for i, code in enumerate(codes, start=1):
        print(f"\n##### Commune {i}/{len(codes)} : {code}")
        try:
            traiter_commune(code)
            reussies.append(code)
        except Exception as erreur:
            print(f"\n!!! Échec pour {code} : {erreur}")
            echouees.append((code, str(erreur)))

    # Bilan final.
    print(f"\nTerminé : {len(reussies)} commune(s) réussie(s), {len(echouees)} en échec.")
    for code, erreur in echouees:
        print(f"  {code} : {erreur.splitlines()[0]}")


if __name__ == "__main__":
    main()
