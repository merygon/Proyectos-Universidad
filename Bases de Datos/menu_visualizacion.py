import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from pymongo import MongoClient
from tkinter import simpledialog
import pymysql
import matplotlib.dates as mdates
from datetime import datetime
from wordcloud import WordCloud  # pip install wordcloud
import config

"""
Nombres de los alumnos:
Mará González Gómez
David Tarrasa Puebla
"""

host = config.MYSQL_HOST
user = config.MYSQL_USER
password = config.MYSQL_PASSWORD
db = config.MYSQL_DB


def conectar_mysql():
    """
    Establece una conexión con la base de datos MySQL.

    Esta función configura y retorna una conexión a la base de datos MySQL especificada.
    Utiliza la configuración definida por las variables 'host', 'user', 'password' y 'database'
    para acceder a la base de datos 'amazonreviews'. Al especificar `pymysql.cursors.DictCursor`,
    aseguramos que los datos de las consultas sean devueltos en forma de diccionarios,
    permitiendo un acceso más intuitivo por nombre de columna.

    Returns:
        Una conexión a la base de datos MySQL.
    """
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db,
        cursorclass=pymysql.cursors.DictCursor,
    )


# FUNCIONES QUERY -----------------------------------------------------------------------------------
def obtener_reviews_por_año_sql(tipo_producto):
    """
    Obtiene la cantidad de reviews por año de un tipo específico de producto o de todos los productos.

    Conecta a la base de datos y realiza una consulta SQL que cuenta la cantidad de reviews
    para cada año. Si 'tipo_producto' es diferente a "todo", la consulta se filtra por ese tipo
    de producto. De lo contrario, cuenta las reviews para todos los tipos de productos.

    Args:
        tipo_producto (str): El tipo de producto para filtrar las reviews o "todo" para no filtrar.

    Returns:
        Una tupla de dos listas: la primera con los años y la segunda con la cantidad de reviews correspondientes a esos años.
    """
    conexion = conectar_mysql()
    try:
        with conexion.cursor() as cursor:
            if tipo_producto != "todo":
                query = """
                SELECT YEAR(reviewTime) AS año, COUNT(*) AS cantidad
                FROM reviews JOIN products ON reviews.asin = products.asin
                WHERE type = %s
                GROUP BY año
                ORDER BY año;
                """
                cursor.execute(query, (tipo_producto,))
            else:
                query = """
                SELECT YEAR(reviewTime) AS año, COUNT(*) AS cantidad
                FROM reviews JOIN products ON reviews.asin = products.asin
                GROUP BY año
                ORDER BY año;
                """
                cursor.execute(query)
            resultados = cursor.fetchall()
    finally:
        conexion.close()

    años = [resultado["año"] for resultado in resultados]
    cantidades = [resultado["cantidad"] for resultado in resultados]
    return años, cantidades


def obtener_popularidad_productos_mysql(categoria):
    """
    Obtiene el conteo de reviews por producto, mostrando su popularidad.

    Esta función realiza una consulta SQL para contar el número de reviews por ASIN, que representa
    un producto único en la base de datos. Si 'categoria' no es "todo", la consulta se filtra para
    contar solo los productos de esa categoría específica.

    Args:
        categoria (str): La categoría de los productos a consultar o "todo" para todos los productos.

    Returns:
        Una lista con el conteo de reviews para cada producto, ordenada de mayor a menor popularidad.
    """
    conexion = conectar_mysql()
    try:
        with conexion.cursor() as cursor:
            if categoria != "todo":
                query = """
                SELECT products.asin, COUNT(reviews.reviewID) AS review_count
                FROM products
                JOIN reviews ON products.asin = reviews.asin
                WHERE products.type = %s
                GROUP BY products.asin
                ORDER BY review_count DESC;
                """
                cursor.execute(query, (categoria,))
            else:
                query = """
                SELECT products.asin, COUNT(reviews.reviewID) AS review_count
                FROM products
                JOIN reviews ON products.asin = reviews.asin
                GROUP BY products.asin
                ORDER BY review_count DESC;
                """
                cursor.execute(query)
            resultados = cursor.fetchall()
    finally:
        conexion.close()

    conteos = [resultado["review_count"] for resultado in resultados]
    return conteos


def obtener_histograma_notas_mysql(tipo_producto=None, asin=None):
    """
    Recupera y genera un histograma de las calificaciones de los productos.

    Realiza una consulta SQL para contar la cantidad de veces que se ha dado cada calificación (overall)
    a un producto. Puede filtrar los resultados por un 'tipo_producto' específico, por un 'asin' de producto
    individual, o incluir todos los productos si no se especifica ningún filtro.

    Args:
        tipo_producto (str, optional): El tipo de producto para el que se recuperarán las calificaciones.
        asin (str, optional): El ASIN del producto individual para el que se recuperarán las calificaciones.

    Returns:
        dos listas: una con las calificaciones únicas y otra con el conteo correspondiente de cada calificación.
    """
    conexion = conectar_mysql()
    try:
        with conexion.cursor() as cursor:
            if asin:
                query = """
                SELECT p.overall, COUNT(*) AS cantidad
                FROM reviews r
                JOIN products p ON r.asin = p.asin
                WHERE p.asin = %s
                GROUP BY p.overall
                ORDER BY p.overall;
                """
                cursor.execute(query, (asin,))
            elif tipo_producto and tipo_producto != "todo":
                query = """
                SELECT p.overall, COUNT(*) AS cantidad
                FROM reviews r
                JOIN products p ON r.asin = p.asin
                WHERE p.type = %s
                GROUP BY p.overall
                ORDER BY p.overall;
                """
                cursor.execute(query, (tipo_producto,))
            else:
                query = """
                SELECT p.overall, COUNT(*) AS cantidad
                FROM reviews r
                JOIN products p ON r.asin = p.asin
                GROUP BY p.overall
                ORDER BY p.overall;
                """
                cursor.execute(query)
            resultados = cursor.fetchall()
    finally:
        conexion.close()

    if not resultados:
        return [], []

    notas = [resultado["overall"] for resultado in resultados]
    cantidades = [resultado["cantidad"] for resultado in resultados]
    return notas, cantidades


def obtener_evolucion_reviews_mysql(tipo_producto=None):
    """
    Obtiene la evolución del número de reviews a lo largo del tiempo.

    Esta función consulta la base de datos para obtener una secuencia acumulada de la cantidad de reviews
    a lo largo del tiempo, con la opción de filtrar por tipo de producto. Si no se especifica un tipo,
    se devuelve la evolución para todos los productos. La consulta SQL utiliza la función de ventana
    COUNT() OVER() para calcular el total acumulado.

    Args:
        tipo_producto (str, optional): El tipo de producto para filtrar la evolución. Si se omite o es 'todo', se incluyen todos los productos.

    Returns:
        list: Dos listas, una con los timestamps UNIX y otra con el recuento acumulado de reviews hasta cada punto en el tiempo.
    """
    conexion = conectar_mysql()
    try:
        with conexion.cursor() as cursor:
            if tipo_producto and tipo_producto != "todo":
                query = """
                SELECT UNIX_TIMESTAMP(reviewTime) AS timestamp, COUNT(*) OVER (ORDER BY UNIX_TIMESTAMP(reviewTime)) AS acumulado
                FROM reviews
                JOIN products ON reviews.asin = products.asin
                WHERE type = %s
                ORDER BY reviewTime;
                """
                cursor.execute(query, (tipo_producto,))
            else:
                query = """
                SELECT UNIX_TIMESTAMP(reviewTime) AS timestamp, COUNT(*) OVER (ORDER BY UNIX_TIMESTAMP(reviewTime)) AS acumulado
                FROM reviews
                ORDER BY reviewTime;
                """
                cursor.execute(query)
            resultados = cursor.fetchall()
    finally:
        conexion.close()

    timestamps = [resultado["timestamp"] for resultado in resultados]
    acumulados = [resultado["acumulado"] for resultado in resultados]
    return timestamps, acumulados


def obtener_reviews_por_usuario_mysql():
    """
    Esta función se conecta a la base de datos MySQL y recupera la cantidad de reviews
    que cada usuario ha realizado. Utiliza una consulta SQL que agrupa los datos por el ID
    del revisor y cuenta el número de reviews para cada uno.

    Returns:
        conteos_reviews (list of int): Una lista que contiene la cantidad de reviews
        que cada usuario ha realizado.
    """
    conexion = conectar_mysql()
    try:
        with conexion.cursor() as cursor:
            query = """
            SELECT reviewerID, COUNT(*) as num_reviews
            FROM reviews
            GROUP BY reviewerID
            """
            cursor.execute(query)
            resultado = cursor.fetchall()
    finally:
        conexion.close()

    conteos_reviews = [row["num_reviews"] for row in resultado]
    return conteos_reviews


def obtener_summaries_categoria(categoria):
    """
    Esta función conecta con la base de datos MySQL y recupera todos los resúmenes
    (summaries) de los productos de una categoría específica. Se realiza una consulta
    SQL que selecciona el campo 'summary' de la tabla 'products' donde el tipo de producto
    coincide con la categoría proporcionada.

    Args:
        categoria (str): La categoría de producto para la que se quieren obtener los resúmenes.

    Returns:
        summaries (list of str): Una lista de resúmenes (summaries) de los productos
        de la categoría solicitada.
    """
    conexion = conectar_mysql()
    summaries = []
    try:
        with conexion.cursor() as cursor:
            query = """
            SELECT summary FROM products WHERE type = %s;
            """
            cursor.execute(query, (categoria,))
            for row in cursor.fetchall():
                summaries.append(row["summary"])
    finally:
        conexion.close()
    return summaries


def obtener_distribucion_calificaciones_mysql():
    """
    Esta función se conecta a la base de datos MySQL 'amazonreviews' para obtener la distribución de las
    calificaciones ('overall') de los productos, agrupadas por tipo de producto.
    Utiliza un diccionario para almacenar las listas de calificaciones asociadas a cada tipo de producto.

    Returns:
        dict: Un diccionario donde las llaves son los tipos de producto ('juguete/juego', 'videojuego', 'musica_digital')
              y los valores son listas de enteros representando las calificaciones de los productos.
    """
    conexion = conectar_mysql()
    datos_distribucion = {}
    try:
        with conexion.cursor() as cursor:
            tipos_producto = [
                "juguete/juego",
                "videojuego",
                "musica_digital",
                "instrumento_musical",
            ]
            for tipo in tipos_producto:
                query = """
                SELECT overall FROM products 
                JOIN reviews ON products.asin = reviews.asin
                WHERE type = %s;
                """
                cursor.execute(query, (tipo,))
                datos_distribucion[tipo] = [row["overall"] for row in cursor.fetchall()]
    finally:
        conexion.close()
    return datos_distribucion


# --------------------------------------------------------------------------------------------------------------------
# GRAFICOS -----------------------------------------------------------------------------------------------------------
def mostrar_grafica_evolucion_reviews_sql(años, conteos):
    """
    Función para generar una gráfica de barras que muestra la evolución del número de reviews por año.
    """
    plt.figure(figsize=(10, 6))
    plt.bar(años, conteos, color="skyblue")
    plt.title("Evolución de Reviews por Años")
    plt.xlabel("Años")
    plt.ylabel("Número de Reviews")
    plt.show()


def mostrar_grafica_popularidad_productos_mysql(conteos):
    """
    Función para generar una gráfica que muestra la popularidad de los productos.
    La popularidad se define como el número de reviews que tiene cada producto.
    """
    conteos_ordenados = sorted(conteos, reverse=True)

    plt.figure(figsize=(10, 6))
    plt.plot(conteos_ordenados)
    plt.title("Evolución de la popularidad de los productos")
    plt.xlabel("Artículos")
    plt.ylabel("Número de reviews")
    plt.show()


def mostrar_histograma_notas_mysql(notas, cantidades):
    """
    Función para generar un histograma que muestra la distribución de las notas.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(notas, cantidades, color="skyblue")
    ax.set_title("Histograma por nota")
    ax.set_xlabel("Nota")
    ax.set_ylabel("Número de reviews")
    ax.set_xticks(range(1, 6))
    ax.set_xticklabels(range(1, 6))
    plt.show()


def mostrar_evolucion_reviews_mysql(timestamps, acumulados):
    """
    Función para generar una gráfica que muestra la evolución del número de reviews a lo largo del tiempo.
    """
    fechas = [datetime.fromtimestamp(ts) for ts in timestamps]

    plt.figure(figsize=(10, 6))
    plt.plot(fechas, acumulados)
    plt.title("Evolución de las reviews a lo largo del tiempo")
    plt.xlabel("Tiempo")
    plt.ylabel("Número de reviews hasta el momento")

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    plt.gcf().autofmt_xdate()

    plt.show()


def mostrar_histograma_reviews_por_usuario():
    """
    Función para generar un histograma que muestra la distribución del número de reviews por usuario.
    """
    conteos_reviews = obtener_reviews_por_usuario_mysql()

    review_counts = {}
    for count in conteos_reviews:
        if count in review_counts:
            review_counts[count] += 1
        else:
            review_counts[count] = 1

    reviews = list(review_counts.keys())
    users = [review_counts[review] for review in reviews]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(reviews, users, color="skyblue")
    ax.set_title("Histograma de Reviews por Usuario")
    ax.set_xlabel("Número de Reviews")
    ax.set_ylabel("Número de Usuarios")
    ax.set_xscale("log")
    plt.show()


def crear_nube_palabras(summaries):
    """
    Función para generar una nube de palabras a partir de un conjunto de resúmenes.
    """

    text = " ".join(summaries)
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(
        text
    )
    plt.figure(figsize=(8, 4), facecolor=None)
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.show()


def mostrar_grafica_distribucion_calificaciones(datos_distribucion):
    """
    Función para generar una gráfica de distribución (boxplot) de calificaciones por tipo de producto.

    La función toma un diccionario `datos_distribucion` donde las claves representan los tipos de producto
    y los valores son listas de calificaciones para cada tipo. La función utiliza la librería matplotlib para
    crear un boxplot que muestra la distribución de las calificaciones para cada tipo de producto.

    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(datos_distribucion.values(), labels=datos_distribucion.keys())
    ax.set_title("Distribución de Calificaciones por Tipo de Producto")
    ax.set_xlabel("Tipo de Producto")
    ax.set_ylabel("Calificaciones")
    plt.show()


# ---------------------------------------------------------------------------------------------------------------------------------
# PETICIONES ----------------------------------------------------------------------------------------------------------------------
def pedir_categoria_y_mostrar_grafica_sql():
    """
    Función para solicitar al usuario una categoría de producto y luego mostrar una gráfica de la evolución del número de reviews por año para esa categoría.

    Salida:
    La función muestra una gráfica de la evolución del número de reviews por año para la categoría seleccionada por el usuario.
    """
    categorias = [
        "juguete/juego",
        "videojuego",
        "musica_digital",
        "instrumento_musical",
        "todo",
    ]
    eleccion = simpledialog.askstring(
        "Categoría",
        "Elige una categoría: juguete/juego, videojuego, musica_digital, instrumento_musical, o todo",
    )
    if eleccion and eleccion in categorias:
        años, cantidades = obtener_reviews_por_año_sql(eleccion)
        mostrar_grafica_evolucion_reviews_sql(años, cantidades)
    else:
        tk.messagebox.showerror("Error", "Por favor, elige una categoría válida.")


def pedir_categoria_y_mostrar_grafica_popularidad():
    """
    Función para solicitar al usuario una categoría de producto y luego mostrar una gráfica de la popularidad de los productos de esa categoría.

    Salida:
    La función muestra una gráfica de la popularidad de los productos de la categoría seleccionada por el usuario.
    """
    categorias = [
        "juguete/juego",
        "videojuego",
        "musica_digital",
        "instrumento_musical",
        "todo",
    ]
    eleccion = simpledialog.askstring(
        "Categoría",
        "Elige una categoría: juguete/juego, videojuego, musica_digital, instrumento_musical, o todo",
    )
    if eleccion and eleccion in categorias:
        conteos = obtener_popularidad_productos_mysql(eleccion)
        mostrar_grafica_popularidad_productos_mysql(conteos)
    else:
        tk.messagebox.showerror("Error", "Por favor, elige una categoría válida.")


def pedir_tipo_producto_o_asin_y_mostrar_histograma():
    """
    Función para solicitar al usuario un tipo de producto, un ASIN o "todo" para mostrar un histograma de la distribución de las notas de los reviews.

    Salida:
    La función muestra un histograma de la distribución de las notas de los reviews para la selección del usuario.
    """
    eleccion = simpledialog.askstring(
        "Búsqueda",
        "Introduce 'todo' para todos los productos, un tipo de producto (juguete/juego, videojuego, musica_digital, instrumento_musical), \n"
        "o un ASIN de un artículo específico.",
    )
    if not eleccion or eleccion == "todo":
        notas, cantidades = obtener_histograma_notas_mysql()
    elif eleccion in [
        "juguete/juego",
        "videojuego",
        "musica_digital",
        "instrumento_musical",
    ]:
        notas, cantidades = obtener_histograma_notas_mysql(tipo_producto=eleccion)
    else:
        notas, cantidades = obtener_histograma_notas_mysql(asin=eleccion)

    if notas and cantidades:
        mostrar_histograma_notas_mysql(notas, cantidades)
    else:
        tk.messagebox.showinfo(
            "Información", "No se encontraron datos para la selección realizada."
        )


def pedir_tipo_producto_y_mostrar_evolucion_reviews():
    """
    Función para solicitar al usuario un tipo de producto o "todo" para mostrar una gráfica de la evolución del número de reviews a lo largo del tiempo.

    Salida:
    La función muestra una gráfica de la evolución del número de reviews a lo largo del tiempo para la selección del usuario.
    """
    eleccion = simpledialog.askstring(
        "Selección de Tipo de Producto",
        "Introduce un tipo de producto (juguete/juego, videojuego, musica_digital, instrumento_musical) "
        "o 'todo' para todos los productos.",
    )
    if eleccion:
        if eleccion.lower() in [
            "juguete/juego",
            "videojuego",
            "musica_digital",
            "instrumento_musical",
        ]:
            timestamps, acumulados = obtener_evolucion_reviews_mysql(
                tipo_producto=eleccion.lower()
            )
        elif eleccion.lower() == "todo":
            timestamps, acumulados = obtener_evolucion_reviews_mysql()
        else:
            tk.messagebox.showinfo("Error", "Tipo de producto no reconocido.")
            return
    else:
        timestamps, acumulados = obtener_evolucion_reviews_mysql()

    if timestamps and acumulados:
        mostrar_evolucion_reviews_mysql(timestamps, acumulados)
    else:
        tk.messagebox.showinfo(
            "Información", "No se encontraron datos para la selección realizada."
        )


def pedir_categoria_y_mostrar_nube_palabras():
    """
    Función para solicitar al usuario una categoría de producto y luego mostrar una nube de palabras a partir de los resúmenes de los reviews de esa categoría.

    Salida:
    La función muestra una nube de palabras a partir de los resúmenes de los reviews de la categoría seleccionada por el usuario.
    """
    categorias = [
        "juguete/juego",
        "videojuego",
        "musica_digital",
        "instrumento_musical",
    ]
    eleccion = simpledialog.askstring(
        "Categoría",
        "Elige una categoría: juguete/juego, videojuego, musica_digital, instrumento_musical",
    )
    if eleccion and eleccion in categorias:
        summaries = obtener_summaries_categoria(eleccion)
        crear_nube_palabras(summaries)
    else:
        tk.messagebox.showerror("Error", "Por favor, elige una categoría válida.")


def pedir_y_mostrar_grafica_distribucion_calificaciones():
    """
    Función para mostrar una gráfica de la distribución de las calificaciones de los reviews para cada tipo de producto.

    Salida:
    La función muestra una gráfica de la distribución de las calificaciones de los reviews para cada tipo de producto.
    """
    datos_distribucion = obtener_distribucion_calificaciones_mysql()
    mostrar_grafica_distribucion_calificaciones(datos_distribucion)


# --------------------------------------------------------------------------------------------------------------------------------------------


def crear_menu_principal():
    """
    Función para crear la ventana principal de la aplicación y colocar los botones para acceder a las diferentes funcionalidades.

    Salida:
    Crea la ventana principal con los botones para las diferentes funcionalidades de la aplicación.
    """
    fondo_label = tk.Label(ventana, image=imagen_fondo)
    fondo_label.place(x=0, y=0, relwidth=1, relheight=1)
    definir_titulo()

    boton_evolucion = tk.Button(
        ventana,
        text="Evolución Reviews por Años",
        command=pedir_categoria_y_mostrar_grafica_sql,
    )
    boton_evolucion.pack(pady=10)
    boton_evolucion.config(
        bg="SteelBlue1", width=60, height=2, borderwidth=5, font=("Times", 15)
    )

    boton_popularidad = tk.Button(
        ventana,
        text="Popularidad de Artículos",
        command=pedir_categoria_y_mostrar_grafica_popularidad,
    )
    boton_popularidad.pack(pady=10)
    boton_popularidad.config(
        bg="SteelBlue1", width=60, height=2, borderwidth=5, font=("Times", 15)
    )

    boton_histograma = tk.Button(
        ventana,
        text="Histograma por Nota",
        command=pedir_tipo_producto_o_asin_y_mostrar_histograma,
    )
    boton_histograma.pack(pady=10)
    boton_histograma.config(
        bg="SteelBlue1", width=60, height=2, borderwidth=5, font=("Times", 15)
    )

    boton_evolucion_reviews = tk.Button(
        ventana,
        text="Evolución Reviews a lo Largo del Tiempo",
        command=pedir_tipo_producto_y_mostrar_evolucion_reviews,
    )
    boton_evolucion_reviews.pack(pady=10)
    boton_evolucion_reviews.config(
        bg="SteelBlue1", width=60, height=2, borderwidth=5, font=("Times", 15)
    )

    boton_reviews_usuario = tk.Button(
        ventana,
        text="Histograma de Reviews por Usuario",
        command=mostrar_histograma_reviews_por_usuario,
    )
    boton_reviews_usuario.pack(pady=10)
    boton_reviews_usuario.config(
        bg="SteelBlue1", width=60, height=2, borderwidth=5, font=("Times", 15)
    )

    boton_nube_palabras = tk.Button(
        ventana,
        text="Nube de Palabras por Categoría",
        command=pedir_categoria_y_mostrar_nube_palabras,
    )
    boton_nube_palabras.pack(pady=10)
    boton_nube_palabras.config(
        bg="SteelBlue1", width=60, height=2, borderwidth=5, font=("Times", 15)
    )

    boton_distribucion_calificaciones = tk.Button(
        ventana,
        text="Distribución de Calificaciones",
        command=pedir_y_mostrar_grafica_distribucion_calificaciones,
    )
    boton_distribucion_calificaciones.pack(pady=10)
    boton_distribucion_calificaciones.config(
        bg="SteelBlue1", width=60, height=2, borderwidth=5, font=("Times", 15)
    )

    boton_salida = tk.Button(ventana, text="Salir", command=ventana.quit)
    boton_salida.pack(side=tk.BOTTOM, pady=20)
    boton_salida.config(
        bg="maroon", fg="White", width=60, height=2, borderwidth=5, font=("Times", 15)
    )


def definir_titulo():
    """
    Esta función define el título de la aplicación y una barra con los nombres de los desarrolladores.
    """
    titulo = tk.Label(
        ventana,
        text="Visualizador de Datos",
        font=("Times", 26, "bold"),
        fg="SteelBlue1",
    )
    titulo.pack(pady=20)
    titulo.config(font=("Times", 21, "bold"), width=100, height=1, bg="Black")
    barra_nombres = tk.Label(ventana, text="María Gómez / David Tarrasa", anchor="w")
    barra_nombres.place(x=10, y=15)
    barra_nombres.config(font=("Times", 10), fg="SteelBlue1", bg="Black")


def main():
    """
    Esta función es la función principal de la aplicación.
    """
    global ventana, imagen_fondo
    ventana = tk.Tk()
    ventana.title("Visualizador de Datos")
    ventana.geometry("1200x900")

    imagen_fondo = ImageTk.PhotoImage(file="imagen.jpg")
    crear_menu_principal()

    ventana.mainloop()


if __name__ == "__main__":
    main()
