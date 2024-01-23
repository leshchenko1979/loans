print("Starting imports")

from flask import Flask, request
import gspread
from reretry import retry
import pandas as pd
import dotenv
import os
import json

dotenv.load_dotenv()

app = Flask(__name__)

MAPPING = {
    "CUserID": "cuid",
    "Ставка": "Фонд_ставка_текст",
    "Сумма": "Фонд_сумма_текст",
    "Имя": "name",
}


@app.post("/")
def main():
    # get worksheets

    print("Start loading data")

    ss = get_ss(os.environ["SPREADSHEET_ID"])
    investor_apps = ss.worksheet("Заявки инвесторов")

    # load data

    data = pd.DataFrame(investor_apps.get_all_records())

    print(len(data), "lines downloaded from Google")

    print("Request:", request.json)

    # process data

    data = process_data(data, request.json)

    # put the table back into Google Sheets

    investor_apps.update([data.columns.values.tolist()] + data.values.tolist())

    print(len(data), "lines uploaded to Google")

    return "Done"


@retry(tries=3, delay=3)
def get_ss(ss_key: str):
    service_string = os.environ["GOOGLE_SERVICE_ACCOUNT"]
    service_dict = json.loads(service_string)
    gc = gspread.service_account_from_dict(service_dict)

    return gc.open_by_key(ss_key)


def process_data(data: pd.DataFrame, new_data: dict):
    # add new data

    data, comments = split_comments(data)

    data = pd.concat(
        [data, pd.DataFrame([{col: new_data[MAPPING[col]] for col in MAPPING}])]
    )

    # dedup the data

    data = data.drop_duplicates("CUserID", keep="last")

    data = update_rankings(data)

    # ensure field order
    FIELD_ORDER = ["CUserID", "Имя", "Ставка", "Сумма", "Ранг"]
    data = data[FIELD_ORDER]

    # turn back into strings

    data["Ставка"] = [
        f"{int(rate)}%" if pd.notna(rate) else 0 for rate in data["Ставка"]
    ]
    data["Сумма"] = [
        f"{int(sum)} млн." if pd.notna(sum) else 0 for sum in data["Сумма"]
    ]

    if comments is not None:
        data = restore_comments(data, comments)

    return data


def split_comments(data: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
    """Split all columns starting with "Комментарии" into a separate dataframe."""

    if "Комментарии" not in data:
        return data, None

    ncol = data.columns.get_loc("Комментарии")
    return data.iloc[:, :ncol], pd.concat(
        [data["CUserID"], data.iloc[:, ncol:]], axis="columns"
    )


def restore_comments(data: pd.DataFrame, comments: pd.DataFrame) -> pd.DataFrame:
    """Merge comments into the new data based on the CUserID field as index."""

    return pd.merge(data, comments, how="left", on="CUserID")


def update_rankings(data):
    # update rankings in the table

    # turn numeric columns into numericals

    for col in ["Ставка", "Сумма"]:
        data[col] = data[col].str.extract("(\d+)").astype(float)

    # pick out indexes of NaNs

    data["nans"] = pd.isna(data["Ставка"]) | pd.isna(data["Сумма"])

    # sort and calculate the ranking

    data = data.sort_values(["nans", "Ставка", "Сумма"], ascending=[True, True, False])

    data = data.reset_index(drop=True)

    data["Ранг"] = [("" if nan else i + 1) for i, nan in zip(data.index, data.nans)]

    return data
