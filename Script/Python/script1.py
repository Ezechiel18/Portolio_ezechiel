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

Liste_lieuditalt = arcpy.ListFeatureClasses('Altitude_Lieux_dits_*')

for lieuditalt in Liste_lieuditalt:
    # Déterminer la valeur d'altitude maximale
    max_alt = -9999
    with arcpy.da.SearchCursor(lieuditalt, ['RASTERVALU']) as cursor:
        for row in cursor:
            if row[0] > max_alt:
                max_alt = row[0]
    
    # Créer l’expression de sélection
    Expression = "RASTERVALU = {0}".format(max_alt)
    
    # Nom de la couche de sortie
    Nom_sortie = "Altitude_Lieux_dits_max_{0}.shp".format(lieuditalt)
    
    # Sélectionner et exporter le lieu-dit le plus élevé
    arcpy.analysis.Select(lieuditalt, Nom_sortie, Expression)
    
########ETAPE 8 : Obtention de la table contenant le lieux dit le plus culminant par commune

# Nom de la table finale
Table_finale = "Lieux_dits_plus_eleve_par_commune.dbf"

# Créer la table vide dans le workspace
arcpy.management.CreateTable(arcpy.env.workspace, Table_finale)

# Ajouter les champs
arcpy.management.AddField(Table_finale, "CODE_INSEE", "TEXT")
arcpy.management.AddField(Table_finale, "NOM_LIEU", "TEXT")
arcpy.management.AddField(Table_finale, "ALTITUDE", "DOUBLE")

# Liste des shapefiles créés à l'étape précédente (un par commune)
Liste_lieudit_max = arcpy.ListFeatureClasses('Altitude_Lieux_dits_max_*')

for couche in Liste_lieudit_max:
    print("Traitement de :", couche)
    
    # Extraire le code INSEE à partir du nom du shapefile
    code_insee = couche.replace("Altitude_Lieux_dits_max_Altitude_Lieux_dits_Commune_", "").replace(".shp", "")
    
    # Lire le lieu-dit et son altitude
    with arcpy.da.SearchCursor(couche, ['NOM', 'RASTERVALU']) as cursor:
        for row in cursor:
            nom_lieu = row[0]
            altitude = row[1]
            
            # Insérer les infos dans la table finale
            with arcpy.da.InsertCursor(Table_finale, ['CODE_INSEE', 'NOM_LIEU', 'ALTITUDE']) as insert_cursor:
                insert_cursor.insertRow((code_insee, nom_lieu, altitude))


    
##il faut qu'on obtienne une table avec une colonne nom de commune, une colone lieu dit et l'altitude.
##mais on souhaite qu'il y a it q'une ligne par commune. genre uniquement le  lieu dit qui a l'altitude le plus elévé par commune.

