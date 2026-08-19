import requests


def test_function():
    try:
        response = requests.get("http://127.0.0.1:8765", timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"Unable to reach AnkiConnect: {error}")
        return False

    print(response.status_code)
    return True