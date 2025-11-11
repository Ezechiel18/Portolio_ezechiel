Afficher le nom des ménages.

```
SELECT nom
FROM menage
```

Le nombre d’interventions.

```
SELECT COUNT(*) 
FROM intervention
```

```Afficher
SELECT lower (nom), nb_pers
FROM menage WHERE nb_pers > 4
```

Les départements dans lesquels se trouvent les bâtiments (à l’aide des deux premiers caractères de
 l’attribut commune).

```
SELECT DISTINCT LEFT (commune,2)
FROM  batiment
```

Les différents types d’intervention

```
SELECT DISTINCT type
FROM intervention
```

La somme des surfaces concernées par des interventions.

```
SELECT SUM (surface_cons)
FROM intervention
```

Les interventions dont le montant est inférieur à 300 € et qui ne sont pas de la plomberie

```
SELECT prix
FROM intervention WHERE prix < 300 AND type != 'plomberie'
```

Les logements dans lesquels le ménage correspondant à l’idmenage 1 a vécu.

```
SELECT idlogement
FROM occupation
WHERE idmenage = 1
```

Les idmenage des ménages présents dans le parc en 2018.

```
 SELECT * 
FROM occupation
WHERE debut <= 2018 
AND fin >=2018

SELECT *
FROM occupation
WHERE 2018 BETWEEN debut AND fin
```

L’année où sont arrivés les premiers ménages dans le parc.

```
SELECT MIN (debut)
FROM occupation
```

Les ménages arrivés en 2013.

```
SELECT idmenage
FROM occupation WHERE debut = 2013
```

En vous aidant des deux réponses précédentes, essayez de trouver comment afficher l’idmenage des
 ménages arrivés la première année des données en imbriquant les deux requêtes.

```

```
