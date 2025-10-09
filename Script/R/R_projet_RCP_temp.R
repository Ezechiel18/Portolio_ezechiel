# 1. Charger les packages nécessaires
install.packages(c("ncdf4", "raster", "terra", "sf", "exactextractr"))
install.packages("geosphere")

library(ncdf4)
library(raster)
library(terra)
library(sf)
library(exactextractr)
library(geosphere)

# 2. Charger la limite administrative depuis le GeoPackage
limite <- st_read("I:/Memoire/SIG/Rendu_Ceres_Flore/Data/GPK/region_interet_2154.gpkg")

# 3. Spécifier le chemin du fichier NetCDF
nc_path <- "I:/Memoire/SIG/Rendu_Ceres_Flore/Data/Enrichissement/RCP_85_temperature/t_CMIP5_rcp85_mon_200601-210012.nc"

# 4. Explorer le contenu du fichier NetCDF avec ncdf4
nc <- nc_open(nc_path)
print(nc)  # Affiche les métadonnées du fichier
ncatt_get(nc, varid = "t")  # Affiche les attributs de la variable 't'
nc_close(nc)

# À ce stade, regarde si l'unité est "K" (Kelvin). Si oui, il faudra convertir en °C (°C = K - 273.15)

# 5. Charger la variable 'tas' via terra (sans tout lire)
raster_brick <- rast(nc_path, subds = "t")

# 6. Harmoniser les systèmes de coordonnées
limite <- st_transform(limite, crs(raster_brick))

# 7. Convertir le vecteur sf en SpatVector (terra)
limite_vect <- vect(limite)

# 8. Découper la zone d’étude
raster_crop <- crop(raster_brick, limite_vect)
raster_mask <- mask(raster_crop, limite_vect)

# 9. Extraire les dates de la couche temporelle
dates <- terra::time(raster_mask)
years <- format(dates, "%Y")
indices_2025 <- which(years == "2025")
indices_2055 <- which(years == "2055")

# 10. Extraire les couches correspondant aux années ciblées
raster_2025 <- raster_mask[[indices_2025]]
raster_2055 <- raster_mask[[indices_2055]]

# 11. Moyenne annuelle
t_2025_mean <- mean(raster_2025)
t_2055_mean <- mean(raster_2055)

# 12. Convertir en °C si les données sont en Kelvin
t_2025_mean_c <- tas_2025_mean - 273.15
t_2055_mean_c <- tas_2055_mean - 273.15

# 13. Visualiser
plot(t_2025_mean, main = "Température moyenne 2025 (°C)")
plot(t_2055_mean, main = "Température moyenne 2055 (°C)")

# 14. Exporter les résultats
writeRaster(t_2025_mean,
            filename = "I:/Memoire/SIG/Rendu_Ceres_Flore/R/Export/t_2025_mean_celsius.tif",
            overwrite = TRUE)

writeRaster(t_2055_mean,
            filename = "I:/Memoire/SIG/Rendu_Ceres_Flore/R/Export/t_2055_mean_celsius.tif",
            overwrite = TRUE)

# 15. Arrondir les valeurs à 1 chiffre après la virgule
t_2025_mean_c_round <- round(t_2025_mean, 1)
t_2055_mean_c_round <- round(t_2055_mean, 1)

# 16. Vectoriser les rasters moyens
vect_2025 <- as.polygons(t_2025_mean, na.rm = TRUE, dissolve = TRUE)
vect_2055 <- as.polygons(t_2055_mean, na.rm = TRUE, dissolve = TRUE)

# 17. Vérifier / réassigner le système de coordonnées
crs(vect_2025) <- crs(t_2025_mean)
crs(vect_2055) <- crs(t_2055_mean)

# 18. Exporter en GeoPackage
writeVector(vect_2025,
            filename = "I:/Memoire/SIG/Rendu_Ceres_Flore/R/Export/tas_2025_vector_celsius.gpkg",
            layer = "temp_2025",
            filetype = "GPKG",
            overwrite = TRUE)

writeVector(vect_2055,
            filename = "I:/Memoire/SIG/Rendu_Ceres_Flore/R/Export/tas_2055_vector_celsius.gpkg",
            layer = "temp_2055",
            filetype = "GPKG",
            overwrite = TRUE)

#Info raster de sortie


# Charger le raster
t_2025_mean <- rast("I:/Memoire/SIG/Rendu_Ceres_Flore/R/Export/t_2025_mean_celsius.tif")

# Résolution des pixels en degrés (latitude et longitude)
pixel_res_deg_lon <- res(t_2025_mean)[1]  # Dimension en longitude

# Latitude moyenne de la France (en degrés)
latitude_france <- 46.6

# Calcul de la taille du pixel en km à la latitude de la France
# distVincenty fonctionne bien pour calculer la distance entre deux points à une latitude donnée
pixel_size_km_france <- distVincentySphere(c(0, latitude_france), 
                                           c(pixel_res_deg_lon, latitude_france)) / 1000

# Afficher la taille du pixel en km pour la France
print(pixel_size_km_france)
