import pandas as pd
import pytest
from flask_app import process_data


# Assuming update_rankings is a function that updates the "Ранг" field based on some logic
def update_rankings(data):
    # Dummy implementation for testing purposes
    data["Ранг"] = range(1, len(data) + 1)
    return data


# Mock the MAPPING and FIELD_ORDER constants
MAPPING = {
    "CUserID": "id",
    "Имя": "name",
    "Ставка": "rate",
    "Сумма": "amount",
    "Ранг": "rank",
}
FIELD_ORDER = ["CUserID", "Имя", "Ставка", "Сумма", "Ранг"]


@pytest.mark.parametrize(
    "existing_data, new_data, expected",
    [
        # Happy path test cases
        pytest.param(
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Имя": ["Alice", "Bob"],
                    "Ставка": ["10%", "20%"],
                    "Сумма": ["100 млн.", "200 млн."],
                    "Ранг": ["1", "2"],
                }
            ),
            {
                "cuid": "3",
                "name": "Charlie",
                "Фонд_ставка_текст": "30%",
                "Фонд_сумма_текст": "300 млн.",
            },
            pd.DataFrame(
                {
                    "CUserID": ["1", "2", "3"],
                    "Имя": ["Alice", "Bob", "Charlie"],
                    "Ставка": ["10%", "20%", "30%"],
                    "Сумма": ["100 млн.", "200 млн.", "300 млн."],
                    "Ранг": [1, 2, 3],
                }
            ),
            id="happy_path",
        ),
        # Edge case: Adding a duplicate user should remove the old entry
        pytest.param(
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Имя": ["Alice", "Bob"],
                    "Ставка": ["10%", "20%"],
                    "Сумма": ["100 млн.", "200 млн."],
                    "Ранг": ["1", "2"],
                }
            ),
            {
                "cuid": "2",
                "name": "Bob",
                "Фонд_ставка_текст": "25%",
                "Фонд_сумма_текст": "250 млн.",
            },
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Имя": ["Alice", "Bob"],
                    "Ставка": ["10%", "25%"],
                    "Сумма": ["100 млн.", "250 млн."],
                    "Ранг": [1, 2],
                }
            ),
            id="edge_case_duplicate_user",
        ),
        # Error case: Missing MAPPING keys in new_data
        pytest.param(
            pd.DataFrame(
                {
                    "CUserID": [1],
                    "Имя": ["Alice"],
                    "Ставка": [10],
                    "Сумма": [100],
                    "Ранг": [1],
                }
            ),
            {"cuid": 2, "name": "Bob"},
            KeyError,
            id="error_case_missing_keys",
        ),
    ],
)
def test_process_data(existing_data, new_data, expected):
    # Arrange
    # (Omitted since all input values are provided via test parameters)

    # Act
    if isinstance(expected, pd.DataFrame):
        result = process_data(existing_data, new_data)
    else:
        with pytest.raises(expected):
            process_data(existing_data, new_data)
        return

    # Assert
    pd.testing.assert_frame_equal(
        result.reset_index(drop=True), expected.reset_index(drop=True)
    )