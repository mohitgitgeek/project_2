import pandas as pd
import requests
from bs4 import BeautifulSoup
import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import re

async def process_task(task_text):
    if "highest grossing films" in task_text:
        return await process_film_task(task_text)
    elif "Indian high court judgement" in task_text:
        return await process_court_task(task_text)
    else:
        raise ValueError("Unknown task format")

async def process_film_task(task_text):
    url_match = re.search(r'https?://[^\s]+', task_text)
    url = url_match.group(0)

    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = pd.read_html(resp.text)

    df = tables[0]  # Assuming first table is correct

    # Cleanup columns for consistency
    df.columns = [str(c).lower() for c in df.columns]

    # Example answers:
    df['worldwide gross'] = df['worldwide gross'].str.replace(r'[^0-9.]', '', regex=True).astype(float)
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    
    # $2bn movies before 2020
    q1 = df[(df['worldwide gross'] >= 2_000_000_000) & (df['year'] < 2020)].shape[0]

    # Earliest $1.5bn movie
    df_15 = df[df['worldwide gross'] >= 1_500_000_000]
    q2 = df_15.sort_values('year').iloc[0]['title']

    # Rank vs Gross correlation
    df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
    corr = df[['rank', 'worldwide gross']].corr().iloc[0, 1]

    # Scatterplot
    plt.figure(figsize=(6, 4))
    sns.scatterplot(x='rank', y='worldwide gross', data=df)
    sns.regplot(x='rank', y='worldwide gross', data=df, scatter=False, color='red', line_kws={"linestyle": "dotted"})
    plt.xlabel("Rank")
    plt.ylabel("Worldwide Gross")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plot_b64 = base64.b64encode(buf.read()).decode()
    data_uri = f"data:image/png;base64,{plot_b64}"

    return [q1, q2, round(corr, 6), data_uri]
