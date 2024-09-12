"""
Este archivo de configuración, config.py, se utiliza para centralizar todas las configuraciones de conexión
de la base de datos y otras constantes que se utilizan en el proyecto. Aquí se definen las credenciales para
conectarse a MySQL y a Neo4j, además de cualquier otra configuración global que pueda ser necesaria.
Al almacenar estos datos en un archivo separado, se facilita la gestión de las configuraciones, ya que solo
necesitan actualizarse en un lugar. 
"""

"""
Nombres de los alumnos:
Mará González Gómez
David Tarrasa Puebla
"""

# CAMBIAR TODAS LAS VARIABLES
# MySQL Configuration
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "MySQL-25MJ"
MYSQL_DB = "AmazonReviews"

# MongoDB Configuration
CONNECTION_STRING = "mongodb://localhost:27017"

# Neo4J Configuration
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "meryggmj"
