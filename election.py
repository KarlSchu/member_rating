#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
r"""
Reads the election data from a xlsx file and creates sorted list of candidates.
KarlSchu, 2025

pyinstaller --onefile --windowed --icon=a.ico election.py 
pyinstaller --onefile --windowed election.py -o dist --add-data "style.css;." --add-data "NachwahlProzedere.md;." 
"""
from datetime import datetime as dt
from io import StringIO
from markdown.extensions.tables import TableExtension
from random import randint
import csv
import markdown
import os
import pandas as pd
import re
import sys


excluded_members = []

timestamp = dt.now().strftime("%Y%m%d")  # or '%Y%m%d_%H%M%S'
timestamp_long = dt.now().strftime("%d.%m.%Y, %H:%M:%S")
data_file = "Mitglieder.xlsx"
out_md = f"candidates_{timestamp}.md"
out_pdf = f"candidates_{timestamp}.pdf"
out_html = f"candidates_{timestamp}.html"


def is_float(element: any):
    if element is None:
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False


def whitespace_remover(dataframe):
    # iterating over the columns
    for i in dataframe.columns:
        # checking datatype of each columns
        if type(dataframe[i]) is pd.core.series.Series:
            # applying strip function on column
            dataframe[i] = dataframe[i].map(str.strip)
        else:
            pass


def read_election_data(file_path):
    if file_path.endswith(".tsv"):
        return read_election_data_from_tsv(file_path)
    elif file_path.endswith(".xlsx") or file_path.endswith(".xlsx"):
        return read_election_data_from_exls(file_path)
    else:
        raise ValueError(
            "Unsupported file format. Please provide a '.tsv' or '.xlsx' file."
        )


def read_election_data_from_exls(file_path):
    """
    Reads the election data from a exls file and returns a dictionary of candidates and their votes.
    """
    global excluded_members
    members = {}
    data = pd.read_excel(file_path, sheet_name=0, header=0)

    data.fillna(0, inplace=True)  # fill NaN values with empty strings
    data.columns = data.columns.str.strip()
    header = data.columns.str.strip()

    for index, row in data.iterrows():
        if row["Nachname"].startswith("#"):
            row["Zuzug"] = "-"
            excluded_members.append(row)
            continue
        adr = row["Grundstück"].strip()
        street = adr.strip().split(" ")[0]
        number = adr.strip().split(" ")[1].strip()
        key = f"{street} {number}"
        ext = ""
        while key in members.keys():
            ext += "'"  # chr(ord(ext) + 1)
            key = f"{street} {number}{ext}"
        members[key] = row

    # whitespace_remover(data)
    return header, members


def read_election_data_from_tsv(file_path):
    """
    Reads the election data from a TSV file and returns a dictionary of candidates and their votes.
    """
    global excluded_members
    members = {}
    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file, delimiter="\t")
        header = ""
        rows = [{k.strip(): v.strip() for k, v in row.items()} for row in reader]
        for index, row in enumerate(rows):
            if index == 0:
                header = row.keys()
                continue
            if row["Nachname"].startswith("#"):
                excluded_members.append(row)
                continue
            adr = row["Grundstück"]
            street = adr.strip().split(" ")[0]
            number = int(adr.strip().split(" ")[1])
            key = f"{street} {number:02d}"
            ext = ""
            while key in members.keys():
                ext += "'"  # chr(ord(ext) + 1)
                key = f"{street} {number:02d}{ext}"
            members[key] = row
    return header, members


def select_candidates(header, members):
    """
    Selects candidates from the members dictionary based on the number of votes.
    """
    global excluded_members

    candidates = {}
    for item in members:
        welpenschutz = dt.now().year - int(item[1]["Zuzug"])
        if welpenschutz < 2:
            item[1]["Zuzug"] = welpenschutz
            excluded_members.append(item[1])
            continue
        item[1]["Zuzug"] = "-"
        if item[1]["Altersbonus"] == "x":
            excluded_members.append(item[1])
            continue
        if item[1]["Fitnessbonus"] == "x":
            excluded_members.append(item[1])
            continue
        if item[1]["Ausschluss"] == "x":
            excluded_members.append(item[1])
            continue
        if item[1]["Aktiver Vorstand"] == "x":
            excluded_members.append(item[1])
            continue
        value = item[1]["Aktivjahre gesamt"]
        active_years = 4 * float(value) if is_float(value) else 0
        if active_years > 90:
            active_years = 90
        rating = 100 - active_years - randint(1, 10)
        item[1]["Rating"] = rating
        candidates[item[0]] = item[1]
    return candidates


def main(data_file):
    header, members = read_election_data(data_file)
    out_path = os.path.dirname(os.path.abspath(data_file))

    # Sort the candidates by rating
    sorted_members = sorted(members.items(), key=lambda x: x[0])

    candidates = select_candidates(header, sorted_members)
    candidates = sorted(candidates.items(), key=lambda x: x[1]["Rating"], reverse=True)

    with open(
        os.path.join("..", "nachwahl_data", "NachwahlProzedere.md"),
        "r",
        encoding="UTF8",
    ) as f:
        results = f.read()
    results += '\n<p class="pagebreak" />\n\n'
    results += f"#### Legende\n\n"
    results += "- 📆 ... Mitgliedsjahre im Vorstand\n"
    results += "- 🕯️ ... Altersbonus\n"
    results += "- 🦾 ... Fitnessbonus\n"
    results += "- 📍 ... Zur Zeit aktiv im Vorstand\n"
    results += "- 🐕 ... Jahre im Verein, wenn < 2, dann Wartefrist\n"
    results += "- 🚧 ... Gesperrt\n"
    results += "- 🌡️ ... Rating\n"
    results += "\n"
    results += f"#### Rating für {len(candidates)} Kandidaten per {timestamp_long}\n\n"
    global_header1 = f"|{'Grundstück':20}|{'Parzelle':9}|{'Namen':42}|{'🐕':1}|{'📆':2}|{'📍':1}|{'🕯️':1} |{'🦾':1}|{'🚧':1}|"
    global_header2 = f"|{'-'*20}|{'-'*9}|{'-'*42}|--|---|--|--|--|--|"
    results += f"{global_header1}{'🌡️':3}|\n"
    results += f"{global_header2}--|\n"
    for member, data in candidates:
        namen = f'{data['Nachname'].strip()}, {data["Vorname"].strip()}'
        parzelle = f"{data['Parzellen-Nr.']}".strip()
        results += f"|{member:20}|{parzelle:9}|{namen:42}|{data['Zuzug']:2}|{data['Aktivjahre gesamt']:3.0f}| {data['Aktiver Vorstand']:1}| {data['Altersbonus']:1}| {data['Fitnessbonus']:1}| {data['Ausschluss']:1}|{data['Rating']:2.0f}|\n"

    results += '\n<p class="pagebreak" />\n\n'
    results += f"#### Nichtberücksichtigte Mitglieder und aktiver Vorstand ({len(excluded_members)})\n\n"
    results += f"{global_header1}\n"
    results += f"{global_header2}\n"
    excluded_members_sorted = sorted(
        excluded_members, key=lambda x: x["Nachname"], reverse=False
    )
    for data in excluded_members_sorted:
        namen = f'{data['Nachname'].strip()}, {data["Vorname"].strip()}'
        parzelle = f"{data['Parzellen-Nr.']}".strip()
        results += f"|{data['Grundstück']:20}|{parzelle:9}|{namen:42}|{data['Zuzug']:2}|{data['Aktivjahre gesamt']:3.0f}| {data['Aktiver Vorstand']:1}| {data['Altersbonus']:1}| {data['Fitnessbonus']:1}| {data['Ausschluss']:1}|\n"
    results = results.replace(" 0|", "  |")
    with open(os.path.join(out_path, out_md), "w", encoding="UTF8") as f:
        f.write(results)
    print(results)
    print(f"Results written to '{os.path.join(out_path, out_md)}'")

    html = markdown.markdown(
        results,
        verbose=True,
        extensions=[TableExtension(use_align_attribute=True), "toc"],
    )
    html = f"""
<!DOCTYPE html>
<html>
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>Wahlkandidaten {timestamp} 🙋🏽‍♂️</title>
    <link rel="stylesheet" href="style.css"/>
    </head>
    <body>
        {html}
    </body>
</html>
""".replace(
        "<table>", '<table class="candidates">'
    )
    with open(os.path.join(out_path, out_html), "w") as f:
        f.write(html)
    print(f"HTML written to '{os.path.join(out_path, out_html)}'")

    from weasyprint import HTML, CSS

    HTML(string=html).write_pdf(
        os.path.join(out_path, out_pdf),
        stylesheets=[CSS("style.css")],
        presentational_hints=True,
        encoding="UTF-8",
    )

    print(f"PDF written to '{os.path.join(out_path, out_pdf)}'")
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        data_file = os.path.join("..", "nachwahl_data", "mitglieder.xlsx")
        print(f"No file provided, using default '{data_file}'")

    if not (
        data_file.endswith(".tsv") or data_file.endswith(".xlsx")
    ) or not os.path.exists(data_file):
        print("Please provide a valid file with '.tsv' or '.xlsx' extension.")
        sys.exit(1)

    print(f"Reading election data from '{data_file}'")

    main(data_file)
