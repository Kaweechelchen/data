#!/usr/bin/env python3

import yaml
import requests
import xmltodict
import re
import argparse
import json
from bs4 import BeautifulSoup
from pprint import pprint

with open('config.yml', 'r') as config_data:
  api = yaml.load(config_data, yaml.BaseLoader)['api']['parking']

parser = argparse.ArgumentParser(description='Chargy station statuses.')
parser.add_argument('--no-details', action='store_true', help='only return totals of different parkings')

args = parser.parse_args()

def get_ettelbruck():
  raw = requests.get(api['ettelbruck']).json()

  parkings = []
  try:
    for parking_raw in raw['Parkings']:
      parking = {}
      parking['city'] = 'Ettelbruck'
      parking['name'] = re.search('(Parking\s)?(.*)',parking_raw['Name']).group(2)
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
        elif availability['Type'] >= 2:
          free_detail['ev'] = int(availability['Count'])
        else:
          raise Exception('unknown free parking type [{}]'.format(availability['Type']))
        free_count += int(availability['Count'])
      parking['free'] = int(free_count)
      if not args.no_details:
        parking['free-detail'] = free_detail
      parkings.append(parking)
  except Exception as e:
    print(e)
    raise e
    return []

  return parkings


def get_luxembourg():
  raw = xmltodict.parse(
    requests.get(api['luxembourg']).text,
    dict_constructor=dict
  )

  parkings = []
  try:
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
      if not args.no_details:
        parking['free-detail'] = free_detail

      parkings.append(parking)
  except:
    return []

  return parkings

def get_esch():
  name_html = BeautifulSoup(requests.get(api['esch']['name']).text, 'html.parser')
  data = requests.get(api['esch']['data']).json()

  parking_names = {}

  for parking in name_html.findAll("div", {"class": "parking"}):
    parking_names[parking.get_attribute_list('data-id')[0]] = parking.p.string

  parkings = []
  try:
    for idx in data:
      parking_raw = data[idx]
      parking = {}
      parking['city'] = 'Esch'
      parking['name'] = parking_names[idx]
      parking['total'] = int(parking_raw['capacity'])
      free_detail = {}
      parking['free'] = int(parking_raw['free'])
      free_detail['general'] = int(parking_raw['free'])
      free_detail['disabled'] = None
      free_detail['ev'] = None
      if not args.no_details:
        parking['free-detail'] = free_detail

      parkings.append(parking)
  except Exception as e:
    print(e)
    return []

  return parkings

def get_parking():
  return (
    get_ettelbruck() +
    get_luxembourg() +
    get_esch()
  )

if __name__ == '__main__':
  print(
    json.dumps(get_parking())
  )
