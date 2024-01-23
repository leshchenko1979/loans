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


@retry(tries=3, delay=3)
def get_ss(ss_key: str, name: str = None):
    service_string = os.environ["GOOGLE_SERVICE_ACCOUNT"]
    service_dict = json.loads(service_string)
    gc = gspread.service_account_from_dict(service_dict)

    return gc.open_by_key(ss_key)


@app.post("/")
def main():
    # get worksheets

    ss = get_ss(os.environ["SPREADSHEET_ID"])
    investor_apps = ss.worksheet("Заявки инвесторов")

    # load data

    data = pd.DataFrame(investor_apps.get_all_records())

    data = process_data(data, request.json)

    # put the table back into Google Sheets

    investor_apps.update([data.columns.values.tolist()] + data.values.tolist())

    return "Done"

def process_data(data: pd.DataFrame, new_data: dict):
    # add new data

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

    return data

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

    data["Ранг"] = [(i + 1 if not n else "") for i, n in zip(data.index, data.nans)]

    return data
