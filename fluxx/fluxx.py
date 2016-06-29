# Fluxx API Python Client
# Wed  8 Jun 17:04:16 2016

import json
import requests


"""
Fluxx Error Class
-----------------
Contains a message and code
"""

class FluxxError(Exception):
    def __init__(self, model, action, error):
        self.model = model
        self.action = action
        self.message = error.get('message')
        self.code = error.get('code')

    def __str__(self):
        return 'Fluxx %s.%s: Error %s | %s' % (self.model, self.action, self.code, self.message)



"""
Fluxx API Client Object
-----------------------
Exposes Crud functionality for given
objects following authentication
"""

class FluxxService(object):
    # initialize fluxx api session
    def __init__(self, instance, client_id, client_secret):
        # set auth token
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        resp = requests.post('https://{}.fluxx.io/oauth/token'.format(instance), data=data)
        content = resp.json()
        self.auth_token = content.get('access_token')
        self.headers = {
            'Authorization': 'Bearer {}'.format(self.auth_token),
        }
        # set base url
        self.base_url = 'https://{}.fluxx.io/api/rest/v1/'.format(instance)


    # create new fluxx database record and return its id
    def create(self, model, data, style='detail'):
        url = self.base_url + model
        body = {
            'data': json.dumps(data),
            'style': style
        }
        resp = requests.post(url, data=body, headers=self.headers)
        content = resp.json()
        if 'error' in content:
            raise FluxxError(model, 'create', content.get('error'))
        return content.get( model )


    # update an existing record and return it
    def update(self, model, id, data, style='detail'):
        url = self.base_url + model + '/' + str( id )
        body = {
            'data': json.dumps(data),
            'style': style
        }
        resp = requests.put(url, data=body, headers=self.headers)
        content = resp.json()
        if 'error' in content:
            raise FluxxError(model, 'update', content.get('error'))
        return content.get(model)


    # returns list of all existing objects and filter if necessary
    def list(self, model, options=None, params=None):
        url = self.base_url + model
        if not options:
            resp = requests.get(url, params=params, headers=self.headers)
        else:
            resp = requests.post(url + '/list', data=options, headers=self.headers)
        content = resp.json()
        if 'error' in content:
            raise FluxxError(model, 'list', content.get('error'))
        return content['records'].get(model)


    # return a single record based on id
    def fetch(self, model, id, style='full'):
        url = self.base_url + model + '/' + str( id )
        resp = requests.get(url, params={'style':style}, headers=self.headers)
        content = resp.json()
        if 'error' in content:
            raise FluxxError(model, 'fetch', content.get('error'))
        return content.get(model)


    # delete a single record based on id
    def delete(self, model, id):
        url = self.base_url + model + '/' + str( id )
        resp = requests.delete(url, headers=self.headers)
        content = resp.json()
        if type(content) is dict:
            if 'error' in content:
                raise FluxxError(model, 'fetch', content.get('error'))
        return content
