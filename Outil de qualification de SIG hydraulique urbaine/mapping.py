# =============================================================================
#  mapping.py — Correspondance des champs client ↔ contrôles qualité
#
#  CE FICHIER EST LE SEUL À MODIFIER POUR CHAQUE NOUVEAU PROJET CLIENT.
#
#  COMMENT L'UTILISER :
#  --------------------
#  Pour chaque champ clé du modèle de données SCE, renseigner le nom exact
#  du champ tel qu'il apparaît dans les données du client.
#
#  Exemple :
#    Le modèle SCE attend un "Diamètre (mm)".
#    Le client l'appelle "diam2" dans son shapefile.
#    → Écrire : "nom_client": "diam2"
#
#  Le rapport affichera toujours le LABEL (nom lisible en français),
#  jamais le nom technique interne ni le nom du client.
#
#  Si le client n'a pas fourni un champ → laisser "nom_client": None
#  Le champ apparaîtra en rouge dans le rapport avec la mention "Absent".
#
#  CHAMPS CLÉS RETENUS :
#  Pour le tronçon : type_troncon, forme, diametre, hauteur, materiau
#  Pour le nœud    : id, type_noeud, cote_tn, cote_rad,
#                    diametre_regard
#
#  CONTRAINTES CONDITIONNELLES TRONÇON (gérées dans quality_attributaire.py) :
#  - Si type = branchement / raccordement / canalisation
#      → diametre OBLIGATOIRE
#      → materiau ≠ herbe
#  - Si type = fossé
#      → hauteur OBLIGATOIRE
#      → materiau = herbe
#  - Sinon → pas de contrainte sur diametre, hauteur, materiau
#  Les champs nuls dans les cas non obligatoires ne comptent PAS dans la
#  complétude — le dénominateur s'adapte selon le type.
# =============================================================================


# -----------------------------------------------------------------------------
#  TRONÇON — Correspondance champs client ↔ modèle SCE
#
#  Structure de chaque entrée :
#    "cle_interne": {
#        "nom_client" : "NomExactDansLeShapefile",  ← SEULE CHOSE À MODIFIER
#        "label"      : "Nom affiché dans le rapport",
#        "controle"   : "type_de_controle",          ← NE PAS MODIFIER
#        "description": "Explication de la règle",   ← NE PAS MODIFIER
#    }
# -----------------------------------------------------------------------------
CHAMPS_TRONCON = {

    # Type de tronçon — contrôle texte (pas de caractères spéciaux)
    # On ne vérifie PAS que la valeur est dans notre liste interne.
    # La donnée client peut avoir ses propres libellés — c'est acceptable.
    # Ce champ pilote les contraintes conditionnelles sur diametre, hauteur,
    # materiau (voir quality_attributaire.py).
    "type_troncon": {
        "nom_client" : "TypeTronco",   # ← Remplacer par le nom exact dans les données client
        "label"      : "Type de tronçon",
        "controle"   : "texte",
        "description": "Champ texte. Pas de caractères spéciaux ni accents.",
    },

    # Forme de section — contrôle texte
    "forme": {
        "nom_client" : "FormSect",     # ← Remplacer par le nom exact dans les données client
        "label"      : "Forme de section",
        "controle"   : "texte",
        "description": "Champ texte. Pas de caractères spéciaux ni accents.",
    },

    # Diamètre tronçon — contrôle numérique
    # Obligatoire uniquement si type = branchement / raccordement / canalisation
    # Multiple de 25 (V8 — était 50 en V7)
    "diametre": {
        "nom_client" : "Diametre",     # ← Remplacer par le nom exact dans les données client
        "label"      : "Diamètre (mm)",
        "controle"   : "numerique",
        "min"        : 1,
        "multiple_of": 25,             # multiple de 25 (pas 50)
        "warn_zero"  : True,           # signaler diamètre = 0 sans bloquer
        "description": "Doit être un nombre > 0 et multiple de 25.",
    },

    # Hauteur — contrôle numérique
    # Obligatoire uniquement si type = fossé
    "hauteur": {
        "nom_client" : "Hauteur",      # ← Remplacer par le nom exact dans les données client
        "label"      : "Hauteur (m)",
        "controle"   : "numerique",
        "min"        : 0.001,
        "description": "Doit être un nombre > 0. Obligatoire uniquement pour les fossés.",
    },

    # Classe de précision géographique — contrôle texte
    # Indique la précision du levé (A = meilleure, B, C = moins précis)
    # Champ optionnel — si absent, s'affiche avec 100% vide en 2.3
    # et des tirets en 4.3
    "classe": {
        "nom_client" : None,           # ← Remplacer par le nom exact si disponible
        "label"      : "Classe de précision",
        "controle"   : "texte",
        "description": "Classe de précision géographique du levé (A, B, C...).",
    },

    # Matériau — contrôle texte
    # Règle conditionnelle :
    #   - fossé     → matériau doit être "herbe" (ou équivalent client)
    #   - canalisation → matériau ne doit PAS être "herbe"
    #   - autres    → pas de contrainte
    "materiau": {
        "nom_client" : "Materiau",     # ← Remplacer par le nom exact dans les données client
        "label"      : "Matériau",
        "controle"   : "texte",
        "description": "Champ texte. Pas de caractères spéciaux ni accents.",
    },
}

# -----------------------------------------------------------------------------
#  TYPES DE TRONÇON — Valeurs client correspondant aux catégories SCE
#  Ces listes permettent d'appliquer les contraintes conditionnelles.
#  MODIFIER selon les valeurs réelles dans les données du client.
# -----------------------------------------------------------------------------

# Valeurs client signifiant "branchement", "raccordement" ou "canalisation"
# → diamètre OBLIGATOIRE, matériau ≠ herbe
TYPES_AVEC_DIAMETRE = [
    "Canalisation", "canalisation", "CANALISATION",
    "Branchement",  "branchement",  "BRANCHEMENT",
    "Raccordement", "raccordement", "RACCORDEMENT",
    "Refoulement",  "refoulement",  "REFOULEMENT",
]

# Valeurs client signifiant "fossé"
# → hauteur OBLIGATOIRE, matériau = herbe
TYPES_FOSSE = [
    "Fossé", "fosse", "FOSSE", "Fosse",
]

# Valeur client signifiant "herbe" pour le matériau
# Modifier selon le libellé réel dans les données client
MATERIAU_HERBE = ["Herbe", "herbe", "HERBE", "Enherbe", "enherbe"]


# -----------------------------------------------------------------------------
#  NŒUD — Correspondance champs client ↔ modèle SCE
# -----------------------------------------------------------------------------
CHAMPS_NOEUD = {

    # Identifiant nœud — contrôle "mixte"
    # Accepte à la fois les entiers purs (ex: 1042) et les chaînes
    # alphanumériques (ex: "ND-042"). Refuse les caractères spéciaux.
    "id": {
        "nom_client" : "IDTOPO",       # ← Remplacer par le nom exact dans les données client
        "label"      : "Identifiant du nœud",
        "controle"   : "mixte",        # Integer OU texte alphanumérique — pas de caractères spéciaux
        "description": "Entier ou texte alphanumérique. Pas de caractères spéciaux ni accents.",
    },

    # Type de nœud — contrôle texte
    "type_noeud": {
        "nom_client" : "TypeNoeud",    # ← Remplacer par le nom exact dans les données client
        "label"      : "Type de nœud",
        "controle"   : "texte",
        "description": "Champ texte. Pas de caractères spéciaux ni accents.",
    },

    # Cote terrain naturel — contrôle numérique
    # Ne doit pas être strictement égal à 0 (voir quality_attributaire.py)
    # Doit être supérieur à la cote radier (contrôle de cohérence inter-champs)
    "cote_tn": {
        "nom_client" : "z_tn",         # ← Remplacer par le nom exact dans les données client
        "label"      : "Cote terrain naturel (m NGF)",
        "controle"   : "numerique",
        "min"        : -10,
        "max"        : 500,
        "warn_zero"  : True,           # cote TN = 0 est suspect — signaler sans bloquer
        "description": "Nombre réel entre -10 et 500 m NGF. Ne doit pas être = 0.",
    },

    # Cote radier — contrôle numérique
    # Doit être inférieur à la cote TN (contrôle dans quality_attributaire.py)
    "cote_rad": {
        "nom_client" : "z_rad",        # ← Remplacer par le nom exact dans les données client
        "label"      : "Cote radier (m NGF)",
        "controle"   : "numerique",
        "min"        : -10,
        "max"        : 500,
        "description": "Nombre réel entre -10 et 500 m NGF. Doit être < cote TN.",
    },

    # Classe de précision géographique — contrôle texte
    # Même logique que pour le tronçon
    "classe": {
        "nom_client" : None,           # ← Remplacer par le nom exact si disponible
        "label"      : "Classe de précision",
        "controle"   : "texte",
        "description": "Classe de précision géographique du levé (A, B, C...).",
    },

    # Diamètre regard — contrôle numérique conditionnel
    # Applicable UNIQUEMENT aux nœuds de type "regard"
    # Si le client n'a pas ce champ → laisser "nom_client": None
    # Minimum 600 mm, multiple de 100
    "diametre_regard": {
        "nom_client" : None,           # ← Remplacer par le nom exact si disponible chez le client
        "label"      : "Diamètre regard (mm)",
        "controle"   : "numerique",
        "min"        : 600,            # diamètre minimum pour un regard
        "multiple_of": 100,            # multiple de 100 (pas 25 ni 50)
        "description": "Applicable uniquement aux nœuds de type regard. Min 600 mm, multiple de 100.",
        "conditionnel_type": "regard", # ce champ n'est contrôlé que si type_noeud = regard
    },
}

# -----------------------------------------------------------------------------
#  VALEURS CLIENT POUR LES TYPES DE NŒUD
#  Modifier selon les valeurs réelles dans les données du client.
# -----------------------------------------------------------------------------

# Valeurs client signifiant "regard"
# → diamètre regard obligatoire (min 600, multiple de 100)
TYPES_REGARD = [
    "Regard", "regard", "REGARD",
    "Regard de visite", "regard de visite",
]


# -----------------------------------------------------------------------------
#  NORMALISATION DES CLASSES DE PRÉCISION
#  Ramène toutes les variantes d'écriture à une lettre majuscule.
#  Exhaustif — couvre minuscules, doublons, espaces, préfixes "classe".
# -----------------------------------------------------------------------------
CLASSE_NORMALISATION = {
    # Classe A
    "a": "A", "aa": "A", "a ": "A", " a": "A",
    "classe a": "A", "classe_a": "A", "class a": "A",
    "a1": "A", "a2": "A",
    # Classe B
    "b": "B", "bb": "B", "b ": "B", " b": "B",
    "classe b": "B", "classe_b": "B", "class b": "B",
    "b1": "B", "b2": "B",
    # Classe C
    "c": "C", "cc": "C", "c ": "C", " c": "C",
    "classe c": "C", "classe_c": "C", "class c": "C",
    "c1": "C", "c2": "C",
    # Classe D (au cas où)
    "d": "D", "dd": "D", "d ": "D", " d": "D",
    "classe d": "D", "classe_d": "D",
}


def normaliser_classe(valeur):
    """
    Normalise une valeur de classe de précision.
    Retourne la lettre majuscule correspondante ou None si non reconnue.
    Exemples : "a" → "A", "Classe B" → "B", "bb" → "B", "B1" → "B"
    """
    if valeur is None:
        return None
    v = str(valeur).strip().lower()
    # Correspondance directe dans le dictionnaire
    if v in CLASSE_NORMALISATION:
        return CLASSE_NORMALISATION[v]
    # Si la valeur commence par une lettre connue (ex: "A3", "B_levé")
    if len(v) >= 1 and v[0] in ["a", "b", "c", "d"]:
        return v[0].upper()
    return None
