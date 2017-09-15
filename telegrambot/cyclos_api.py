import requests
from requests.auth import HTTPBasicAuth
import config
from datetime import datetime


# function that return the url where the api is
def _url(path):
    return ('https://communities.cyclos.org/' + config.COMMUNITY
            + '/api/' + path)


# Return the data needed by request auth param
def authentication(name, password):
    return HTTPBasicAuth(name, password)


# Return the auth data for login (now only used for testing pourposes)
def auth_data_for_login():
    return requests.get(_url('auth/data-for-login'))


# Return the account balance, it need the username and the password
def get_account_balance(name, password):
    response = requests.get(_url(name+"/accounts"),
                            auth=authentication(name, password))
    data = response.json()
    return data[0]['status']
    # return data


# Return the basic account info
def auth(name, password):
    response = requests.get(_url('auth'),
                            auth=authentication(name, password))
    if (response.status_code == 200):
        return True
    else:
        return False


# Search advertisements
def search(name, password, keyword):
    pass


# Create new advertisement
def create_advert(name, password, title, body, parent, child, price):
    begin = datetime.today()
    begin_formated = str(begin.year)+"-"+str(begin.month)+"-"+str(begin.day - 2)+"T"+str(begin.hour)+":"+str(begin.minute)+":"+str(begin.second)+".304Z"
    end = datetime(begin.year + 1, begin.month, begin.day - 2)
    end_formated = str(end.year)+"-"+str(end.month)+"-"+str(end.day)+"T"+str(end.hour)+":"+str(end.minute)+":"+str(end.second)+".304Z"
    data = get_marketplace_info(name, password)
    for parent_data in data['categories']:
        if parent_data['name'] is parent:
            parent = parent_data['id']
    currency_id = get_marketplace_currency_id(name, password)
    categories = get_marketplace_info(name, password)
    for parent_category in categories['categories']:
        if parent_category['name'] == parent:
            parent_id = parent_category['id']
            for children_category in parent_category['children']:
                if children_category['name'] == child:
                    child_id = children_category['id']
    payload = {
              "name": title,
              "description": body,
              "publicationPeriod": {
                "begin": begin_formated,
                "end": end_formated
              },
              "categories": [
                child_id
              ],
              "currency": currency_id,
              "price": price,
              "promotionalPrice": price,
              "promotionalPeriod": {
                "begin": begin_formated,
                "end": begin_formated
              },
              "customValues": {},
              "addresses": [
              "adress"
              ],
              "kind": "simple",
              "submitForAuthorization": 'false',
              "hidden": 'false',
              "images": [
              "string"
              ]
              }
    response = requests.post(_url(name+'/marketplace'),
                             json=payload,
                             auth=authentication(name, password))
    if (response.status_code == 201):
        return True
    else:
        return False


# Get info needed to create new advertisements
def get_marketplace_info(name, password):
    payload = {'fields': 'categories', 'kind': 'simple'}
    # payload = {'kind': 'simple'}
    response = requests.get(_url(name+'/marketplace/data-for-new'),
                            params=payload,
                            auth=authentication(name, password))
    return response.json()


# Get the currency id
def get_marketplace_currency_id(name, password):
    payload = {'fields': 'currencies', 'kind': 'simple'}
    response = requests.get(_url('/marketplace/data-for-search'),
                            params=payload,
                            auth=authentication(name, password))
    currency = response.json()
    currency_id = currency['currencies'][0]['id']
    return currency_id
