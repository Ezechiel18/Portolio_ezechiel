### AMETOVENA Ezéchiel
##DAte: 05 NOV 2025
### Objet :Repérer le lieu-dit le plus culminant par  commune.
## ETAPE 1: Importation du module

import arcpy #Import du module arcgis pour python

#ETAPE 2 configuration del'environement de travail

arcpy.env.overwriteOutput = True #Autorise le réenregistrement de la couche
arcpy.env.workspace = "H:/M2_Avignon/Cours/Pratique_SIG/S5/data/EXERCICE_1/DATA" #Indique l'espace de travail - le chemin

#ETAPE 3: Analayser la projection  des rasters  et definir  si necessaire : regrouper les dalles; raster

Liste_raster = arcpy.ListRasters('*asc')  # crée une liste pour regrouper tous les fichiers rasters concerné par l'exercice, point asc dans ce cas
Projection = 'PROJECTION.prj' #Crée une variable pour le fichier contenant la projection des rasters
Target = 'TARGET.asc' #Cré une variable pour indiquer l'endroit d'enregistement du resulat de la daille unique des rasters

for raster in Liste_raster:  #Pour chaque fichier  de la liste des rasters 
    if arcpy.Describe(raster).spatialReference.name == 'Unknown': # Condition si le système de coordonnées est inconnu
        
        arcpy.management.DefineProjection(raster,Projection) ##definir le syutème de projection idéal pour les raster 
Raster_altitude = arcpy.management.Mosaic(Liste_raster,Target) ## Crée une mosaique des rasters.
    

##ETAPE 4: Création  d'une couche  par commune sur la zone d'étude; Vecteur
Communes = 'COMMUNE.SHP' #Création de la varibale pour commune
Liste_code_insee = [] #Création de la liste pour le code insee
Liste_communes =[]
with arcpy.da.SearchCursor(Communes, 'CODE_INSEE') as cursor:
    for row in cursor:
        Liste_code_insee.extend(row)
for code_insee in Liste_code_insee:
    Expression = "CODE_INSEE = '{0}'".format(code_insee)
    Nom_sortie = "Commune_{0}.shp".format(code_insee)
    output = arcpy.analysis.Select(Communes,Nom_sortie,Expression)
    Liste_communes.extend(output)
    

##ETAPE 5 : Sélectinner les lieux-dits dans chacune des communes, Vecteur
Liste_communes_bis = arcpy.ListFeatureClasses('Commune_*')
Lieu_dit = "LIEU_DIT_HABITE.SHP"

for commune in Liste_communes_bis:
    Nom_sortie = "Lieu_ditnv_{0}.shp".format(commune)
    output = arcpy.management.SelectLayerByLocation(Lieu_dit,'WITHIN',commune)
    arcpy.management.CopyFeatures(output,Nom_sortie)


##ETAPE 6 : extraire les valeurs d'altitude dans les lieux-dits; Raster et vecteur

Liste_lieudit =  arcpy.ListFeatureClasses ('Lieu_ditnv_*')
for lieux in Liste_lieudit:
    Nom_sortie = "Altitude_Lieux_dits_{0}.shp".format(lieux)
    arcpy.sa.ExtractValuesToPoints(lieux, Target, Nom_sortie)

##ETAPE 7: Sélectionner et exporter les lieux-dits qui ont la valeur maximale; Vecteur
Liste_lieux_dits = arcpy.ListFeatureClasses('Altitude_*shp') # Permet de créer une liste des fichiers qui débutent par altitude et terminent par shp

for lieux_altitude in Liste_lieux_dits : # Boucle : permet d'iterer les operations suivantes pour chaque lieux-dits de la liste.

    Nom_sortie_2 = Nom_sortie[:-4] + '_table.txt' # Permet de supprimer le type de fichier (.shp) du nom de la couche et configurer le nouveau nom

    arcpy.analysis.Statistics(lieux_altitude, Nom_sortie_2, "RASTERVALU MAX","NOM_1") # Pour realiser une analyse statistique : le code permet ici de selectionner la ville qui a la valeur maximale d'altitude dans chaque commune et de garder dans une colonne le nom de la commune

Liste_altitude_max = arcpy.ListTables('*_table.txt')

arcpy.management.Merge(Liste_altitude_max, 'TABLE_FINALE_t.dbf') # Permet de regrouper les tables en une seule table finale qui indique donc, pour chaque commune, l'altitude de la ville la plus elevee
