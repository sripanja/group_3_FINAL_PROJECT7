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
    pprint(response.json())


def get_fhir_patient(resource_id):
    url = f'{BASE_URL}/Patient/{resource_id}'
    response = requests.get(url=url, headers=get_headers())
    data = response.json()

    new_patient_dict['name'][0]['family'] = data['name'][0]['family']
    new_patient_dict['name'][0]['given'] = data['name'][0]['given']
    new_patient_dict['identifier'][0]['value'] = random.randint(a=10000, b=99999)
    new_patient_dict['identifier'][0]['period']['start'] = datetime.datetime.today().date().isoformat()
    new_patient_dict['gender'] = data['gender']
    new_patient_dict['birthDate'] = data['birthDate']

    address_line = data['address'][0]['line'][0]
    address_city = data['address'][0]['city']
    address_state = data['address'][0]['state']
    address_postcode = data['address'][0]['postalCode']

    new_patient_dict['address'][0]['line'] = address_line
    new_patient_dict['address'][0]['city'] = address_city
    # new_patient_dict['address'][0]['district']= data['address'][0]['district']
    new_patient_dict['address'][0]['state'] = address_state
    new_patient_dict['address'][0]['postalCode'] = address_postcode
    new_patient_dict['address'][0]['text'] = f"{address_line}, {address_city}, {address_state}, {address_postcode}"

    try:
        headers = {
            'Accept': "application/json"
        }
        url = PRIMARY_CARE_SERVER_URL + '/' + 'Patient'
        response = requests.post(url=url, json=new_patient_dict, headers=headers)
        if response.status_code == 200 or response.status_code == 201:
            response_data = response.json()
            with open(data_dir / 'patient_resource_id.txt', 'w') as f:
                f.write(response_data['id'])
                print('Patient resource ID created.')
        else:
            print(f'Error - {response.status_code}')
    except Exception as e:
        print(e)


def get_direct_parent(concept_id):
    response = requests.get(f'{BASE_HERMES_URL}/{concept_id}/extended')
    data = response.json()
    direct_parents = data['directParentRelationships']
    is_a_relation = direct_parents['116680003']
    first_parent_code = is_a_relation[0]
    concept_description_response = requests.get(f'{BASE_HERMES_URL}/{first_parent_code}/extended')
    concept_description_data = concept_description_response.json()
    preferred_parent_description = concept_description_data['preferredDescription']['term']
    return first_parent_code, preferred_parent_description



def search_condition(patient_resource_id):
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    data = response.json()
    if 'entry' in data:
        conditions = data['entry']
        thirty_condition = conditions[30]
        snomed_code = thirty_condition['resource']['code']['coding'][0]['code']
        parent = get_direct_parent(concept_id=snomed_code)
        parent_code = parent[0]
        parent_description = parent[1]
        new_condition_dict['code']['coding'][0]['code'] = parent_code
        new_condition_dict['code']['coding'][0]['display'] = parent_description
        new_condition_dict['code']['text'] = parent_description
        with open(data_dir / 'patient_resource_id.txt', 'r') as f:
            patient_resource_id = f.readline()
        new_condition_dict['subject']['reference'] = f"Patient/{patient_resource_id}"

        try:
            headers = {
                'Accept': "application/json"
            }
            url = PRIMARY_CARE_SERVER_URL + '/' + 'Condition'
            response = requests.post(url=url, json=new_condition_dict, headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                print(response_data)
                print('Condition resource created.')
            else:
                print(f'Error - {response.status_code}')
        except Exception as e:
            print(e)
    else:
        print('No results found')


if __name__ == '__main__':
    get_fhir_patient(resource_id='985ac75c-54cd-47ab-afe1-93d52db5ba48')
    search_condition(patient_resource_id='985ac75c-54cd-47ab-afe1-93d52db5ba48')