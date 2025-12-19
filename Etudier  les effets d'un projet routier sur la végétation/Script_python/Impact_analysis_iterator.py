# Titre : Etudier les effets d'un projet routier sur la végétation
# Ezéchiel AMETOVENA
# Date de création : 08//10//2025
# Date de MAJ : 15//10//2025

#### ETAPE 1. Configurer l'env ###

import arcpy

arcpy.env.overwriteOutput = True
arcpy.env.workspace = "H:/M2_Avignon/Cours/Pratique_SIG/Projet/Seance_4/data2"

#  ETAPE 2 BOUCLE FOR
projet_route = ["PlanA_Roads.shp", "PlanB_Roads.shp", "PlanC_Roads.shp"]
vegetype = "Vegtype.shp"

for couche in projet_route:
    Name_couche = couche [:-4]
    for distance in range (100, 501, 100):
        OutputName = "{0}Roads_Buffer_{1}".format(Name_couche,distance)
        Value_dist = "{0} Meters".format(distance)
        arcpy.analysis.Buffer (couche,OutputName,Value_dist)







