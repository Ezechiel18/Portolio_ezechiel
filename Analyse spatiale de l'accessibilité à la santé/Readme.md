# Accessibilité à la santé au Togo

Analyse spatiale de la couverture sanitaire par commune

## Objectif

Estimation de l'accessibilité géographique, démographique et financière aux établissements de santé, à l'échelle des 117 communes togolaises. Traitement ArcGIS Pro, publication prévue sur ArcGIS Online. Carte web interactive en cours de développement.

## Données

- Établissements de santé : 2271 points, attributs `etablissement_type`, `secteur`
- Communes : 117 polygones, `commune_id`
- Population : RGPH5, INSEED 2023, jointe par `commune_id`
- Bâti : OSM

## Norme de référence

Rayon de 5 km, PMPP 2021 (Banque mondiale, P174266)

## Chaîne de géotraitement

### 1. Buffer (Analyse > Proximité)

Entrée : établissements de santé. Distance : 5 km. Dissolution : NONE.

### 2. Sélection par localisation (bâti ∩ buffer) puis Calculate Field

```
acces_dis = "oui" si intersection, "non" sinon
```

### 3. Spatial Join (bâti vers commune)

Type de correspondance : INTERSECT. Ajoute `commune_id` à chaque bâtiment.

### 4. Summary Statistics

COUNT, champ de cas `commune_id`, exécuté séparément sur sélection `acces_dis = 'oui'` et `acces_dis = 'non'`.
Sortie : `bati_oui`, `bati_non` par commune.

### 5. Join Field

Retour sur couche commune, clé `commune_id`.

### 6. Calculate Field  nettoyage des nulls

```python
def nettoyer(val):
    if val is None:
        return 0
    return val
```

### 7. Calculate Field  estimation dasymétrique

```
pop_couvert = population * (bati_oui / (bati_oui + bati_non))
pop_non_couvert = population - pop_couvert
taux_couverture_pct = (bati_oui / (bati_oui + bati_non)) * 100
```

Sécurité division par zéro si `bati_oui + bati_non = 0` : retour 0.

### 8. Spatial Join (établissements de santé vers commune)

Clé `commune_id`.

### 9. Calculate Field — classification sectorielle

```python
def classer(s):
    if s == "Public" or s == "Public/Communautaire":
        return "Public"
    return "Prive elargi"
```

### 10. Summary Statistics

COUNT par `commune_id`, séparé sur `secteur_simplifie = 'Public'` et `'Prive elargi'`.
Sortie : `etab_public`, `etab_prive`.

### 11. Join Field

Retour sur couche commune.

### 12. Calculate Field  proxy financier

```python
def pct_public(pub, priv):
    total = pub + priv
    if total == 0:
        return None
    return (pub / total) * 100

def classer_fin(pub, priv):
    total = pub + priv
    if total == 0:
        return "Non renseigne"
    pct = (pub / total) * 100
    return "Favorable" if pct >= 50 else "Defavorable"
```

### 13. Calculate Field  classes de lecture cartographique

4 classes égales, pas de 25 points.

```python
def classer_couverture(taux):
    if taux is None:
        return "Non renseigne"
    if taux < 25:
        return "Tres peu couvert (0-25%)"
    if taux < 50:
        return "Peu couvert (25-50%)"
    if taux < 75:
        return "Couverture moyenne (50-75%)"
    return "Bien couvert (75-100%)"
```

Logique identique pour `classe_public` sur `pct_pub`.

### 14. Calculate Field indicateur composite de priorité

```python
def priorite(taux_couv, fin):
    if taux_couv is None or fin == "Non renseigne":
        return "Non renseigne"
    if taux_couv < 50 and fin == "Defavorable":
        return "Priorite haute"
    if taux_couv < 50 or fin == "Defavorable":
        return "Priorite moderee"
    return "Priorite faible"
```

## Limites

- Buffer euclidien, non un temps de trajet réseau
- Rayon uniforme sur tous les niveaux de la pyramide sanitaire, non différencié par type d'établissement
- Dasymétrie à pondération uniforme par bâtiment, sans variable de surface ou de typologie
- Proxy financier disponible à l'échelle communale uniquement, non désagrégeable au bâtiment
- Couverture du bâti potentiellement incomplète en zone rurale (OpenStreetMap)
