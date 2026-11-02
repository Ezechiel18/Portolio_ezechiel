# LCZ France : pré-diagnostic de la surchauffe urbaine à la commune

Ce script calcule les **zones climatiques locales** (LCZ, *Local Climate Zones*) d'une commune française, sur une grille régulière de 200 m. Il s'inspire de la méthode du Cerema et l'applique à n'importe quelle commune de France métropolitaine, à partir de données ouvertes de l'IGN.

Le résultat est un **pré-diagnostic** : il indique où la forme urbaine et l'occupation du sol rendent un quartier plus sensible à la surchauffe. Ce n'est pas une carte d'îlot de chaleur mesuré.

## Ce que fait le script

Pour chaque commune demandée, le script :

1. récupère le contour de la commune (BD TOPO, flux WFS de la Géoplateforme) ;
2. construit une grille de mailles de 200 m calée sur le Lambert-93 ;
3. récupère les bâtiments (BD TOPO) et applique le filtre du Cerema ( prise en coimpte des bâtis à hauteur connue et exclusion des bâtis d'au moins 3 m, on garde les bâtiments en service, on exclus les constructions légères) ;
4. lit l'OCS GE du département et la ramène à 6 classes (bâti, route et surface imperméable, sol nu, eau, végétation arborée, végétation herbacée) ;
5. calcule les indicateurs de forme urbaine : hauteur moyenne (HRE) et surface moyenne (ARE) des bâtiments ;
6. calcule les indicateurs d'occupation du sol : BuR, RoR, BsR, WaR, VeR et VHR ;
7. attribue une classe LCZ à chaque maille avec l'arbre de décision du Cerema ;
8. réalise des contrôles qualité et signale les mailles douteuses ;
9. produit les résultats : GeoPackage, cartes, graphique et rapport.

Chaque commune est traitée séparément. Si l'une échoue, le script le signale et passe à la suivante.

## Résultats produits

Un dossier par commune est créé dans `sorties/`, par exemple `sorties/38185-Grenoble/` :

| Fichier | Contenu |
| --- | --- |
| `mailles-lcz.gpkg` | Grille avec la classe LCZ, les indicateurs et les contrôles qualité, à ouvrir dans QGIS |
| `carte-lcz.png` | Carte des classes LCZ |
| `carte-sensibilite.png` | Carte des degrés de sensibilité à l'îlot de chaleur |
| `repartition-lcz.png` | Part de la surface communale occupée par chaque classe |
| `rapport-controles.txt` | Répartition des classes et résultats des contrôles qualité |

## Installation

Le script utilise Python avec les bibliothèques suivantes : numpy, pandas, geopandas, shapely, pyogrio, requests et matplotlib.

Avec conda :

```bash
conda create -n lcz -c conda-forge python geopandas pyogrio requests matplotlib
conda activate lcz
```

## Données à télécharger

La BD TOPO est lue directement en ligne, rien à télécharger.

L'**OCS GE** n'existe pas en flux : il faut télécharger le GeoPackage du département sur le site de l'IGN, puis placer le fichier `OCCUPATION_SOL.gpkg` dans le dossier `data/`, dans un sous-dossier dont le nom contient le code du département sur trois caractères, entouré de tirets bas :

```
data/
└── OCSGE_D038_2024/
    └── OCCUPATION_SOL.gpkg
```

## Utilisation

Placez-vous dans le dossier `script/`, puis :

```bash
# une commune (code INSEE)
python lcz_commune.py 38185

# plusieurs communes
python lcz_commune.py 34023 34172 34129

# toutes les communes d'un département
python lcz_commune.py --departement 34
```

## Contrôles qualité

Le script ne corrige rien en silence. Il marque les mailles concernées dans le GeoPackage :

- `ctrl_somme` : la somme des taux d'occupation du sol s'écarte de plus d'un point de 100 % ;
- `ctrl_bati_sans_bdtopo` : maille bâtie selon l'OCS GE, mais sans bâtiment BD TOPO retenu ;
- `ctrl_vhr_force` : maille sans végétation, dont le taux de végétation arborée a été fixé à 0.

Si l'OCS GE contient un code absent de la table de reclassement, le calcul de la commune s'arrête : aucune zone n'est classée au hasard.

## Limites

- Les résultats dépendent de la qualité et de la date des données IGN. L'OCS GE n'a pas le même millésime partout.
- La grille de 200 m lisse les situations locales : une maille peut mélanger plusieurs types de tissu urbain.
- Il s'agit d'une adaptation personnelle de la méthode du Cerema, pas de la méthode officielle. Les résultats peuvent différer de ceux publiés par le Cerema.

## Sources

- Cerema, guide technique sur les zones climatiques locales.
- IGN, BD TOPO (flux WFS de la Géoplateforme).
- IGN, OCS GE.
- Stewart I. D. et Oke T. R. (2012), *Local Climate Zones for Urban Temperature Studies*, Bulletin of the American Meteorological Society.

## Auteur

Ezéchiel Ametovena, géomaticien.

## Licence

Code sous licence MIT (voir le fichier `LICENSE`). Les données IGN restent soumises à leur propre licence.
