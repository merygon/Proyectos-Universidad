import requests
from urllib.parse import urlencode, urlunsplit
import json
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import io
import re
import unicodedata

SCHEME = "https"
BASE = "ergast.com/api/f1"


class NoMoreRaces(Exception):
    def __init__(self) -> None:
        pass


def make_url_and_petition(year, race, query={}):
    QUERY = urlencode(query)
    PATH = f"{year}/{race}/pitstops.json"
    url = urlunsplit((SCHEME, BASE, PATH, QUERY, ""))
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def pitstop_api_petition(year, race):
    jresposnse = make_url_and_petition(year, race)
    total = int(jresposnse["MRData"]["total"])
    if total == 0:
        if year != 2021 or race != 12:
            raise NoMoreRaces
        else:
            return
    pitstop_info = jresposnse["MRData"]["RaceTable"]["Races"][0]["PitStops"]
    if total > 30:
        times = total // 30 if total % 30 != 0 else total // 30 - 1
        for i in range(times):
            jresposnse = make_url_and_petition(year, race, {"offset": (i + 1) * 30})
            pitstop_info += jresposnse["MRData"]["RaceTable"]["Races"][0]["PitStops"]

    return pitstop_info
    # with open(f"race_{race}_{year}_pitstops.json", "w") as f:
    #     json.dump(pitstop_info, f)


def obtain_numbers(number_df, driver_df):
    regex = re.compile(r"(.+)\s+([^\[\]]+)(\[[.*]\])?")
    name_format = lambda s: "".join(
        c
        for c in unicodedata.normalize("NFKD", regex.search(s).group(2).lower())
        if not unicodedata.combining(c)
    )
    number_df["driverId"] = number_df["Pilotos"].apply(name_format)
    number_df.replace({"d'ambrosio": "ambrosio"}, inplace=True)
    driver_df_copy = driver_df.copy()
    driver_df_copy["driverId"] = driver_df_copy["driverId"].apply(
        lambda x: x.split("_")[-1]
    )
    final_df = driver_df_copy[["driverId"]].merge(
        number_df[["N.º", "driverId"]], on="driverId"
    )
    final_df = final_df.sort_values(by="driverId")
    final_df["driverId"] = driver_df["driverId"].sort_values()
    final_df.rename({"N.º": "permanentNumber"}, inplace=True, axis=1)
    return final_df.reset_index().drop("index", axis=1)


def obtain_driver_df(driverpath, year):
    driver_info = requests.get(f"{SCHEME}://{BASE}/{year}/drivers.json").json()
    driver_df = pd.DataFrame(driver_info["MRData"]["DriverTable"]["Drivers"])[
        ["driverId", "permanentNumber"]
    ]

    if year in [2012, 2013, 2014]:
        url = f"https://es.wikipedia.org/wiki/Temporada_{year}_de_F%C3%B3rmula_1"
        response = requests.get(url)
        text = response.content.decode("utf-8")
        soup = BeautifulSoup(text, "html.parser")
        table = soup.find("table", {"class": "wikitable"})
        dfs = pd.read_html(io.StringIO(str(table)))
        number_df = dfs[0]
        driver_df = obtain_numbers(number_df, driver_df)

    driver_df.to_csv(driverpath)
    return driver_df


def create_pitstops_csv():
    for year in range(2012, 2024):
        folder_name = f"races_{year}"
        os.makedirs(folder_name, exist_ok=True)
        try:
            driverpath = os.path.join(folder_name, f"drivers_{year}.csv")
            if not os.path.exists(driverpath):
                driver_df = obtain_driver_df(driverpath, year)

            else:
                driver_df = pd.read_csv(driverpath, index_col=0)

            race = 1
            while True:
                filename = f"race_{race}_{year}.csv"
                filepath = os.path.join(folder_name, filename)
                if not os.path.exists(filepath):
                    pitstop_info = pitstop_api_petition(year, race)
                    if pitstop_info:
                        pitstop_df = pd.DataFrame(pitstop_info)
                        for column in ["lap", "stop", "duration"]:
                            pitstop_df[column] = pd.to_numeric(
                                pitstop_df[column], errors="coerce"
                            )
                        final_pitstop_df = pd.DataFrame(
                            pitstop_df.groupby("driverId").agg(
                                {"stop": "max", "duration": "median"}
                            )
                        ).reset_index()
                    else:
                        final_pitstop_df = pd.DataFrame(
                            {
                                "driverId": ["alonso"],
                                "stop": [""],
                                "duration": [""],
                            },
                        )
                    final_df = final_pitstop_df.merge(
                        driver_df, on="driverId", how="outer"
                    )
                    if year in [2022, 2023]:
                        final_df.loc[
                            final_df["driverId"] == "max_verstappen", "permanentNumber"
                        ] = 1
                    final_df.to_csv(filepath)

                # Aqui va la parte del dataframe
                race += 1

        except NoMoreRaces:
            pass
        except Exception as e:
            print(f"Se ha producido un error: {e}")


create_pitstops_csv()
