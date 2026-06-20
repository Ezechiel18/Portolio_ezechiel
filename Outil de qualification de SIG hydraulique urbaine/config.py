# =============================================================================
#  config.py — Configuration centrale du projet de qualification SIG — SCE
#
#  Ce fichier contient les paramètres du projet (chemins, infos projet,
#  caractères interdits, pondérations). Il ne contient PAS le mapping
#  des champs — celui-ci est dans mapping.py.
#
#  À MODIFIER pour chaque nouveau projet : chemins, nom projet, commune.
#  NE PAS MODIFIER : les listes de caractères et les constantes techniques.
# =============================================================================

import os

# -----------------------------------------------------------------------------
#  CHEMINS DES DONNÉES D'ENTRÉE
#  Modifier pour pointer vers les fichiers du client.
# -----------------------------------------------------------------------------
DATA_DIR     = r"C:\Projet_prediag\qualification\test_data"
TRONCON_FILE = os.path.join(DATA_DIR, "Troncon.shp")
NOEUD_FILE   = os.path.join(DATA_DIR, "Noeud.shp")

# -----------------------------------------------------------------------------
#  LOGO SCE
#  Renseigner le chemin vers le fichier PNG du logo SCE.
#  Ex : r"C:\logos\logo_sce.png"
#  Laisser None pour utiliser le logo SVG de substitution.
# -----------------------------------------------------------------------------
LOGO_SCE_PATH = r"C:\Projet_prediag\qualification\logo\Logo_SCEsf.png"  # ← REMPLACER PAR LE CHEMIN RÉEL DU LOGO SCE

# -----------------------------------------------------------------------------
#  INFORMATIONS DU PROJET (affichées dans l'en-tête du rapport)
# -----------------------------------------------------------------------------
PROJET_NOM      = "Réseau d'assainissement"
PROJET_COMMUNE  = "Commune X"
PROJET_VERSION  = "v1.0"
# La date est générée automatiquement à l'exécution — ne pas renseigner ici.

# -----------------------------------------------------------------------------
#  CARACTÈRES INTERDITS DANS LES CHAMPS TEXTE
#  Problèmes de traitement et d'encodage dans les couches SIG.
# -----------------------------------------------------------------------------
SPECIAL_CHARS = [
    '<', '>', '&', "'", '"', ';', '/', '\\',
    '|', '*', '?', '#', '@', '!', '%', '`',
    '^', '{', '}', '[', ']', '~', '$'
]

ACCENT_CHARS = [
    'é','è','ê','ë','à','â','ù','û','ü','î','ï','ô','ö','ç','æ','œ',
    'É','È','Ê','Ë','À','Â','Ù','Û','Ü','Î','Ï','Ô','Ö','Ç','Æ','Œ'
]

# -----------------------------------------------------------------------------
#  PARAMÈTRE TOPOLOGIQUE
#  Distance max (mètres) entre un nœud et une extrémité de tronçon
#  pour considérer qu'ils sont connectés.
#  La donnée est reprojetée en Lambert 93 (EPSG:2154) si nécessaire.
# -----------------------------------------------------------------------------
SNAP_TOLERANCE = 0.5

# -----------------------------------------------------------------------------
#  PONDÉRATION DE L'INDICE FINAL DE QUALITÉ
#  La somme doit être égale à 1.0
# -----------------------------------------------------------------------------
POIDS_ATTR = 0.50   # qualité attributaire
POIDS_TOPO = 0.50   # qualité topologique

# -----------------------------------------------------------------------------
#  ACTIONS CORRECTIVES PAR TYPE DE PROBLÈME
#  Dictionnaire associant chaque type d'anomalie à :
#    - une catégorie : "Terrain" (visite physique) ou "Carto" (bureau)
#    - une action corrective : description de ce qu'il faut faire
#
#  Ce dictionnaire est utilisé dans main.py pour :
#    1. Remplir les champs action_corrective et categorie_action dans les GeoPackages
#    2. Construire la section 5 du rapport (actions terrain / actions carto)
#    3. Calculer le nombre d'ouvrages à visiter (catégorie Terrain uniquement)
#
#  Pour ajouter un nouveau type de problème : ajouter une ligne ici.
#  NE PAS modifier les clés existantes — elles sont référencées dans le code.
# -----------------------------------------------------------------------------
ACTIONS_CORRECTIVES = {
    # --- Actions terrain : nécessitent une visite physique sur le terrain ---

    # Topologiques
    "noeud_non_raccorde":      ("Terrain", "Vérifier le raccordement sur le terrain"),
    "troncon_ext_libre":       ("Terrain", "Vérifier la continuité du réseau sur le terrain"),
    "noeud_milieu_troncon":    ("Terrain", "Vérifier le découpage du tronçon sur le terrain"),

    # Altimétriques
    "cote_tn_manquante":       ("Terrain", "Réaliser un relevé altimétrique terrain (TN)"),
    "cote_rad_manquante":      ("Terrain", "Réaliser un relevé altimétrique terrain (radier)"),
    "cote_tn_inf_rad":         ("Terrain", "Contrôler et corriger les cotes par relevé terrain"),
    "cote_tn_zero":            ("Terrain", "Vérifier et relever la cote terrain naturel"),

    # Dimensionnels
    "diametre_absent":         ("Terrain", "Mesurer le diamètre sur le terrain"),
    "hauteur_absente_fosse":   ("Terrain", "Mesurer la hauteur du fossé sur le terrain"),
    "diametre_regard_absent":  ("Terrain", "Mesurer le diamètre du regard sur le terrain"),

    # Identification
    "type_non_renseigne":      ("Terrain", "Identifier le type d'ouvrage depuis plan ou terrain"),
    "info_non_attendue":       ("Carto",   "Supprimer la valeur dans la table attributaire"),
    "classe_absente":          ("Carto",   "Ajouter le champ classe dans la table attributaire"),
    "classe_non_renseignee":   ("Carto",   "Compléter les classes de précision dans la table attributaire"),

    # --- Actions carto : corrigibles au bureau sans visite terrain ---

    # Caractères
    "caracteres_speciaux":     ("Carto", "Corriger les caractères spéciaux dans la table attributaire"),

    # Identification
    "identifiant_non_conforme":("Carto", "Renommer l'identifiant dans la table attributaire"),

    # Matériau
    "materiau_incoherent":     ("Carto", "Vérifier et corriger le matériau au bureau"),
}
