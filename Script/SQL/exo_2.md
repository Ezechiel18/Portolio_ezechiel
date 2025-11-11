L’idlogement des logements dans lesquels la famille FLATTOT a vécu.

```
SELECT o.idlogement
FROM occupation AS o
JOIN menage AS m ON o.idmenage = m.idmenage
WHERE nom = 'FLATTOT';
```

Le nombre d’intervention de chaque type.

```
SELECT type, COUNT (*) AS nb_interv
FROM intervention
GROUP BY type
```

La somme des surfaces des logement pour chaque batiment.

```
SELECT SUM (surface) AS sum_sup
FROM logement AS l
JOIN batiment AS b ON b.idbatiment = l.batiment
GROUP BY batiment
```

Le nombre d’interventions réalisées par chaque entreprise.

```
SELECT siren,COUNT (*)
FROM intervention
GROUP BY siren
```

Le montant des travaux pour chaque logement.

```
SELECT idlogement, SUM (prix) AS montant_logement
FROM intervention
GROUP BY idlogement
```

Le bâtiment qui a fait l’objet du plus d’intervention.

```
SELECT idbatiment, COUNT (idintervention) AS nb_inter_bat
FROM intervention AS i
JOIN logement AS l ON l.idlogement = i.idlogement
JOIN batiment AS b ON b.idbatiment = l.batiment
GROUP BY idbatiment
ORDER BY nb_inter_bat DESC
LIMIT 1
```

Le nombre de résidents par commune en 2015.

```
SELECT b.commune, SUM (m.nb_pers) AS nb_tot
FROM menage AS m
JOIN occupation AS o ON o.idmenage = m.idmenage
JOIN logement AS l ON l.idlogement = o.idlogement
JOIN batiment AS b ON b.idbatiment = l.batiment
WHERE debut <= 2015 AND fin >= 2015
GROUP BY b.commune
```

Le nombre de logements dans lesquels les différentes familles ont vécu, en les classant par ordre décroissant

```
SELECT m.nom, COUNT (l.idlogement) AS nb_log_fam
FROM logement AS l
JOIN occupation AS o ON o.idlogement = l.idlogement
JOIN menage AS m ON m.idmenage = o.idmenage
GROUP BY m.nom
ORDER BY nb_log_fam DESC
```

L’adresse de chaque ménage présent dans le parc du bailleur en 2022.

```
SELECT b.adresse, m.nom
FROM batiment AS b
JOIN logement AS l ON l.batiment = b.idbatiment
JOIN occupation AS o ON o.idlogement = l.idlogement
JOIN menage AS m ON m.idmenage = o.idmenage
WHERE o.debut <= 2022 AND o.fin >= 2022
```

La date d’emménagement et l’adresse des MUNHOVEN pour chaque logement qu’ils ont occupé

```
SELECT o.debut, b.adresse, m.nom
FROM batiment AS b
JOIN logement AS l ON l.batiment = b.idbatiment
JOIN occupation AS o ON o.idlogement = l.idlogement
JOIN menage AS m ON m.idmenage = o.idmenage
WHERE m.nom = 'MUNHOVEN'
```

Les logements vides en 2022

```
SELECT l.idlogement
FROM logement AS l
LEFT JOIN occupation AS o
ON o.idlogement = l.idlogement
AND o.debut <=2022
AND o.fin >=2022
WHERE o.idlogement IS NULL;

---- ou
```
