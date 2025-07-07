# data-analyst-agent/app.py

import io
import base64
from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.post("/api/")
async def analyze(file: UploadFile):
    task = await file.read()
    task_text = task.decode("utf-8").lower()

    if "highest grossing films" in task_text:
        return await analyze_movies(task_text)

    return JSONResponse({"error": "Unsupported task"}, status_code=400)


async def analyze_movies(task_text):
    url = "https://en.wikipedia.org/wiki/List_of_highest-grossing_films"
    df = scrape_movie_data(url)

    two_billion = df[(df["Worldwide gross"] >= 2_000_000_000) & (df["Year"] < 2020)]
    ans1 = len(two_billion)

    over_1_5bn = df[df["Worldwide gross"] >= 1_500_000_000]
    earliest = over_1_5bn.sort_values("Year").iloc[0]["Title"]

    correlation = np.corrcoef(df["Rank"], df["Peak"])[0, 1]

    img_base64 = generate_plot(df)

    return [ans1, earliest, round(correlation, 6), img_base64]


def scrape_movie_data(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", {"class": "wikitable"})

    rows = table.find_all("tr")
    data = []
    for row in rows[1:]:
        cols = row.find_all(["td", "th"])
        if len(cols) < 5:
            continue
        rank = int(cols[0].text.strip().split()[0])
        title = cols[1].text.strip()
        gross_str = cols[2].text.strip().replace("$", "").replace(",", "").replace(" billion", "").replace(" million", "")
        gross = float(gross_str) * (1_000_000_000 if "billion" in cols[2].text.lower() else 1_000_000)
        year = int(cols[3].text.strip())
        peak = int(cols[4].text.strip())
        data.append([rank, title, gross, year, peak])

    return pd.DataFrame(data, columns=["Rank", "Title", "Worldwide gross", "Year", "Peak"])


def generate_plot(df):
    plt.figure(figsize=(6, 4))
    sns.scatterplot(data=df, x="Rank", y="Peak", s=40)
    sns.regplot(data=df, x="Rank", y="Peak", scatter=False, color="red", linestyle="dotted")
    plt.xlabel("Rank")
    plt.ylabel("Peak")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"
