from sentinelsat import SentinelAPI
import json

with open('/home/delgado/proj/manuscript/data/credentials.json') as json_file:
    data = json.load(json_file)

api = SentinelAPI(data['username'], data['password'], 'https://scihub.copernicus.eu/dhus')

def checknget(product_id):
    is_online = api.is_online(product_id)
    if is_online:
        print('Product {} is online. Starting download.'.format(product_id))
        api.download(product_id)
    else:
        print('Product {} is not online.'.format(product_id))


#product_id='12c35311-1184-4147-86fa-5fc5404cc102'
#checknget(product_id)

product_id='f7a6b362-cf40-42d8-900e-a30a8060e89f'
checknget(product_id)

product_id='2da20ba3-35d4-45ac-8c8e-47ee83d4f84d'
checknget(product_id)

product_id='e0e3edf4-4f0e-471f-8aca-f9adceab1795'
checknget(product_id)

