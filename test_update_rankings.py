import numpy as np
import pandas as pd
import pytest

from flask_app import update_rankings

# Test IDs for parametrization
happy_path_ids = [
    "numeric_values",
    "sorted_input",
    "unsorted_input",
]

edge_case_ids = [
    "single_row",
    "all_nans",
]

error_case_ids = [
    "empty_dataframe",
    "non_string_columns",
    "missing_columns",
]


@pytest.mark.parametrize(
    "input_data, expected",
    [
        (
            pd.DataFrame({"Ставка": ["10", "20"], "Сумма": ["100", "200"]}),
            pd.DataFrame(
                {
                    "Ставка": [10.0, 20.0],
                    "Сумма": [100.0, 200.0],
                    "nans": [False, False],
                    "Ранг": [1, 2],
                }
            ),
        ),
        (
            pd.DataFrame({"Ставка": ["10", "20"], "Сумма": ["200", "100"]}),
            pd.DataFrame(
                {
                    "Ставка": [10.0, 20.0],
                    "Сумма": [200.0, 100.0],
                    "nans": [False, False],
                    "Ранг": [1, 2],
                }
            ),
        ),
        (
            pd.DataFrame({"Ставка": ["20", "10"], "Сумма": ["100", "200"]}),
            pd.DataFrame(
                {
                    "Ставка": [10.0, 20.0],
                    "Сумма": [200.0, 100.0],
                    "nans": [False, False],
                    "Ранг": [1, 2],
                }
            ),
        ),
    ],
    ids=happy_path_ids,
)
def test_update_rankings_happy_path(input_data, expected):
    # Act
    result = update_rankings(input_data)

    # Assert
    pd.testing.assert_frame_equal(result, expected)


@pytest.mark.parametrize(
    "input_data, expected",
    [
        (
            pd.DataFrame({"Ставка": ["10"], "Сумма": ["100"]}),
            pd.DataFrame(
                {"Ставка": [10.0], "Сумма": [100.0], "nans": [False], "Ранг": [1]}
            ),
        ),
        (
            pd.DataFrame({"Ставка": [None], "Сумма": [None]}),
            pd.DataFrame(
                {"Ставка": [np.nan], "Сумма": [np.nan], "nans": [True], "Ранг": [""]}
            ),
        ),
    ],
    ids=edge_case_ids,
)
def test_update_rankings_edge_cases(input_data, expected):
    # Act
    result = update_rankings(input_data)

    print(result)

    # Assert
    pd.testing.assert_frame_equal(result, expected)


@pytest.mark.parametrize(
    "input_data",
    [
        (pd.DataFrame({"Ставка": [], "Сумма": []})),
        (pd.DataFrame({"Rate": ["10", "20"], "Amount": ["100", "200"]})),
        (pd.DataFrame({"Ставка": [10, 20], "Сумма": [100, 200]})),
    ],
    ids=error_case_ids,
)
def test_update_rankings_error_cases(input_data):
    # Act & Assert
    with pytest.raises(Exception):
        update_rankings(input_data)
