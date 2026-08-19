import requests


def test_function():
    try:
        response = requests.get("https://api.ankiweb.net", timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"Unable to reach AnkiWeb: {error}")
        return False

    print(response.status_code)
    return True