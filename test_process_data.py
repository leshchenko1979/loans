import numpy as np
import pandas as pd
import pytest

from flask_app import process_data, split_comments


# Assuming update_rankings is a function that updates the "Ранг" field based on some logic
def update_rankings(data):
    # Dummy implementation for testing purposes
    data["Ранг"] = range(1, len(data) + 1)
    return data


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
                    "Телефон": ["000000000000", "000000000000"],
                    "Ранг": ["1", "2"],
                }
            ),
            {
                "cuid": "3",
                "name": "Charlie",
                "Фонд_ставка_текст": "30%",
                "Фонд_сумма_текст": "300 млн.",
                "phone": "81231231212",
            },
            pd.DataFrame(
                {
                    "CUserID": ["1", "2", "3"],
                    "Имя": ["Alice", "Bob", "Charlie"],
                    "Ставка": ["10%", "20%", "30%"],
                    "Сумма": ["100 млн.", "200 млн.", "300 млн."],
                    "Телефон": ["000000000000", "000000000000", "81231231212"],
                    "Ранг": [1, 2, 3],
                }
            ),
            id="happy_path",
        ),
        # Happy path: Keep incoming comments
        pytest.param(
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Имя": ["Alice", "Bob"],
                    "Ставка": ["10%", "20%"],
                    "Сумма": ["100 млн.", "200 млн."],
                    "Телефон": ["000000000000", "000000000000"],
                    "Ранг": ["1", "2"],
                    "Комментарии": ["Это Алиса", "Это Боб"],
                }
            ),
            {
                "cuid": "3",
                "name": "Charlie",
                "Фонд_ставка_текст": "30%",
                "Фонд_сумма_текст": "300 млн.",
                "phone": "000000000000",
            },
            pd.DataFrame(
                {
                    "CUserID": ["1", "2", "3"],
                    "Имя": ["Alice", "Bob", "Charlie"],
                    "Ставка": ["10%", "20%", "30%"],
                    "Сумма": ["100 млн.", "200 млн.", "300 млн."],
                    "Телефон": ["000000000000", "000000000000", "000000000000"],
                    "Ранг": [1, 2, 3],
                    "Комментарии": ["Это Алиса", "Это Боб", np.nan],
                }
            ),
            id="happy_path_keep_comments",
        ),
        # Edge case: Adding a duplicate user should remove the old entry
        pytest.param(
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Имя": ["Alice", "Bob"],
                    "Ставка": ["10%", "20%"],
                    "Сумма": ["100 млн.", "200 млн."],
                    "Телефон": ["000000000000", "000000000000"],
                    "Ранг": ["1", "2"],
                }
            ),
            {
                "cuid": "2",
                "name": "Bob",
                "Фонд_ставка_текст": "25%",
                "Фонд_сумма_текст": "250 млн.",
                "phone": "000000000000",
            },
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Имя": ["Alice", "Bob"],
                    "Ставка": ["10%", "25%"],
                    "Сумма": ["100 млн.", "250 млн."],
                    "Телефон": ["000000000000", "000000000000"],
                    "Ранг": [1, 2],
                }
            ),
            id="edge_case_duplicate_user",
        ),
        # Edge case: A missing column in existing_data should be added to new_data
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
                "phone": "000000000000",
            },
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Имя": ["Alice", "Bob"],
                    "Ставка": ["10%", "25%"],
                    "Сумма": ["100 млн.", "250 млн."],
                    "Телефон": ["", "000000000000"],
                    "Ранг": [1, 2],
                }
            ),
            id="edge_case_missing_col",
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

    print(result)

    # Assert
    pd.testing.assert_frame_equal(
        result.reset_index(drop=True), expected.reset_index(drop=True)
    )


@pytest.mark.parametrize(
    "data, expected_data, comments",
    [
        pytest.param(
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Имя": ["Alice", "Bob"],
                    "Ставка": ["10%", "20%"],
                    "Сумма": ["100 млн.", "200 млн."],
                    "Ранг": ["1", "2"],
                    "Комментарии": ["Это Алиса", "Это Боб"],
                }
            ),
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Имя": ["Alice", "Bob"],
                    "Ставка": ["10%", "20%"],
                    "Сумма": ["100 млн.", "200 млн."],
                    "Ранг": ["1", "2"],
                }
            ),
            pd.DataFrame(
                {"CUserID": ["1", "2"], "Комментарии": ["Это Алиса", "Это Боб"]}
            ),
            id="happy_path"
        ),
        pytest.param(
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Имя": ["Alice", "Bob"],
                    "Ставка": ["10%", "20%"],
                    "Сумма": ["100 млн.", "200 млн."],
                    "Ранг": ["1", "2"],
                    "Комментарии": ["Это Алиса", "Это Боб"],
                    "": ["", "Ещё комментарии"],
                }
            ),
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Имя": ["Alice", "Bob"],
                    "Ставка": ["10%", "20%"],
                    "Сумма": ["100 млн.", "200 млн."],
                    "Ранг": ["1", "2"],
                }
            ),
            pd.DataFrame(
                {
                    "CUserID": ["1", "2"],
                    "Комментарии": ["Это Алиса", "Это Боб"],
                    "": ["", "Ещё комментарии"],
                }
            ),
            id="edge_case_2_columns"
        ),
    ],
)
def test_split_comments(data, expected_data, comments):
    result_expected_data, result_comments = split_comments(data)

    print(result_expected_data)
    print(result_comments)

    pd.testing.assert_frame_equal(
        result_expected_data.reset_index(drop=True),
        expected_data.reset_index(drop=True),
    )
    pd.testing.assert_frame_equal(
        result_comments.reset_index(drop=True), comments.reset_index(drop=True)
    )
