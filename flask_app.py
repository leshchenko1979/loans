print("Starting imports")

import json
import logging
import os
from collections import namedtuple

import dotenv
import gspread
from flask import Flask, request
from reretry import retry

import yandex_logging

dotenv.load_dotenv()

app = Flask(__name__)

NEW_APP_FIELD_MAPPING = {
    "cuid": "cuid",
    "name": "name",
    "rate": "Фонд_ставка_текст",
    "amount": "Фонд_сумма_текст",
    "phone": "phone",
}


Application = namedtuple(
    "Application", "cuid, name, rate, amount, phone, rank, other_fields"
)


MAIN_FIELDS = len(Application._fields) - 1


def line_to_app(fields: list[str]) -> Application:
    return Application(*fields[:MAIN_FIELDS], other_fields=fields[MAIN_FIELDS:])


def dict_to_app_list(app_dict: dict) -> list[Application]:
    return [line_to_app(line) for line in dict_to_list_of_lines(app_dict)]


def dict_to_list_of_lines(data_dict: dict) -> list[list[str]]:
    other_fields = set(data_dict.keys()) - set(Application._fields)
    ordered_col_list = [*Application._fields[:MAIN_FIELDS], *other_fields]
    return list(zip(*[data_dict[key] for key in ordered_col_list]))


@app.post("/")
def main():
    logging.debug("Start loading data")

    ss: gspread.Spreadsheet = get_ss(os.environ["SPREADSHEET_ID"])
    investor_apps = ss.worksheet("Заявки инвесторов")

    first_line, data = load_data(investor_apps)

    logging.debug(f"{len(data)} lines downloaded from Google")

    logging.info("Request: {request.json}")

    data = process_data(data, request.json)

    lines = stretch_to_max_len([first_line] + data_to_lines(data))
    investor_apps.update(lines)

    logging.debug(f"{len(data)} lines uploaded to Google")

    return "Done"


def load_data(investor_apps: gspread.Worksheet):
    all_lines = investor_apps.get_all_values()
    first_line = all_lines[0]
    data = [line_to_app(line) for line in all_lines[1:]]

    return first_line, data


@retry(tries=3, delay=3)
def get_ss(ss_key: str) -> gspread.Spreadsheet:
    """Get a spreadsheets from Google by a spreadsheet key."""

    service_string = os.environ["GOOGLE_SERVICE_ACCOUNT"]
    service_dict = json.loads(service_string)
    gc = gspread.service_account_from_dict(service_dict)

    return gc.open_by_key(ss_key)


def process_data(data: list[Application], new_data: dict):
    """Process the data by adding new data, deduplicating, updating rankings,
    and ensuring Google Sheets safety.
    """

    data = add_new_data(data, new_data)
    data = dedup(data)
    data = update_rankings(data)
    data = ensure_gsheets_safety(data)

    return data


def add_new_data(data, new_data):
    mapped = {
        col: new_data[NEW_APP_FIELD_MAPPING[col]] for col in NEW_APP_FIELD_MAPPING
    }
    return data + [Application(**mapped, rank="", other_fields=[])]


def dedup(data):
    return list({app.cuid: app for app in data}.values())


def update_rankings(data: list[Application]):
    """Update rankings"""

    rate_and_amount_to_numbers(data)

    # sort and calculate the ranking

    data.sort(key=lambda app: app.rate)

    for i, app in enumerate(data):
        data[i] = data[i]._replace(rank=i + 1)

    return data


def rate_and_amount_to_numbers(data: list[Application]):
    for i, app in enumerate(data):
        # turn numeric columns into numericals
        try:
            rate = int(app.rate.replace("%", ""))
        except ValueError:
            rate = 0

        try:
            amount = int(app.amount.replace(" млн.", ""))
        except ValueError:
            amount = 0

        data[i] = data[i]._replace(rate=rate, amount=amount)


def ensure_gsheets_safety(data):
    """Make data safe for placing into Google Sheets.

    If gspread gets nans in input, it raises a JSONEncode exception.
    """

    for i, app in enumerate(data):
        data[i] = data[i]._replace(rate=f"{app.rate}%", amount=f"{app.amount} млн.")

    return data


def stretch_to_max_len(lines: list[list]):
    max_len = len(max(lines, key=len))
    return [[*line, *([""] * (max_len - len(line)))] for line in lines]


def data_to_lines(data: list[Application]):
    return [(*list(app._asdict().values())[:-1], *app.other_fields) for app in data]


if __name__ == "__main__":
    main()
