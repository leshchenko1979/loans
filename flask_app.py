print("Starting imports")

import datetime
import json
import logging
import os
from dataclasses import dataclass, field, fields, asdict

import dotenv
import gspread
from flask import Flask, request
from reretry import retry

import yandex_logging

dotenv.load_dotenv()

app = Flask(__name__)

NEW_APP_FIELD_MAPPING = {
    "rate": "Фонд_ставка_текст",
    "amount": "Фонд_сумма_текст",
}


@dataclass
class Application:
    cuid: str
    name: str
    rate: str
    amount: str
    phone: str
    telegram: str = ""
    created_at: str = ""
    rank: int = 0
    other_fields: list = field(default_factory=list)

    @staticmethod
    def from_json(json_data: dict, **kwargs):
        data_dict = {
            key: value for key, value in json_data.items() if key in FIELD_NAMES
        }
        data_dict |= {
            key: json_data[value] for key, value in NEW_APP_FIELD_MAPPING.items()
        }
        self = Application(**data_dict)

        self.created_at = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.telegram = "https://t.me/" + json_data["messenger_username"]

        # Overwite from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        return self

    @staticmethod
    def from_line(line: list[str]):
        return Application(*line[:MAIN_FIELDS], other_fields=line[MAIN_FIELDS:])


MAIN_FIELDS = len(fields(Application)) - 1
FIELD_NAMES = [field.name for field in fields(Application)]

def dict_to_app_list(app_dict: dict) -> list[Application]:
    return [Application.from_line(line) for line in dict_to_list_of_lines(app_dict)]


def dict_to_list_of_lines(data_dict: dict) -> list[list[str]]:
    other_fields = set(data_dict.keys()) - set(FIELD_NAMES)
    ordered_col_list = [*FIELD_NAMES[:MAIN_FIELDS], *other_fields]
    return list(zip(*[data_dict[key] for key in ordered_col_list]))


@app.post("/")
def main():
    logging.debug("Start loading data")

    ss: gspread.Spreadsheet = get_ss(os.environ["SPREADSHEET_ID"])
    investor_apps = ss.worksheet("Заявки инвесторов")

    first_line, data = load_data(investor_apps)

    logging.debug(f"{len(data)} lines downloaded from Google")

    logging.info(f"Request: {request.json}", extra={"request": request.json})

    data = process_data(data, request.json)

    lines = stretch_to_max_len([first_line] + data_to_lines(data))
    investor_apps.update(lines)

    logging.debug(f"{len(data)} lines uploaded to Google")

    return "Done"


def load_data(investor_apps: gspread.Worksheet):
    all_lines = investor_apps.get_all_values()
    first_line = all_lines[0]
    data = [Application.from_line(line) for line in all_lines[1:]]

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
    return data + [Application.from_json(new_data)]


def dedup(data):
    return list({app.cuid: app for app in data}.values())


def update_rankings(data: list[Application]):
    """Update rankings"""

    rate_and_amount_to_numbers(data)

    # sort and calculate the ranking

    data.sort(key=lambda app: app.rate)

    for i, app in enumerate(data):
        app.rank = i + 1

    return data


def rate_and_amount_to_numbers(data: list[Application]):
    for app in data:
        # turn numeric columns into numericals
        try:
            app.rate = int(app.rate.replace("%", ""))
        except ValueError:
            app.rate = 0

        try:
            app.amount = int(app.amount.replace(" млн.", ""))
        except ValueError:
            app.amount = 0


def ensure_gsheets_safety(data: list[Application]):
    """Make data safe for placing into Google Sheets.

    If gspread gets nans in input, it raises a JSONEncode exception.
    """

    for app in data:
        app.rate = f"{app.rate}%"
        app.amount = f"{app.amount} млн."

    return data


def stretch_to_max_len(lines: list[list]):
    max_len = len(max(lines, key=len))
    return [[*line, *([""] * (max_len - len(line)))] for line in lines]


def data_to_lines(data: list[Application]):
    return [(*list(asdict(app).values())[:-1], *app.other_fields) for app in data]


if __name__ == "__main__":
    main()
