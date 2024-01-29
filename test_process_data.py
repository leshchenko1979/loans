import pytest

from flask_app import Application, data_to_lines, dict_to_app_list, process_data


@pytest.mark.parametrize(
    "existing_data, new_data, expected",
    [
        # Happy path test cases
        pytest.param(
            {
                "cuid": ["1", "2"],
                "name": ["Alice", "Bob"],
                "rate": ["10%", "20%"],
                "amount": ["100 млн.", "200 млн."],
                "phone": ["000000000000", "000000000000"],
                "rank": ["1", "2"],
            },
            {
                "cuid": "3",
                "name": "Charlie",
                "Фонд_ставка_текст": "30%",
                "Фонд_сумма_текст": "300 млн.",
                "phone": "81231231212",
            },
            {
                "cuid": ["1", "2", "3"],
                "name": ["Alice", "Bob", "Charlie"],
                "rate": ["10%", "20%", "30%"],
                "amount": ["100 млн.", "200 млн.", "300 млн."],
                "phone": ["000000000000", "000000000000", "81231231212"],
                "rank": [1, 2, 3],
            },
            id="happy_path",
        ),
        # Happy path: Keep incoming comments
        pytest.param(
            {
                "cuid": ["1", "2"],
                "name": ["Alice", "Bob"],
                "rate": ["10%", "20%"],
                "amount": ["100 млн.", "200 млн."],
                "phone": ["000000000000", "000000000000"],
                "rank": ["1", "2"],
                "Комментарии": ["Это Алиса", "Это Боб"],
            },
            {
                "cuid": "3",
                "name": "Charlie",
                "Фонд_ставка_текст": "30%",
                "Фонд_сумма_текст": "300 млн.",
                "phone": "000000000000",
            },
            {
                "cuid": ["1", "2", "3"],
                "name": ["Alice", "Bob", "Charlie"],
                "rate": ["10%", "20%", "30%"],
                "amount": ["100 млн.", "200 млн.", "300 млн."],
                "phone": ["000000000000", "000000000000", "000000000000"],
                "rank": [1, 2, 3],
                "Комментарии": ["Это Алиса", "Это Боб", ""],
            },
            id="happy_path_keep_comments",
        ),
        # Edge case: Adding a duplicate user should remove the old entry
        pytest.param(
            {
                "cuid": ["1", "2"],
                "name": ["Alice", "Bob"],
                "rate": ["10%", "20%"],
                "amount": ["100 млн.", "200 млн."],
                "phone": ["000000000000", "000000000000"],
                "rank": ["1", "2"],
            },
            {
                "cuid": "2",
                "name": "Bob",
                "Фонд_ставка_текст": "25%",
                "Фонд_сумма_текст": "250 млн.",
                "phone": "000000000000",
            },
            {
                "cuid": ["1", "2"],
                "name": ["Alice", "Bob"],
                "rate": ["10%", "25%"],
                "amount": ["100 млн.", "250 млн."],
                "phone": ["000000000000", "000000000000"],
                "rank": [1, 2],
            },
            id="edge_case_duplicate_user",
        ),
        # Error case: Missing MAPPING keys in new_data
        pytest.param(
            {
                "CUserID": [1],
                "Имя": ["Alice"],
                "Ставка": [10],
                "Сумма": [100],
                "Ранг": [1],
            },
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
    if isinstance(expected, dict):
        result = process_data(dict_to_app_list(existing_data), new_data)
    else:
        with pytest.raises(expected):
            process_data(dict_to_app_list(existing_data), new_data)
        return

    print(result)

    # Assert
    assert [
        result[i]._asdict() == dict_to_app_list(expected)[i]._asdict()
        for i in range(len(result))
    ]


@pytest.mark.parametrize(
    "app_dict, expected",
    [
        [
            {
                "cuid": ["1", "2"],
                "name": ["Alice", "Bob"],
                "rate": ["10%", "20%"],
                "amount": ["100 млн.", "200 млн."],
                "phone": ["000000000000", "000000000000"],
                "rank": ["1", "2"],
                "other_field3": ["1", "2"],
                "other_field2": ["3", "4"],
                "other_field1": ["5", "6"],
            },
            [
                Application(
                    "1",
                    "Alice",
                    "10%",
                    "100 млн.",
                    "000000000000",
                    "1",
                    ["1", "3", "5"],
                ),
                Application(
                    "2", "Bob", "20%", "200 млн.", "000000000000", "2", ["2", "4", "6"]
                ),
            ],
        ]
    ],
    ids=["happy_way"],
)
def test_dict_to_app(app_dict: dict[str, list[str]], expected: list[Application]):
    result = dict_to_app_list(app_dict)

    assert [result[i]._asdict() == expected[i]._asdict() for i in range(len(result))]


@pytest.mark.parametrize(
    "data, expected",
    [
        [
            [
                Application(
                    "1",
                    "Alice",
                    "10%",
                    "100 млн.",
                    "000000000000",
                    "1",
                    ["1", "3", "5"],
                ),
                Application(
                    "2", "Bob", "20%", "200 млн.", "000000000000", "2", ["2", "4", "6"]
                ),
            ],
            [
                ("1", "Alice", "10%", "100 млн.", "000000000000", "1", "1", "3", "5"),
                ("2", "Bob", "20%", "200 млн.", "000000000000", "2", "2", "4", "6"),
            ],
        ]
    ],
    ids=["happy_way"],
)
def test_app_list_to_list_of_lines(data: list[Application], expected: list[list[str]]):
    result = data_to_lines(data)

    assert result == expected
