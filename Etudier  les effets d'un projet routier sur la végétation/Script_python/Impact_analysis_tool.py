#Titre: Etudier  les effets d'un projet routier sur la végétation
#Ezechiel AMETOVENA
#Date de création : 08/10/2025
#Date de MAJ: 08/10/2025

##### ETAPE 1 . Configuration  de l'env ##
import arcpy
arcpy.env.overwriteOutput = True


### ETAPE 2. Importer les données ##
Routes = arcpy.GetParametersAsText (0) #Fichier de forme
Vegetations = arcpy.GetParametersAsText (1) #Fichier de forme

#Configurer les paramètres

Distance = arcpy.GetParametersAsText (2) #valeur ou champ
Analyse_statistique = arcpy.GetParametersAsText (3) #Champs
Champ_regroupement = arcpy.GetParametersAsText (4) #Champs


### ETAPE 3 . Configurer les sorties ##

Route_buf = arcpy.GetParametersAsText (5) #Fichier de forme
vegdec = arcpy.GetParametersAsText (6) #Fichier de forme
Tableveg = arcpy.GetParametersAsText (7) #table

##ETAPE 4 . Traitement

arcpy.analysis.Buffer (Routes, Route_buf, Distance)

arcpy.analysis.Clip (Vegetations, Route_buf, vegdec, Analyse_statistique, Champ_regroupement)

arcpy.analysis.Statistics(
    in_table= vegdec,
    out_table= Tableveg,
    statistics_fields="Shape_Area SUM",
    case_field="VEG_TYPE",
    concatenation_separator=""
)
