from qgis.core import QgsVectorLayerExporter, QgsProject, QgsMapLayer

# Paramètres à adapter
host = "localhost"
port = "5437"
dbname = "memoiregag"
user = "postgres"
password = "climatologie"
schema = "public"

# Récupérer toutes les couches vectorielles ouvertes dans le projet
layers = [layer for layer in QgsProject.instance().mapLayers().values() if layer.type() == QgsMapLayer.VectorLayer]

for layer in layers:
    table_name = layer.name().lower().replace(" ", "_")
    
    # Supprimer key='id' si tes couches n'ont pas de champ ID unique
    uri = f"dbname='{dbname}' host={host} port={port} user='{user}' password='{password}' table=\"{schema}\".\"{table_name}\""

    print(f"📤 Export de la couche : {layer.name()} ➜ table : {table_name}")

    # Export
    error = QgsVectorLayerExporter.exportLayer(
        layer,
        uri,
        "postgres",
        layer.crs(),
        False
    )

    if error[0] == QgsVectorLayerExporter.NoError:
        print(f"✅ Couche '{layer.name()}' exportée avec succès.")
    else:
        print(f"❌ Erreur pour '{layer.name()}': {error[1]}")
