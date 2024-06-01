import datetime

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
                "telegram": ["abc", "def"],
                "created_at": ["some date", "some other date"],
                "rank": ["1", "2"],
            },
            {
                "cuid": "3",
                "name": "Charlie",
                "Фонд_ставка_текст": "30%",
                "Фонд_сумма_текст": "300 млн.",
                "phone": "81231231212",
                "messenger_username": "leshchenko1979",
            },
            {
                "cuid": ["1", "2", "3"],
                "name": ["Alice", "Bob", "Charlie"],
                "rate": ["10%", "20%", "30%"],
                "amount": ["100 млн.", "200 млн.", "300 млн."],
                "phone": ["000000000000", "000000000000", "81231231212"],
                "telegram": ["abc", "def", "https://t.me/leshchenko1979"],
                "created_at": ["some date", "some other date", datetime.datetime.now()],
                "rank": [1, 2, 3],
            },
            id="happy_path",
        ),
        # Happy path: Keep incoming comments
        pytest.param(
            {
                "cuid": ["1", "2"],
                "name": ["Alice", "Bob"],
                "rate": ["10%", "30%"],
                "amount": ["100 млн.", "200 млн."],
                "phone": ["000000000000", "000000000000"],
                "rank": ["1", "2"],
                "Комментарии": ["Это Алиса", "Это Боб"],
            },
            {
                "cuid": "3",
                "name": "Charlie",
                "Фонд_ставка_текст": "20%",
                "Фонд_сумма_текст": "300 млн.",
                "phone": "000000000000",
            },
            {
                "cuid": ["1", "3", "2"],
                "name": ["Alice", "Charlie", "Bob"],
                "rate": ["10%", "20%", "30%"],
                "amount": ["100 млн.", "300 млн.", "200 млн."],
                "phone": ["000000000000", "000000000000", "000000000000"],
                "rank": [1, 2, 3],
                "Комментарии": ["Это Алиса", "", "Это Боб"],
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
    assert [result[i] == dict_to_app_list(expected)[i] for i in range(len(result))]


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
                "telegram": ["abc", "def"],
                "created_at": ["some date", "some other date"],
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
                    "abc",
                    "some date",
                    "1",
                    ("1", "3", "5"),
                ),
                Application(
                    "2",
                    "Bob",
                    "20%",
                    "200 млн.",
                    "000000000000",
                    "def",
                    "some other date",
                    "2",
                    ("2", "4", "6"),
                ),
            ],
        ]
    ],
    ids=["happy_way"],
)
def test_dict_to_app(app_dict: dict[str, list[str]], expected: list[Application]):
    result = dict_to_app_list(app_dict)

    for result_row, expected_row in zip(result, expected):
        if result_row != expected_row:
            print(result_row, expected_row)
            raise AssertionError


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
                    "abc",
                    "some date",
                    "1",
                    ["1", "3", "5"],
                ),
                Application(
                    "2",
                    "Bob",
                    "20%",
                    "200 млн.",
                    "000000000000",
                    "abc",
                    "some date",
                    "2",
                    ["2", "4", "6"],
                ),
            ],
            [
                (
                    "1",
                    "Alice",
                    "10%",
                    "100 млн.",
                    "000000000000",
                    "abc",
                    "some date",
                    "1",
                    "1",
                    "3",
                    "5",
                ),
                (
                    "2",
                    "Bob",
                    "20%",
                    "200 млн.",
                    "000000000000",
                    "abc",
                    "some date",
                    "2",
                    "2",
                    "4",
                    "6",
                ),
            ],
        ]
    ],
    ids=["happy_way"],
)
def test_app_list_to_list_of_lines(data: list[Application], expected: list[list[str]]):
    result = data_to_lines(data)

    assert result == expected


from flask_app import stretch_to_max_len


# Happy path tests with various realistic test values
@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        pytest.param(
            [[1, 2], [3, 4, 5], [6]],
            [[1, 2, ""], [3, 4, 5], [6, "", ""]],
            id="happy_path_uneven_lists",
        ),
        pytest.param(
            [[], [1], [1, 2]],
            [["", ""], [1, ""], [1, 2]],
            id="happy_path_empty_first_list",
        ),
        pytest.param(
            [[1], [1], [1]], [[1], [1], [1]], id="happy_path_equal_length_lists"
        ),
        pytest.param(([1], (2, 3)), [[1, ""], [2, 3]], id="edge_case_lists_and_tuples"),
        pytest.param([[1, 2, 3]], [[1, 2, 3]], id="edge_case_single_inner_list"),
        pytest.param(
            [[None, None], [None]],
            [[None, None], [None, ""]],
            id="edge_case_none_values",
        ),
    ],
)
def test_stretch_to_max_len(input_data, expected_output):
    assert stretch_to_max_len(input_data) == expected_output


# Error cases
@pytest.mark.parametrize(
    "input_data, exception",
    [
        pytest.param([1, 2, 3], TypeError, id="error_case_flat_list"),
    ],
)
def test_stretch_to_max_len_error_cases(input_data, exception):
    # Act / Assert
    with pytest.raises(exception):
        stretch_to_max_len(input_data)


@pytest.mark.parametrize(
    "input_data, expected",
    [
        (
            {
                "CUserId_костыль": "6u3t.dj",
                "bothelp_user_id": 487,
                "conversations_count": 9,
                "created_at": 1717259362,
                "created_at_show": "1/06/2024 16:29:22 UTC",
                "cuid": "6u3t.dj",
                "email": "",
                "first_contact_at": 1692106736,
                "first_name": "Алексей",
                "last_contact_at": 1717259361,
                "last_name": "Лещенко | Деньги девелоперам",
                "messenger_username": "leshchenko1979",
                "name": "Лещенко | Инвестиции Алексей",
                "phone": "3",
                "profile_link": "",
                "ref": "",
                "user_id": "133526395",
                "utm_campaign": "",
                "utm_content": "",
                "utm_medium": "",
                "utm_source": "",
                "utm_term": "",
                "Комментарии": ".",
                "Следующий контакт": "",
                "Фонд_Ранг": "3",
                "Фонд_ставка_текст": "20%",
                "Фонд_сумма": 123,
                "Фонд_сумма_текст": "2 млн.",
            },
            Application(
                **{
                    "cuid": "6u3t.dj",
                    "name": "Лещенко | Инвестиции Алексей",
                    "rate": "20%",
                    "amount": "2 млн.",
                    "phone": "3",
                    "telegram": "https://t.me/leshchenko1979",
                    "created_at": datetime.datetime(2022, 1, 1, 0, 0, 0),
                    "rank": 0,
                    "other_fields": [],
                }
            ),
        )
    ],
)
def test_create_applicaption_from_json(input_data, expected):
    assert (
        Application.from_json(
            input_data, created_at=datetime.datetime(2022, 1, 1, 0, 0, 0)
        )
        == expected
    )
