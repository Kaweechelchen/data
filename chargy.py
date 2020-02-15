#!/usr/bin/env python3

import yaml
import requests
import xmltodict
import re
import json
import argparse
from pprint import pprint

with open('config.yml', 'r') as config_data:
    api = yaml.load(config_data, yaml.BaseLoader)['api']['charging_stations']

parser = argparse.ArgumentParser(description='Chargy station statuses.')
parser.add_argument('-t', '--total', action='store_true', help='only return totals')

args = parser.parse_args()

def get_chargy_stations():
    raw = xmltodict.parse(
        requests.get(api['chargy']).text,
        dict_constructor=dict
    )
    return raw['kml']['Document']['Placemark']


def get_chargy_connectors():
    connectors = []
    total = {
        'available': 0,
        'offline': 0,
        'charging': 0
    }

    for station in get_chargy_stations():
        location = {
            'address': station['address'],
            'coordinates': list(map(float, station['Point']['coordinates'].split(',')))
        }

        for chg_device in station['ExtendedData']['Data']:
            if chg_device['@name'] != 'chargingdevice':
                continue

            for raw_connector in json.loads(chg_device['value'])['connectors']:
                status = raw_connector['description'].lower()
                connector = {
                    'id': int(raw_connector['id']),
                    'name': raw_connector['name'],
                    'status': status,
                    'chg_speed': raw_connector['maxchspeed'],
                    'location': location
                }
                total[status] += 1

                connectors.append(connector)

    if args.total:
        return total
    return {
        'total': total,
        'connectors': connectors
    }



def get_charging_stations():
    return (
        get_chargy_connectors()
    )

if __name__ == '__main__':
    print(
        json.dumps(get_charging_stations())
    )
