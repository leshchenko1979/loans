import pytest

from flask_app import Application, dict_to_app_list, update_rankings

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
    "non_string_columns",
]


@pytest.mark.parametrize(
    "input_data, expected",
    [
        (
            {"rate": ["10", "20"], "amount": ["100", "200"]},
            {"rate": [10.0, 20.0], "amount": [100.0, 200.0], "rank": [1, 2]},
        ),
        (
            {"rate": ["10", "20"], "amount": ["200", "100"]},
            {"rate": [10.0, 20.0], "amount": [200.0, 100.0], "rank": [1, 2]},
        ),
        (
            {"rate": ["20", "10"], "amount": ["100", "200"]},
            {"rate": [10.0, 20.0], "amount": [200.0, 100.0], "rank": [1, 2]},
        ),
    ],
    ids=happy_path_ids,
)
def test_update_rankings_happy_path(input_data, expected):
    # Act
    result = update_rankings(dict_to_app_list(add_missing_application_keys(input_data)))

    # Assert all rows in result match all rows in expected
    assert all(
        result_row._asdict() == expected_row._asdict()
        for result_row, expected_row in zip(
            result, dict_to_app_list(add_missing_application_keys(expected))
        )
    )


def add_missing_application_keys(input_data):
    for key in Application._fields:
        if key not in input_data:
            input_data[key] = []
    return input_data


@pytest.mark.parametrize(
    "input_data, expected",
    [
        (
            {"rate": ["10"], "amount": ["100"]},
            {"rate": [10.0], "amount": [100.0], "rank": [1]},
        ),
        (
            {"rate": [None], "amount": [None]},
            {"rate": [0], "amount": [0], "rank": [1]},
        ),
    ],
    ids=edge_case_ids,
)
def test_update_rankings_edge_cases(input_data, expected):
    # Act
    result = update_rankings(dict_to_app_list(add_missing_application_keys(input_data)))

    # Assert all rows in result match all rows in expected
    assert all(
        result_row._asdict() == expected_row._asdict()
        for result_row, expected_row in zip(
            result, dict_to_app_list(add_missing_application_keys(expected))
        )
    )


@pytest.mark.parametrize(
    "input_data",
    [{"rate": [10, 20], "amount": [100, 200]}],
    ids=error_case_ids,
)
def test_update_rankings_error_cases(input_data):
    # Act & Assert
    with pytest.raises(Exception):
        update_rankings(dict_to_app_list(add_missing_application_keys(input_data)))
