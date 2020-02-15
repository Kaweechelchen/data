#!/usr/bin/env python3

import yaml
import requests
import xmltodict
import re
import json

with open('config.yml', 'r') as config_data:
    api = yaml.load(config_data, yaml.BaseLoader)['api']['parking']

def get_ettelbruck():
    raw = requests.get(api['ettelbruck']).json()

    parkings = []
    for parking_raw in raw['Parkings']:
        parking = {}
        parking['city'] = 'Ettelbruck'
        parking['name'] = re.search('Parking\s(.*)',parking_raw['Name']).group(1)
        if parking_raw['Info1'] is None:
            parking['total'] = None
        else:
            parking['total'] = int(re.search('(\d+).*', parking_raw['Info1']).group(1))

        free_detail = {}
        free_count = 0
        for availability in parking_raw['Availabilities']:
            if availability['Type'] == 0:
                free_detail['general'] = int(availability['Count'])
            elif availability['Type'] == 1:
                free_detail['disabled'] = int(availability['Count'])
            elif availability['Type'] == 2:
                free_detail['ev'] = int(availability['Count'])
            else:
                raise Exception('unknown free parking type [{}]'.format(availability['Type']))
            free_count += int(availability['Count'])
        parking['free'] = int(free_count)
        parking['free-detail'] = free_detail
        parkings.append(parking)

    return parkings


def get_luxembourg():
    raw = xmltodict.parse(
        requests.get(api['luxembourg']).text,
        dict_constructor=dict
    )

    parkings = []
    for parking_raw in raw['rss']['channel']['item']:
        parking = {}
        parking['city'] = 'Luxembourg'
        parking['name'] = parking_raw['title']
        if parking_raw['vdlxml:total'] is None:
            parking['total'] = None
        else:
            parking['total'] = int(parking_raw['vdlxml:total'])
        free_detail = {}
        if parking_raw['vdlxml:actuel'] is None:
            parking['free'] = None
            free_detail['general'] = None
        else:
            parking['free'] = int(parking_raw['vdlxml:actuel'])
            free_detail['general'] = int(parking_raw['vdlxml:actuel'])
        free_detail['disabled'] = None
        free_detail['ev'] = None
        parking['free-detail'] = free_detail
        
        parkings.append(parking)

    return parkings

def get_parking():
    return (
        get_ettelbruck() +
        get_luxembourg()
    )

if __name__ == '__main__':
    print(
        json.dumps(get_parking())
    )