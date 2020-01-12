#!/usr/bin/env python3

import yaml
import requests
import xmltodict
import re

with open('config.yml', 'r') as config_data:
    cfg = yaml.load(config_data, yaml.BaseLoader)

def get_ettelbruck():
    raw = requests.get(cfg['api']['ettelbruck']).json()

    parkings = []
    for parking_raw in raw['Parkings']:
        parking = {}
        parking['city'] = 'Ettelbruck'
        parking['name'] = re.search('Parking\s(.*)',parking_raw['Name']).group(1)
        if parking_raw['Info1'] is None:
            parking['total'] = None
        else:
            parking['total'] = int(re.search('(\d+).*', parking_raw['Info1']).group(1))

        free = {}
        free_count = 0
        for availability in parking_raw['Availabilities']:
            if availability['Type'] == 0:
                free['general'] = int(availability['Count'])
            elif availability['Type'] == 1:
                free['disabled'] = int(availability['Count'])
            elif availability['Type'] == 2:
                free['ev'] = int(availability['Count'])
            else:
                raise Exception('unknown free parking type [{}]'.format(availability['Type']))
            free_count += int(availability['Count'])
        free['total'] = int(free_count)
        parking['free'] = free
        parkings.append(parking)

    return parkings


def get_luxembourg():
    raw = xmltodict.parse(
        requests.get(cfg['api']['luxembourg']).text,
        dict_constructor=dict
    )

    parkings = []
    for parking_raw in raw['rss']['channel']['item']:
        parking = {}
        parking['city'] = 'Luxembourg'
        parking['name'] = parking_raw['title']
        parking['total'] = parking_raw['vdlxml:total']
        free = {}
        if parking_raw['vdlxml:actuel'] is None:
            free['total'] = None
        else:
            free['total'] = int(parking_raw['vdlxml:actuel'])
        free['general'] = None
        free['disabled'] = None
        free['ev'] = None
        parking['free'] = free
        
        parkings.append(parking)

    return parkings

print(
    get_ettelbruck() +
    get_luxembourg()
)

