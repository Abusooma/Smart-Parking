import requests

endpoint = "http://127.0.0.1:8000/parking/endpoint_url/"

try:
    responses = requests.get(
        endpoint, params={'matricule': '8858888', 'parking_id': 7, 'type': 'sortie'})
except requests.exceptions.RequestException as e:
    print(f"Une erreur HTTP est survenue: {e}")

print(responses.status_code)
