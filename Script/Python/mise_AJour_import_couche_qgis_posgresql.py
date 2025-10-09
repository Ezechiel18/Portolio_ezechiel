from qgis.core import QgsVectorLayerExporter, QgsProject, QgsMapLayer
import psycopg2

# Paramètres de connexion à PostgreSQL
host = "localhost"
port = "5437"
dbname = "memoiregag"
user = "postgres"
password = "climatologie"
schema = "public"

# Connexion à la base PostgreSQL
conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
conn.autocommit = True
cur = conn.cursor()

# Couches vectorielles du projet QGIS
layers = [layer for layer in QgsProject.instance().mapLayers().values() if layer.type() == QgsMapLayer.VectorLayer]

for layer in layers:
    table_name = layer.name().lower().replace(" ", "_")
    qualified_table_name = f'"{schema}"."{table_name}"'

    # Vérifie si la table existe
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        )
    """, (schema, table_name))
    exists = cur.fetchone()[0]

    # Supprime la table existante si nécessaire
    if exists:
        print(f"🧹 La table '{table_name}' existe déjà. Suppression en cours...")
        cur.execute(f'DROP TABLE {qualified_table_name} CASCADE')
        print(f"✅ Table '{table_name}' supprimée.")

    # Prépare l'URI de connexion
    uri = f"dbname='{dbname}' host={host} port={port} user='{user}' password='{password}' table={qualified_table_name}"

    print(f"📤 Export de la couche : {layer.name()} ➜ table : {table_name}")

    # Export de la couche (avec écrasement)
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

# Fermeture
cur.close()
conn.close()
