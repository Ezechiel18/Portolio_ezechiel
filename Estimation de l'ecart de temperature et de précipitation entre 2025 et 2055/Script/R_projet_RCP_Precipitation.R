# 1. Charger les packages nécessaires
install.packages("sf")
install.packages(c("ncdf4", "raster", "terra", "sf", "exactextractr"))
library(ncdf4)
library(raster)
library(terra)
library(sf)
library(exactextractr)  # très utile pour l’extraction zonale
library(terra)    # pour manipuler les rasters et NetCDF
library(sf)       # pour le vecteur (GeoPackage)
library(ncdf4)    # pour inspecter les variables du NetCDF

# 2. Charger la limite administrative depuis le GeoPackage
limite <- st_read("I:/Memoire/SIG/Rendu_Ceres_Flore/Data/GPK/region_interet_2154.gpkg")

# 3. Charger une variable du NetCDF via terra (sans tout lire)
nc_path <- "I:/Memoire/SIG/Rendu_Ceres_Flore/Data/Enrichissement/Bias_jour_35_mois/tx35ba_CMIP6_ssp585_mon_201501-210012.nc"
raster_brick <- rast(nc_path, subds = "tx35ba")  # ou nom exact de la variable dans le fichie .nc

# 4. Reprojeter la limite si nécessaire
limite <- st_transform(limite, crs(raster_brick))  # maintenant les deux couches ont le même CRS

# 5. Convertir le vecteur sf en SpatVector (terra)
limite_vect <- vect(limite)

# 6. Découper la zone d’étude
raster_crop <- crop(raster_brick, limite_vect)
raster_mask <- mask(raster_crop, limite_vect)

# 7. Extraire les dates de la couche temporelle
dates <- terra::time(raster_mask)
years <- format(dates, "%Y")
indices_2025 <- which(years == "2025")
indices_2055 <- which(years == "2055")

# 8. Extraire les couches correspondant aux années ciblées
raster_2025 <- raster_mask[[indices_2025]]
raster_2055 <- raster_mask[[indices_2055]]

# 9. (optionnel) Moyenne annuelle
pr_2025_mean <- mean(raster_2025)
pr_2055_mean <- mean(raster_2055)

# 10. (optionnel) Visualiser
plot(pr_2025_mean, main = "Précipitations moyennes 2025")
plot(pr_2055_mean, main = "Précipitations moyennes 2055")
# 11. Exporter les résultats dans un dossier
writeRaster(pr_2025_mean,
            filename = "I:/Memoire/SIG/Rendu_Ceres_Flore/R/Export/pr_2025_mean.tif",
            overwrite = TRUE)

writeRaster(pr_2055_mean,
            filename = "I:/Memoire/SIG/Rendu_Ceres_Flore/R/Export/pr_2055_mean.tif",
            overwrite = TRUE)

# 12. Arrondir les valeurs à 1 chiffre après la virgule (facultatif mais utile pour regrouper les valeurs proches)
pr_2025_mean_round <- round(pr_2025_mean, 1)
pr_2055_mean_round <- round(pr_2055_mean, 1)

# 13. Vectoriser les rasters moyens (avec fusion des polygones par valeur arrondie)
vect_2025 <- as.polygons(pr_2025_mean_round, na.rm = TRUE, dissolve = TRUE)
vect_2055 <- as.polygons(pr_2055_mean_round, na.rm = TRUE, dissolve = TRUE)

# 14. Vérifier / réassigner le système de coordonnées
crs(vect_2025) <- crs(pr_2025_mean)
crs(vect_2055) <- crs(pr_2055_mean)

# 15. Exporter en GeoPackage
writeVector(vect_2025,
            filename = "I:/Memoire/SIG/Rendu_Ceres_Flore/R/Export/pr_2025_vector.gpkg",
            layer = "precip_2025",
            filetype = "GPKG",
            overwrite = TRUE)

writeVector(vect_2055,
            filename = "I:/Memoire/SIG/Rendu_Ceres_Flore/R/Export/pr_2055_vector.gpkg",
            layer = "precip_2055",
            filetype = "GPKG",
            overwrite = TRUE)
