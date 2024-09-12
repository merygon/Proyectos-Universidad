import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter


def merge_data(
    crawler_data: str,
    ergast_data: str,
    crawler_df: pd.DataFrame,
    ergast_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Función que fusiona los DataFrames del apartado 1 con los del 2 en la columna que se corresponde con su número identificador
    para crear un único DataFrame. Añadimos además las columnas que indican la temporada a la que corresponde el resultado de
    cada corredor y el número de la carrera.
    """
    crawler_df.rename(
        {"No.": "permanentNumber"}, inplace=True, axis=1
    )  # cambiamos el nombre de la columna de los dfs del apartado 1 para se corresponda con el nombre de los dfs del apartado 2
    merged_df = pd.merge(
        crawler_df, ergast_df, on="permanentNumber", how="inner"
    )  # creamos el dataframe de fusión en la columna con el método inner dado que hay pilotos que compiten en algunas carrears y no en otras, de esta forma solo cogerá los pilotos que están en la carrera
    name = ergast_data.split("/")[-1].rsplit(".", 1)[
        0
    ]  # cogemos el nombre del df y hacemos un split para sacar los datos de temporada y número de carrera
    number = name.split("_")[1]  # número de carrera
    year = name.split("_")[2]  # temporada
    gp_name = crawler_data.split("/")[-1].split(" ", 1)[-1].rsplit(".", 1)[0]
    merged_df["RaceNumber"] = number
    merged_df["Season"] = year
    merged_df["GPName"] = gp_name
    return merged_df


# 1: número de paradas optimo en cada circuito


def paradas_optimas(merged_df: pd.DataFrame) -> pd.Series:
    """
    Función que analiza el número de paradas óptimo en ese circuito en función de las que realizo el ganador.
    """
    # Primero pasamos los datos que vamos a evaluar a tipo int para poder tratar con ellos
    merged_df["stop"] = pd.to_numeric(merged_df["stop"], errors="coerce")
    merged_df["Pos"] = pd.to_numeric(merged_df["Pos"], errors="coerce")
    median_pit_stops = merged_df.groupby("Driver")[
        "stop"
    ].mean()  # creamos un df solo con las columnas del nombre del corredor y sus paradas

    df_positions = merged_df[
        ["Driver", "Pos"]
    ]  # creamos otro df solo con las columnas del nombre del corredor y su posición final en la carrera

    # Fusiona los DataFrames por la columna 'Driver'
    median_pit_stops_with_positions = pd.merge(
        median_pit_stops, df_positions, on="Driver", how="left"
    )

    median_pit_stops_sorted = median_pit_stops_with_positions.sort_values(
        by="Pos", ascending=True
    )  # ordenamos los datos por posición de primero al último y al final los descalificados

    # Bar plot
    # Creamos un gráfico de barras que representa los datos obtenidos para poder estudiar si existe algún tipo de relación
    # entre el número de paradas y la posición final obtenida
    median_pit_stops_sorted.plot(kind="bar", x="Pos", y="stop", figsize=(10, 5))
    plt.title("Promedio de paradas de los pilotos en la carrera")
    plt.xlabel("Posición")
    plt.ylabel("Promedio de paradas")
    plt.xticks(rotation=45)
    plt.show()

    return median_pit_stops_sorted


def check_winner_with_pit(merged_df):
    possible_winners = merged_df.iloc[:3].copy()
    possible_winners["Time/Retired"] = possible_winners["Time/Retired"].apply(
        lambda x: float(
            x.lstrip("+").replace(" ", "").replace("Lap", "00").replace("lap", "00")
        )
        if ":" not in x
        else 0
    )

    time_m = possible_winners.iloc[0]["duration"]
    possible_winners["duration"] = possible_winners["duration"].apply(
        lambda x: float(time_m) - x
    )

    possible_winners["new_time"] = (
        possible_winners["Time/Retired"]
        + possible_winners["duration"] * possible_winners["stop"]
    )
    if possible_winners[possible_winners["new_time"] < 0].shape != (0, 15):
        d[
            str(
                possible_winners["RaceNumber"].iloc[0]
                + "-"
                + str(possible_winners["Season"].iloc[0])
            )
        ] = list(
            possible_winners[
                (possible_winners["Pos"] == "1") | (possible_winners["new_time"] < 0)
            ]["Driver"]
        )
        if (
            str(
                possible_winners["RaceNumber"].iloc[0]
                + "-"
                + str(possible_winners["Season"].iloc[0])
            )
            == "21-2023"
        ):
            print(
                possible_winners[
                    (possible_winners["Pos"] == "1")
                    | (possible_winners["new_time"] < 0)
                ]["Driver"]
            )


def year_positions(year_df, year):
    constructor_order = (
        year_df.groupby("Constructor")["duration"].median().sort_values()
    )
    print(year, constructor_order)
    l.append(list(constructor_order.index)[0].split("-")[0].strip())


d = {}
l = []


if __name__ == "__main__":
    year = int(
        input("Introduce el año del que deseas estudiar las carreras (2012-2023): ")
    )
    while year not in range(2012, 2024):
        print("Año no valido, por favor introduzca un año valido.")
        year = int(
            input("Introduce el año del que deseas estudiar las carreras (2012-2023): ")
        )

    directory = f"{year}"  # seleccionamos el nombre del directorio que tiene los datos de Scrappy
    csv_files = sorted(
        [file for file in os.listdir(directory) if file.endswith(".csv")],
        key=lambda x: int(x.split(" ")[0].strip("#")),
    )  # cogemos todos los ficheros de ese directorio y los ordenamos tal y como vienen en la carpeta
    number = int(
        input(
            f"Seleccion el número de carrera que deseas estudiar (1-{len(csv_files)}): "
        )
    )
    while number not in range(1, len(os.listdir()) + 1):
        number = input(
            f"Seleccion el número de carrera que deseas estudiar (1-{len(csv_files)}): "
        )

    # ahora nos aseguramos de que los ficheros existen y los convertimos a un DataFrame de pandas para poder manipularlos
    try:
        crawler_data = f"{directory}/{csv_files[number]}"
        crawler_df = pd.read_csv(crawler_data)  # conversión a un DataFrame
        crawler_df = crawler_df.drop("Unnamed: 0", axis=1)
    except FileExistsError as error:
        print(error)

    try:
        ergast_data = f"races_{year}/race_{number}_{year}.csv"
        ergast_df = pd.read_csv(ergast_data)  # conversión a un DataFrame
        ergast_df = ergast_df.drop("Unnamed: 0", axis=1)
    except FileExistsError as error:
        print(error)

    # llamamos a la función de merge e imprimos el dataset final
    merged_df = merge_data(crawler_data, ergast_data, crawler_df, ergast_df)
    print(merged_df)

    merged_df.to_csv(f"merged_data_{year}_race_{number}.csv", index=False)

    # analisis del dataframe obtenido

    print(f"Número de paradas óptimas del circuito: ")
    num_stops = paradas_optimas(merged_df)
    print(num_stops.head(1))

    l_year = []
    year_df = pd.DataFrame()
    for year in range(2012, 2024):
        directory = f"{year}"
        csv_files = sorted(
            [file for file in os.listdir(directory) if file.endswith(".csv")],
            key=lambda x: int(x[1:3].strip()),
        )

        for number in range(len(csv_files)):
            try:
                crawler_data = f"{directory}/{csv_files[number]}"
                crawler_df = pd.read_csv(crawler_data)  # conversión a un DataFrame
                crawler_df = crawler_df.drop("Unnamed: 0", axis=1)
            except FileExistsError as error:
                print(error)

            try:
                ergast_data = f"races_{year}/race_{number+1}_{year}.csv"
                ergast_df = pd.read_csv(ergast_data)  # conversión a un DataFrame
                ergast_df = ergast_df.drop("Unnamed: 0", axis=1)
            except FileExistsError as error:
                print(error)

            # llamamos a la función de merge e imprimos el dataset final
            merged_df = merge_data(crawler_data, ergast_data, crawler_df, ergast_df)
            constructor_order = (
                merged_df.groupby("Constructor")["duration"].median().sort_values()
            )
            # check_winner_with_pit(merged_df)
            year_df = pd.concat([year_df, merged_df])
            l_year.append(list(constructor_order.index)[0].split("-")[0].strip())
        # year_positions(year_df, year)
        year_df = pd.DataFrame()
        counter = Counter(l_year)
        frequent = (
            max(counter, key=lambda x: counter[x])
            if max(counter, key=lambda x: counter[x]) != "Red Bull"
            else "Red Bull Racing"
        )
        l.append(frequent)
        l_year = []

        # merged_df.to_csv(f"merged_data_{year}_race_{number}.csv", index=False)
    print(l)

    # Sample data (replace this with your list of words)

    # Count the occurrences of each word
    word_counts = Counter(l)

    # Convert the Counter object to a DataFrame for Seaborn plotting
    word_counts_df = pd.DataFrame(list(word_counts.items()), columns=["Word", "Count"])
    word_counts_df = word_counts_df.sort_values(by="Count", ascending=False)

    # Create a bar plot using Seaborn
    plt.figure(figsize=(10, 6))  # Adjust the figure size as needed
    sns.barplot(x="Word", y="Count", data=word_counts_df, palette="viridis")

    plt.xlabel("Equipo")

    # Show the plot
    plt.show()
