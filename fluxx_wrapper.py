# -*- coding: utf-8 -*-

"""
Fluxx API Python Client
    Wed  8 Jun 17:04:16 2016
"""

import logging
import json
import requests

# TODO:
# i/ add style as instance variable instead of method arg
# ii/ add HTTP Error handling at initialization


try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logger = logging.getLogger(__name__).addHandler(NullHandler())


def _pluck_result(model):
    m = model.split('_')
    if m[0] == 'mac':
        return 'machine_model'
    else:
        return model.lower()


class FluxxError(Exception):

    """Fluxx error class,
    contains a message and code
    """

    def __init__(self, model, action, error):
        self.model = model
        self.action = action
        self.message = error.get('message')
        self.code = error.get('code')

    def __str__(self):
        return 'Fluxx %s.%s: Error %s | %s' % (
            self.model, self.action, self.code, self.message
        )


class FluxxMethod(object):

    """Allows first attribute of client
    to be substituted as the model type of an api call."""

    def __init__(self, client, method_name):
        self.client = client
        self.method_name = method_name

    def __getattr__(self, key):
        return FluxxMethod(self.client, '.'.join(( self.method_name, key )))

    def __call__(self, *args, **kwargs):
        try:
            model_type, method_type = self.method_name.split('.')
            method = getattr(self.client, method_type)
            return method(model_type, *args, **kwargs)

        except ValueError:
            raise AttributeError('Invalid model, method combination.')


class FluxxClient(object):

    """Fluxx API Client Object,
    exposes Crud functionality for given
    objects following authentication
    """

    def __init__(self, instance, client_id, client_secret, version='v2', style='full'):
        # generate base url based on instance type
        _instance = instance.split('.')
        domain = 'fluxx'
        suffix = 'io'
        if _instance.pop() == 'preprod':
            self.production = False
            domain = 'fluxxlabs'
            suffix = 'com'
        _base_url = 'https://{0}.{1}.{2}/'.format(instance, domain, suffix)

        # create request session
        self.session = requests.Session()

        # set auth token
        oauth_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }

        # retrieve OAuth auth token
        resp = self.session.post(
            _base_url + 'oauth/token',
            data=oauth_data
        )
        content = resp.json()

        # set auth header
        self.auth_token = content.get('access_token')
        self.session.headers.update({
            'Authorization': 'Bearer {}'.format(self.auth_token),
        })

        # set instance variables
        self.base_url = _base_url + 'api/rest/{}/'.format(version)
        self.style = style


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

    def create(self, model, data):
        """create new fluxx database record and return its id"""

        url = self.base_url + model
        content = self.session.post(url, data=data).json()

        if 'error' in content:
            raise FluxxError(model, 'create', content.get('error'))
        return content.get(_pluck_result(model))

    def update(self, model, id, data):
        """update an existing record and return it"""

        url = self.base_url + model + '/' + str( id )
        content = self.session.put(url, data=data).json()

        if 'error' in content:
            raise FluxxError(model, 'update', content.get('error'))
        return content.get(_pluck_result(model))

    def list(self, model, data=None, params=None):
        """returns list of all existing objects and filter if necessary
        uses instance style value if not present in POST body"""

        url = self.base_url + model
        if not data:
            resp = self.session.get(url, params=params)
        else:
            if 'style' not in data:
                data.update({'style': self.style})
            resp = self.session.post(url + '/list', data=data)

        content = resp.json()
        if 'error' in content:
            raise FluxxError(model, 'list', content.get('error'))
        return content['records'].get(_pluck_result(model))

    def get(self, model, id, params={}):
        """returns a single record based on id"""

        url = self.base_url + model + '/' + str( id )
        if not 'style' in params:
            params.update({'style': self.style})

        content = self.session.get(url, params=params).json()

        if 'error' in content:
            raise FluxxError(model, 'fetch', content.get('error'))
        return content.get(_pluck_result(model))

    def delete(self, model, id):
        """deletes a single record based on id"""

        url = self.base_url + model + '/' + str( id )
        content = self.session.delete(url).json()

        if type(content) is dict:
            if 'error' in content:
                raise FluxxError(model, 'fetch', content.get('error'))
        return content

    def __getattr__(self, name):
        """Inserts Fluxx Models as first argument
        in request call.

        :attribute: Model Name
        :returns: Return value of function call

        """
        return FluxxMethod(self, name)
