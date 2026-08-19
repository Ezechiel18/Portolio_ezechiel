# Qualification du SIG sur les réseau d'eau pluviale et usées
## Documentation complète - V22

---

## Objectif du projet

Ce projet génère automatiquement un rapport de qualification des données SIG
à partir de deux couches hydrauliques (tronçons et nœuds). Il produit :

- Un rapport **HTML** (mise en page fidèle, ouvrable dans Chrome)
- Un rapport **PDF** (une page A4 paysage)
- Un fichier **PowerPoint** éditable (pour ajustements manuels)
- Les couches **GeoPackage enrichies** avec les champs de qualification
La démarche à consister à échanger avec les chefs projets, les responsables de domaines, de pôles et les directeurs de département afin de construire les indicateurs de qualifications du SIG conformément à la règlementation dans le secteur. Il s'agit donc d'un outil sur mesure pour la qualification de données. 
---

## Structure du projet

```
rapport_qualite/
│
├── config.py            ← Chemins, infos projet, logo SCE  [À MODIFIER EN REUTILISATION]
├── mapping.py           ← Correspondance champs client      [À MODIFIER EN REUTILISATION]
├── main.py              ← Point d'entrée — lancer ce fichier
├── environment.yml      ← Environnement conda
│
├── analysis/
│   ├── quality_attributaire.py   ← Contrôles typage et caractères spéciaux
│   └── quality_spatiale.py       ← Contrôles connectivité topologique
│
├── viz/
│   ├── charts.py        ← Graphiques (jauges, donuts, barres)
│   └── maps.py          ← Cartes avec fond OpenStreetMap
│
├── templates/
│   └── report.html      ← Template Jinja2 du rapport
│
└── output/              ← Généré automatiquement à l'exécution
    ├── charts/          ← Graphiques PNG intermédiaires
    ├── maps/            ← Cartes PNG intermédiaires
    ├── report_debug.html
    ├── Rapport_qualif_YYYYMMDD_HHMM.pdf
    ├── Rapport_qualif_YYYYMMDD_HHMM.pptx
    ├── Troncon_qualif.gpkg
    └── Noeud_qualif.gpkg
```

---

## Réutilisation-installation pour une première fois

### Étape 1-Télécharger et décompresser le projet (ensemble du script)

Placer le dossier `rapport_qualite/` à l'emplacement de votre choix.
Exemple : `C:\mmmm\rapport_qualite\`

### Étape 2-Créer l'environnement conda

Ouvrir **Anaconda Prompt** et exécuter :

```bash
cd C:\Projet_prediag\rapport_qualite
conda env create -f environment.yml
```

Cette commande crée l'environnement `qual_env` avec toutes les dépendances.
Ne faire cette étape **qu'une seule fois**.

### Étape 3-Vérifier l'installation

```bash
conda activate qual_env
python -c "import geopandas, contextily, jinja2, pptx; print('OK')"
```

---

## Utilisation-pour chaque nouveau projet

### Étape 1-Ouvrir `config.py` et modifier

```python
# Chemins vers les données du client
DATA_DIR     = r"C:\MonProjet\données"
TRONCON_FILE = os.path.join(DATA_DIR, "Troncon.shp")
NOEUD_FILE   = os.path.join(DATA_DIR, "Noeud.shp")

# Logo SCE (chemin vers le PNG du logo)
LOGO_SCE_PATH = r"C:\logos\logo.png"

# Informations du projet
PROJET_NOM     = "Réseau d'assainissement"
PROJET_COMMUNE = "Nom de la commune"
PROJET_VERSION = "v1.0"
```

### Étape 2-Ouvrir `mapping.py` et renseigner les noms des champs

Pour chaque champ clé, indiquer le nom **exact** tel qu'il apparaît
dans les données du client (vérifier dans QGIS ou avec la commande ci-dessous).

```bash
python -c "import geopandas as gpd; print(list(gpd.read_file('Troncon.shp').columns))"
```

Puis modifier dans `mapping.py` :

```python
CHAMPS_TRONCON = {
    "diametre": {
        "nom_client" : "diam",   # ← nom exact dans les données client
        "label"      : "Diamètre (mm)",
        ...
    },
    ...
}
```

Si un champ est absent des données client, laisser `"nom_client": None`.
Il apparaîtra en rouge dans le rapport.

### Étape 3-Lancer le script

```bash
conda activate qual_env
cd C:\Projet_prediag\rapport_qualite
python main.py
```

Le script affiche sa progression dans le terminal :

```
[1/5] Chargement …
[2/5] Contrôles attributaires …
[3/5] Contrôles topologiques …
[4/5] Graphiques et cartes …
[5/5] Rapport …
  ✓ IFQ = 67%
```

### Étape 4-Récupérer les sorties

Tous les fichiers sont dans le dossier `output/` :

| Fichier | Description |
|---------|-------------|
| `Rapport_qualif_YYYYMMDD_HHMM.pdf` | Rapport PDF une page |
| `Rapport_qualif_YYYYMMDD_HHMM.pptx` | Rapport PowerPoint éditable |
| `report_debug.html` | HTML — ouvrir dans Chrome pour vérifier |
| `Troncon_qualif.gpkg` | Tronçons enrichis avec champs `_qualif` |
| `Noeud_qualif.gpkg` | Nœuds enrichis avec champs `_qualif` |

---

## Comprendre les champs de qualification dans les GeoPackages

### Champs ajoutés aux tronçons

| Champ | Valeurs | Signification |
|-------|---------|---------------|
| `borde_ext1` | oui / non | Extrémité 1 (premier point) reliée à un nœud |
| `borde_ext2` | oui / non | Extrémité 2 (dernier point) reliée à un nœud |
| `statut_delimitation` | deux_cotes / un_cote_seul / non_delimite | Statut global |
| `{cle}_qualif` | oui / non | Conformité de chaque champ mappé |

### Champs ajoutés aux nœuds

| Champ | Valeurs | Signification |
|-------|---------|---------------|
| `connecte` | oui / non | Nœud raccordé à un tronçon |
| `{cle}_qualif` | oui / non | Conformité de chaque champ mappé |

**Règle des champs `_qualif` :**
- `oui` = valeur présente + type correct + pas de caractère spécial
- `non` = valeur absente OU type incorrect OU caractère spécial

---

## Ce que le script vérifie

### Qualité attributaire (sur les champs définis dans `mapping.py`)

- **Champs numériques** : la valeur est-elle un nombre ? Est-elle dans la plage réaliste ? Est-elle multiple du pas attendu (ex: diamètre multiple de 50) ?
- **Champs texte** : contient-elle des caractères spéciaux (`< > & ' " ; / \ | * ? # @ !`) ou des accents qui posent problème dans les SIG ?
- **Complétude** : quel pourcentage de valeurs est réellement renseigné ?

**Important** : le script ne vérifie PAS que les occurrences sont dans la liste interne SCE. La donnée client peut avoir ses propres libellés — c'est acceptable.

### Qualité topologique

- **Nœuds** : chaque nœud est-il à moins de 0.5 m d'une extrémité de tronçon ?
- **Tronçons** : chaque extrémité de tronçon est-elle proche d'un nœud ?
- Tolérance configurable dans `config.py` → `SNAP_TOLERANCE`

---

## HTML sur une seule page

Le meilleur rendu PDF s'obtient via **Chrome** :

1. Ouvrir `output/report_debug.html` dans Chrome
2. `Ctrl+P` → Enregistrer en PDF
3. Paramètres : A4, Paysage, Marges minimales, "Graphiques d'arrière-plan" coché

Ou automatiquement si Chrome est installé : le script le détecte et l'utilise.

---

## Adapter la tolérance topologique

Dans `config.py` :
```python
SNAP_TOLERANCE = 0.5   # mètres — augmenter si les données sont peu précises
```

---

## Ajouter ou retirer des champs à contrôler

Dans `mapping.py`, ajouter une entrée dans `CHAMPS_TRONCON` ou `CHAMPS_NOEUD` :

```python
"nouveau_champ": {
    "nom_client" : "NomDansLeShapefile",
    "label"      : "Nom affiché dans le rapport",
    "controle"   : "numerique",   # ou "texte"
    "min"        : 0,             # si numerique
    "description": "Explication",
},
```

---

