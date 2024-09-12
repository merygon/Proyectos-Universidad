from neo4j import GraphDatabase
import pandas as pd
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
import random

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
connection_string = config.CONNECTION_STRING
uri = config.NEO4J_URI
user_Neo4J = config.NEO4J_USER
password_Neo4J = config.NEO4J_PASSWORD
driver = GraphDatabase.driver(uri, auth=(f"{user_Neo4J}", f"{password_Neo4J}"))

"""
4.1 Obtener similitudes entre usuarios y mostrar los enlaces en Neo4J
"""


def jaccard_similarity(set1: set, set2: set) -> int:
    """
    Función que calcula la similtud de Jaccard (INTERSECCIÓN/UNIÓN) para los n usuarios con los n-1 usuarios.
    """
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    if union != 0:
        similitud = intersection / union
        return similitud


def articulos_puntuados(reviewer_id: str) -> dict:
    """
    Función que devuelve los ids de los articulos que ha puntuado cada usuario.
    """
    global conexion_mysql

    similarities = {}

    cursor = conexion_mysql.cursor()

    query = f"""SELECT DISTINCT r.asin
                FROM products p INNER JOIN reviews r ON r.asin = p.asin
                WHERE reviewerID = "{reviewer_id}";
                """
    cursor.execute(query)
    articulos_puntuados = set([row[0] for row in cursor.fetchall()])

    return articulos_puntuados


def similitudes(limite_usuarios: int):
    """
    Función que calcula primero los x usuarios (en función del parámetro indicado por el usuario) con mayor número de reviews
    y devuelve los ids obtenidos en SQL.
    A continuación, llama a la función que calcula la similitud de los articulos puntuados por usuarios, previamente se calcula esta
    similitud haciendo uso de la función articulos puntuados.
    Finalmente, carga los datos a Neo4j.
    """
    global driver, conexion_mysql

    cursor = conexion_mysql.cursor()

    query = f"""SELECT reviewerID
                FROM reviews
                GROUP BY reviewerID
                ORDER BY COUNT(*) DESC
                LIMIT {limite_usuarios};
                """
    cursor.execute(query)
    results = [row[0] for row in cursor.fetchall()]

    # Antes de ejecutar la consulta, borramos la base para que empiece de 0
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    with driver.session() as session:
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                user1 = results[i]
                user2 = results[j]
                similitud = jaccard_similarity(
                    articulos_puntuados(user1),
                    articulos_puntuados(user2),
                )
                if similitud != 0:
                    consulta = (
                        f"MERGE (u1:USER {{id: '{user1}'}})"
                        f"MERGE (u2:USER {{id: '{user2}'}})"
                        f"MERGE (u1) - [:SIMILITUD {{valor: '{similitud}'}}] -> (u2)"
                    )
                    session.run(consulta)
        print("Datos cargados.")


"""
4.2 Obtener enlaces entre usuarios y artículos
"""


def usuarios_articulos(tipo_articulo: str, num_articulos: int):
    """
    Función que obtiene en primer lugar el número de articulos pedido por el usuario correspondientes al tipo elegido también por el
    usuario, y devuelve los ids del objeto junto con los usuarios que los han puntuado con su nota y fecha.
    Elimina los posible datos que pueda haber de consultas anteriores en Neo4j y después carga los nuevos datos.
    """
    global driver, conexion_mysql

    cursor = conexion_mysql.cursor()

    query = f"""SELECT asin
                FROM products
                WHERE type = '{tipo_articulo}';
                """
    cursor.execute(query)
    productos = cursor.fetchall()
    muestra_random_productos = random.sample(productos, num_articulos)

    # Antes de ejecutar la consulta, borramos la base para que empiece de 0
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    with driver.session() as session:
        for producto in muestra_random_productos:
            id_producto = producto[0]
            query = f"""SELECT reviewerID, overall, reviewTime
                        FROM products NATURAL JOIN reviews
                        WHERE asin = "{id_producto}";
                        """
            cursor.execute(query)
            results = cursor.fetchall()
            for row in results:
                reviewerID, overall, reviewTime = row
                consulta = (
                    f"MERGE (u:USER {{id: '{reviewerID}'}}) "
                    f"MERGE (p:PRODUCT {{id: '{id_producto}'}}) "
                    f"MERGE (u)-[:USED {{rating: {overall}, time: '{reviewTime}'}}]->(p)"
                )
                session.run(consulta)
        print("Datos cargados.")


"""
4.3 Obtener algunos usuarios que han visto más de un determinado tipo de artículo
"""


def usuarios_varios_tipos_articulos():
    """
    Función que calcula los primeros 400 usuarios ordenados por nombre en SQL.
    A continuación, almacena por cada colección del tipo de objeto en MongoDB los ids de los usuarios que han puntuado esos artículos.
    Prosigue a evaluar cuántas veces se repite cada id de los de SQL en los de MongoDB y finalmente, carga en Neo4j aquellos usuarios
    que hayan puntuado más de un artículo (este es el número representado en el enlace del usuario con el producto.)
    """
    global driver, conexion_mysql, connection_string

    # Antes de ejecutar la consulta, borramos la base para que empiece de 0
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    cursor = conexion_mysql.cursor()

    query1 = f"""SELECT reviewerID
                FROM reviews
                LIMIT 400;
            """

    cursor.execute(query1)
    results = cursor.fetchall()
    usuarios_sql = [id[0] for id in results]

    client = MongoClient(connection_string)
    db = client["Reviews"]

    ids_collection = [
        doc["reviewerID"] for doc in db["Videogames"].find({}, {"reviewerID": 1})
    ]
    ids_collection1 = [
        doc["reviewerID"] for doc in db["Toys&Games"].find({}, {"reviewerID": 1})
    ]
    ids_collection2 = [
        doc["reviewerID"] for doc in db["MusicInst"].find({}, {"reviewerID": 1})
    ]
    ids_collection3 = [
        doc["reviewerID"] for doc in db["Digitalmusic"].find({}, {"reviewerID": 1})
    ]

    # Combinamos los usuarios de las colecciones de MongoDB en una sola lista
    usuarios_mongodb = []
    for id in ids_collection:
        usuarios_mongodb.append(id)
    for id in ids_collection1:
        usuarios_mongodb.append(id)
    for id in ids_collection2:
        usuarios_mongodb.append(id)
    for id in ids_collection3:
        usuarios_mongodb.append(id)

    id_counts = {}
    for id in usuarios_sql:
        if id in usuarios_mongodb:
            id_counts[id] = id_counts.get(id, 0) + 1
        else:
            id_counts[id] = 1

    # Vemos si los usuarios de SQL aparecen más de una vez en los de MongoDB
    usuarios_en_multiples_colecciones = [
        usuario for usuario in set(usuarios_sql) if usuarios_mongodb.count(usuario) > 1
    ]

    # Consulta SQL para obtener los usuarios con su correspondiente ASIN y tipo de producto y la cantidad de productos de ese tipo que han puntuado
    for id in usuarios_en_multiples_colecciones:
        query2 = f"""SELECT reviewerID, COUNT(p.asin) AS num_prod, type
                    FROM reviews r INNER JOIN products p ON r.asin = p.asin
                    WHERE reviewerID = '{id}'
                    GROUP BY reviewerID, type;
                """
        cursor.execute(query2)

        with driver.session() as session:
            results = cursor.fetchall()
            for row in results:
                reviewerID, num_prod, tipo = row
                consulta = (
                    f"MERGE (u:USER {{id: '{reviewerID}'}}) "
                    f"MERGE (t:TYPE_PRODUCT {{id: '{tipo}'}}) "
                    f"MERGE (u) - [:RATED {{consumed: {num_prod}}}] -> (t)"
                )
                session.run(consulta)
    print("Carga de datos finalizada en Neo4j")


"""
4.4 Artículos populares y artículos en común entre usuarios
"""


def articulos_populares_encomun():
    """
    Función que calcula en SQL los 5 artículos más populares con menos de 40 reviews y los carga en Neo4j junto con los usuarios
    que los han puntuado y el rating que les han dado.
    Por último, en Neo4j muestra el cálculo del enlace de los usuarios de cuántos artículos han puntuado en común.
    """
    global driver, conexion_mysql

    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    cursor = conexion_mysql.cursor()

    # 5 articulos más populares con menos de 40 reviews
    query = f"""SELECT p.asin
                FROM reviews r INNER JOIN products p ON r.asin = p.asin
                GROUP BY p.asin
                HAVING COUNT(reviewerID) < 40
                ORDER BY overall DESC
                LIMIT 5;
            """
    cursor.execute(query)
    results = cursor.fetchall()

    for row in results:
        id_prod = row[0]
        query2 = f"""SELECT reviewerID, overall
                    FROM reviews NATURAL JOIN products
                    WHERE asin = '{id_prod}';
                """
        cursor.execute(query2)
        resultados = cursor.fetchall()
        for fila in resultados:
            reviewerID, nota = fila

            with driver.session() as session:
                consulta = (
                    f"MERGE (u:USER {{id: '{reviewerID}'}}) "
                    f"MERGE (p:PRODUCT {{id: '{id_prod}'}}) "
                    f"MERGE (u) - [:RATED {{rating: {nota}}}] -> (p)"
                )
                session.run(consulta)
    print("Datos cargados.")

    # Cálculo del enlace de los usuarios con el número de articulos en comun punutados
    with driver.session() as session:
        consulta_enlaces = """MATCH (u1:USER)-[:RATED]->(p:PRODUCT)<-[:RATED]-(u2:USER)
                                WITH u1, u2, COLLECT(DISTINCT p) AS productos_comunes
                                WHERE SIZE(productos_comunes) > 1
                                RETURN u1, u2, SIZE(productos_comunes) AS num_productos_comunes
                            """
        session.run(consulta_enlaces)


if __name__ == "__main__":

    print(
        """
          Menú:
            1. Obtener similitudes entre usuarios y mostrar los enlaces en Neo4J

            2. Obtener enlaces entre usuarios y artículos

            3. Obtener algunos usuarios que han visto más de un determinado tipo de artículo

            4. Artículos populares y artículos en común entre usuarios
          """
    )
    eleccion = int(input("Seleccióna la opción que deseas ver: "))
    while eleccion not in range(1, 6):
        eleccion = int(input("Seleccióna la opción que deseas ver: "))

    if eleccion == 1:
        limite_usuarios = int(input("Introduce un límite de usuarios: "))
        similitudes(limite_usuarios)
    elif eleccion == 2:
        tipo_articulo = input(
            "Introduce el tipo de articulo que deseas seleccionar: (juguete/juego, videojuego, instrumento_musical, musica_digital) "
        )
        num_articulos = int(
            input("Introduce el número de articulos que deseas seleccionar: ")
        )
        while tipo_articulo not in [
            "juguete/juego",
            "videojuego",
            "instrumento_musical",
            "musica_digital",
        ]:
            tipo_articulo = input(
                "Introduce el tipo de articulo que deseas seleccionar: (juguete/juego, videojuego, instrumento_musical, musica_digital)"
            )
            num_articulos = int(
                input("Introduce el número de articulos que deseas seleccionar: ")
            )
        usuarios_articulos(tipo_articulo, num_articulos)
    elif eleccion == 3:
        usuarios_varios_tipos_articulos()
    elif eleccion == 4:
        articulos_populares_encomun()
    else:
        print("Fin del programa")
