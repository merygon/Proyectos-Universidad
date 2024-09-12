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

connection_string = config.CONNECTION_STRING
client = MongoClient(connection_string)


def insertar_mogodb():
    """
    Función que inserta la información del fichero en la base de datos.
    Bases de datos ya creadas: Videogames en Reviews
    Bases de datos a crear: Musical Instrument, Toys & Games y Digital Music
    """
    global client

    db = client["Reviews"]

    collection = db["Videogames"]
    with open("Video_Games_5.json") as file:
        for line in file:
            data = json.loads(line)
            collection.insert_one(
                {
                    "reviewerID": data["reviewerID"],
                    "asin": data["asin"],
                    "reviewText": data["reviewText"],
                }
            )

    collection1 = db["Toys&Games"]

    with open("Toys_and_Games_5.json") as file:
        for line in file:
            data = json.loads(line)
            collection1.insert_one(
                {
                    "reviewerID": data["reviewerID"],
                    "asin": data["asin"],
                    "reviewText": data["reviewText"],
                }
            )

    collection2 = db["MusicInst"]

    with open("Musical_Instruments_5.json") as file:
        for line in file:
            data = json.loads(line)
            collection2.insert_one(
                {
                    "reviewerID": data["reviewerID"],
                    "asin": data["asin"],
                    "reviewText": data["reviewText"],
                }
            )

    collection3 = db["Digitalmusic"]

    with open("Digital_Music_5.json") as file:
        for line in file:
            data = json.loads(line)
            collection3.insert_one(
                {
                    "reviewerID": data["reviewerID"],
                    "asin": data["asin"],
                    "reviewText": data["reviewText"],
                }
            )


def crear_base_datos():
    global host_sql, user_sql, password_sql
    conexion_mysql = pymysql.connect(
        host=f"{host_sql}", user=user_sql, password=password_sql
    )

    nombre_base_datos = "AmazonReviews"

    with conexion_mysql:

        cursor = conexion_mysql.cursor()

        sql = "CREATE DATABASE " + str(nombre_base_datos)
        cursor.execute(sql)

        sql = "USE " + str(nombre_base_datos)
        cursor.execute(sql)


def tablas():
    global host_sql, user_sql, password_sql
    conexion_mysql = pymysql.connect(
        host=f"{host_sql}",
        user=user_sql,
        password=password_sql,
        database="AmazonReviews",
    )

    cursor = conexion_mysql.cursor()

    consulta = """CREATE TABLE IF NOT EXISTS reviewers (reviewerID VARCHAR(255) PRIMARY KEY,
                                                    reviewerName VARCHAR(255))"""

    cursor.execute(consulta)

    conexion_mysql.commit()

    consulta = """CREATE TABLE IF NOT EXISTS products (asin VARCHAR(255) PRIMARY KEY,
                                                    helpful1 INT,
                                                    helpful2 INT,
                                                    overall INT,
                                                    summary TEXT,
                                                    type TEXT)"""

    cursor.execute(consulta)

    conexion_mysql.commit()

    consulta = """CREATE TABLE IF NOT EXISTS reviews (reviewerID VARCHAR(255),
                                                    asin VARCHAR(255),
                                                    reviewID INT,
                                                    reviewTime DATE,
                                                    PRIMARY KEY (reviewerID, asin, reviewID),
                                                    FOREIGN KEY (reviewerID) REFERENCES reviewers(reviewerID),
                                                    FOREIGN KEY (asin) REFERENCES products(asin))"""

    cursor.execute(consulta)

    conexion_mysql.commit()

    cursor.close()
    conexion_mysql.close()


def insercion_datos():
    global host_sql, user_sql, password_sql
    conexion_mysql = pymysql.connect(
        host=f"{host_sql}",
        user=user_sql,
        password=password_sql,
        database="AmazonReviews",
    )

    archivos = [
        "Video_Games_5.json",
        "Toys_and_Games_5.json",
        "Musical_Instruments_5.json",
        "Digital_Music_5.json",
    ]

    with conexion_mysql.cursor() as cursor:

        for archivo in archivos:

            if archivo == "Video_Games_5.json":
                tipo = "videojuego"
            if archivo == "Toys_and_Games_5.json":
                tipo = "juguete/juego"
            if archivo == "Musical_Instruments_5.json":
                tipo = "instrumento_musical"
            if archivo == "Digital_Music_5.json":
                tipo = "musica_digital"

            with open(f"{archivo}") as file:

                reviewID = 0  # contador = reviewID

                for line in file:
                    reviewID += 1
                    data = json.loads(line)

                    # Separación del valor de lista helpful en 2 variables distintas
                    helpful1, helpful2 = data.get("helpful")

                    # Estandarización del valor de tiempo al estandar YYYY-MM-DD
                    reviewTime_str = data.get("reviewTime")
                    reviewTime = datetime.strptime(
                        reviewTime_str, "%m %d, %Y"
                    ).strftime("%Y-%m-%d")

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
                        "INSERT INTO reviews (reviewerID, asin, reviewID, reviewTime) VALUES (%s, %s, %s, %s)",
                        (
                            data.get("reviewerID"),
                            data.get("asin"),
                            reviewID,
                            reviewTime,
                        ),
                    )

        conexion_mysql.commit()

    conexion_mysql.close()


if __name__ == "__main__":

    insertar_mogodb()
    print("Datos insertados en MongoDB.")
    crear_base_datos()
    print("Base de datos creada")
    tablas()
    print("Tablas creadas.")
    insercion_datos()
    print("Datos insertados.")
