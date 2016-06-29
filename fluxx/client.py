# Fluxx API Python Client
# Wed  8 Jun 17:04:16 2016

import json
import requests

# TODO:
# i/ add style as instance variable instead of method arg
# ii/ add HTTP Error handling at initialization


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

class Fluxx(object):
    # initialize fluxx api session
    def __init__(self, instance, client_id, client_secret, style='detail'):
        # generate base url based on instance type
        _instance = instance.split('.')
        domain = 'fluxx'
        suffix = 'io'
        if _instance.pop() == 'preprod':
            domain = 'fluxxlabs'
            suffix = 'com'
        _base_url = 'https://{0}.{1}.{2}/'.format(instance, domain, suffix)

        # set auth token
        oauth_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        # send request /receive response
        resp = requests.post(
            _base_url + 'oauth/token',
            data=oauth_data
        )
        content = resp.json()

        # set instance variables
        self.style = style
        # get auth token
        self.auth_token = content.get('access_token')
        self.headers = {
            'Authorization': 'Bearer {}'.format(self.auth_token),
        }
        # set base url
        self.base_url = _base_url + 'api/rest/v1/'


    # style property METHODS

    @property
    def style(self):
        return self._style

    @style.setter
    def style(self, value):
        options = ['detail', 'compact', 'full']
        if not value in options:
            raise ValueError('Style must one of: {}'.format(str(options)))
        self._style = value


    # crud METHODS

    # create new fluxx database record and return its id
    def create(self, model, data):
        url = self.base_url + model
        body = {
            'data': json.dumps(data),
            'style': self.style
        }
        resp = requests.post(url, data=body, headers=self.headers)
        content = resp.json()
        if 'error' in content:
            raise FluxxError(model, 'create', content.get('error'))
        return content.get( model )


    # update an existing record and return it
    def update(self, model, id, data):
        url = self.base_url + model + '/' + str( id )
        body = {
            'data': json.dumps(data),
            'style': self.style
        }
        resp = requests.put(url, data=body, headers=self.headers)
        content = resp.json()
        if 'error' in content:
            raise FluxxError(model, 'update', content.get('error'))
        return content.get(model)


    # returns list of all existing objects and filter if necessary
    # uses instance style value if not present in POST body
    def list(self, model, data=None, params=None):
        url = self.base_url + model
        if not data:
            resp = requests.get(url, params=params, headers=self.headers)
        else:
            if 'style' not in data:
                data.update({'style': self.style})
            resp = requests.post(url + '/list', data=data, headers=self.headers)
        content = resp.json()
        if 'error' in content:
            raise FluxxError(model, 'list', content.get('error'))
        return content['records'].get(model)


    # return a single record based on id
    def fetch(self, model, id):
        url = self.base_url + model + '/' + str( id )
        resp = requests.get(url, params={'style': self.style}, headers=self.headers)
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
