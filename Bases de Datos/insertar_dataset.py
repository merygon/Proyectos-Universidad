import time
from pymongo import MongoClient, InsertOne, UpdateOne, ReplaceOne
from pymongo.database import Database
import pymysql
import pandas as pd
import numpy as np
import re
from datetime import datetime
import json
import config

"""
Nombres de los alumnos:
Mará González Gómez
David Tarrasa Puebla
"""

# Carga de las variables del archivo config
host_sql = config.MYSQL_HOST
user_sql = config.MYSQL_USER
password_sql = config.MYSQL_PASSWORD
conexion_mysql = pymysql.connect(
    host=f"{host_sql}",
    user=user_sql,
    password=password_sql,
    database="AmazonReviews",
)

host_mongodb = config.MONGODB_HOST
port_mongodb = config.MONGODB_PORT
client = MongoClient(f"{host_mongodb}", port_mongodb)
db = client["Reviews"]

archivo = "Clothing_Shoes_and_Jewelry_5.json"


def insertar_mogodb():
    global archivo, client, db
    """
    Función que inserta la información del fichero en la base de datos.
    """
    collection = db["Clothing&Shoes&Jewelry"]

    with open(f"{archivo}") as file:
        for line in file:
            data = json.loads(line)
            collection.insert_one(data)


def insercion_datos():
    global conexion_mysql, archivo

    with conexion_mysql.cursor() as cursor:

        with open(f"{archivo}") as file:

            reviewID = 0  # contador = reviewID
            tipo = "Clothing/Shoes/Jewels"

            for line in file:
                reviewID += 1
                data = json.loads(line)

                # Separación del valor de lista helpful en 2 variables distintas
                helpful1, helpful2 = data.get("helpful")

                # Estandarización del valor de tiempo al estandar YYYY-MM-DD
                reviewTime_str = data.get("reviewTime")
                reviewTime = datetime.strptime(reviewTime_str, "%m %d, %Y").strftime(
                    "%Y-%m-%d"
                )

                # Inserción de los datos en sus tablase correspondientes
                cursor.execute(
                    "INSERT IGNORE INTO reviewers (reviewerID, reviewerName) VALUES (%s, %s)",
                    (data.get("reviewerID"), data.get("reviewerName")),
                )
                cursor.execute(
                    "INSERT IGNORE INTO products (asin, helpful1, helpful2, overall, summary, type) VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        data.get("asin"),
                        helpful1,
                        helpful2,
                        data.get("overall"),
                        data.get("summary"),
                        tipo,
                    ),
                )
                cursor.execute(
                    "INSERT INTO reviews (reviewerID, asin, reviewID, reviewText, reviewTime) VALUES (%s, %s, %s, %s, %s)",
                    (
                        data.get("reviewerID"),
                        data.get("asin"),
                        reviewID,
                        data.get("reviewText"),
                        reviewTime,
                    ),
                )

    conexion_mysql.commit()
    conexion_mysql.close()


if __name__ == "__main__":

    insertar_mogodb()
    print("Datos insertados en MongoDB.")
    insercion_datos()
    print("Datos insertados.")
