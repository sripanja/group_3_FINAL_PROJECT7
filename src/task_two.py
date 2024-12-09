import json
import random
import datetime
from time import thread_time

import requests
from pprint import pprint
from pathlib import Path
from src.registration import data_dir
from src.data_templates import new_patient_dict, new_condition_dict

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_CARE_SERVER_URL = "http://137.184.71.65:8080/fhir"
BASE_HERMES_URL = 'http://159.65.173.51:8080/v1/snomed/concepts'


def get_access_token_from_file():
    file_path = Path(data_dir / "access_token.json")
    if not file_path.exists():
        print("Error: access_token.json file not found.")
        return None
    try:
        with open(file_path, 'r') as json_file:
            json_data = json.load(json_file)
            access_token = json_data.get("access_token")
        return access_token
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error reading access token from file: {e}")
        return None


def get_headers():
    access_token = get_access_token_from_file()
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    return headers


def get_fhir_resource(resource_name):
    url = f'{BASE_URL}/{resource_name}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)


def get_fhir_patient(patient_resource_id):
    url = f'{BASE_URL}/Patient/{patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    data = response.json()


def child_term(concept_id):
    return f"<! {concept_id}"

def get_snomed_code(patient_resource_id):
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    data = response.json()
    if 'entry' in data:
        conditions = data['entry']
        thirty_condition = conditions[30]
        snomed_code = thirty_condition['resource']['code']['coding'][0]['code']
        return (snomed_code)


def search_condition(patient_resource_id):
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    data = response.json()
    pprint (data)
    snomed = get_snomed_code(patient_resource_id)
    if 'entry' in data:
        conditions = data['entry']
        thirty_condition = conditions[30]
        snomed_code = thirty_condition['resource']['code']['coding'][0]['code']
    print(snomed)
    children = child_term(concept_id=snomed_code)
    child_code = children[0]
    print('here')
    print(child_code)


def expression_constraint(search_string):
    response = requests.get(f'{BASE_HERMES_URL}/search?constraint={search_string}')
    data = response.json()

    for concept in data:
        concept_id = concept['conceptId']
        preferred_term = concept['preferredTerm']
        term = concept['term']
        print(f"Concept ID: {concept_id} | Preferred term: {preferred_term} | term: {term}")


if __name__ == '_main_':
    patient_resource_id = '985ac75c-54cd-47ab-afe1-93d52db5ba48'
    get_snomed_code(patient_resource_id)
    get_fhir_patient(patient_resource_id)
    # concept_id=snomed_code
    string_value = child_term(concept_id).strip()
    # print()
    expression_constraint(search_string=string_value)