from sentinelsat import SentinelAPI
import json

with open('./data/credentials.json') as json_file:
    data = json.load(json_file)

api = SentinelAPI(data['username'], data['password'], 'https://scihub.copernicus.eu/dhus')

def checknget(product_id):
    is_online = api.is_online(product_id)
    if is_online:
        print('Product {} is online. Starting download.'.format(product_id))
        api.download(product_id)
    else:
        print('Product {} is not online.'.format(product_id))


product_id='12c35311-1184-4147-86fa-5fc5404cc102'
checknget(product_id)
