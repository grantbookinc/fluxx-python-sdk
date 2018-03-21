# -*- coding: utf-8 -*-

"""
Fluxx API Python Client
Created at Wed  8 Jun 17:04:16 2016
"""

import os
import logging
import json

import requests

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

log = logging.getLogger(__name__)
log.addHandler(NullHandler())


def get_fluxx_client(instance):
    """Initializes and returns a <FluxxClient> using environmental
    variables derived from the provided instance string. _INSTANCE, _CLIENT,
    and _SECRET must appended to the instance name and present in the environment.

    :instance: String
    :returns: <FluxxClient>

    """
    instance = instance.upper()
    try:
        ins = os.environ['{}_INSTANCE'.format(instance)]
        cli = os.environ['{}_CLIENT'.format(instance)]
        sec = os.environ['{}_SECRET'.format(instance)]
        return FluxxClient(ins, cli, sec, 'v2', 'full')
    except KeyError as e:
        cause, *_ = e.args
        raise ValueError('Instance environment parameter "{}" must be set.'.format(cause))


def format_write_request(dt):
    return {
        'cols': json.dumps(list(dt.values())),
        'data': json.dumps(dt)
    }


def parse_response(resp, model):
    """Parses Requests response to return model,
    raises Fluxx Error is call was unsuccessful

    :resp: <Requests.Response>
    :returns: <Dict>

    """
    content = resp.json()

    if 'error' in content:
        raise FluxxError(model, resp.request.method, content.get('error'))

    if model.split('_')[0] == 'mac':
        model = 'machine_model'
    else:
        model = model.lower()

    if 'records' in content:
        return content['records'].get(model)

    return content.get(model)


class FluxxError(IOError):

    """Fluxx error class,
    contains a message and code
    """

    def __init__(self, model, action, error):
        self.model = model
        self.action = action
        self.message = error.get('message')
        self.code = error.get('code')

    def __str__(self):
        return 'Error performing %s request on %s. Code: %s. Messages: %s' % (
            self.action, self.model, self.code, self.message
        )


class FluxxMethod(object):

    """Allows first attribute of client
    to be substituted as the model type of an api call."""

    def __init__(self, client, method_name):
        self.client = client
        self.method_name = method_name

    def __getattr__(self, key):
        return FluxxMethod(self.client, '.'.join((self.method_name, key)))

    def __call__(self, *args, **kwargs):
        try:
            model_type, method_type = self.method_name.split('.')
            method = getattr(self.client, method_type)
            return method(model_type, *args, **kwargs)

        except ValueError as e:
            print(e)
            raise AttributeError('Invalid model, method combination.')


class FluxxClient(object):

    """Fluxx API Client Object,
    exposes Crud functionality for given
    objects following authentication
    """

    instance = None
    client_id = None
    client_id = None

    def __init__(self, instance, client_id,
                 client_secret, version='v2', style='full'):
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

        if 'access_token' not in content:
            raise IOError(content['error_description'])

        # set auth header
        self.auth_token = content['access_token']
        self.session.headers.update({
            'Authorization': 'Bearer {}'.format(self.auth_token),
        })

        # set instance variables
        self.base_url = _base_url + 'api/rest/{}/'.format(version)
        self.style = style

    @property
    def style(self):
        return self._style

    @style.setter
    def style(self, value):
        options = ['detail', 'compact', 'full']
        if value not in options:
            raise ValueError('Style must one of: {}'.format(str(options)))
        self._style = value

    def create(self, model, data):
        """create new fluxx database record and return its id"""

        url = self.base_url + model
        body = format_write_request(data)
        resp = self.session.post(url, data=body)
        return parse_response(resp, model)

    def update(self, model, id, data):
        """update an existing record and return it"""

        url = self.base_url + model + '/' + str(id)
        body = format_write_request(data)
        resp = self.session.put(url, data=body)
        return parse_response(resp, model)

    def list(self, model, cols=['id'], **kwargs):
        """Returns list of relevent object with attributes specified
        by the columns parameter. Default 100 records per page.
        Current only supports GET requests.
        """
        if 'page' in kwargs and kwargs['page'] == 0:
            raise ValueError('Page number must be greater than 1.')

        url = self.base_url + model
        params = {
            'cols': json.dumps(cols),
            'page': kwargs.get('page', 1),
            'per_page': kwargs.get('per_page', 100),
            # 'filter': json.dumps(kwargs.get('filter'))
        }
        if 'filter' in kwargs:
            params.update({'filter': json.dumps(kwargs['filter'])})

        resp = self.session.get(url, params=params)
        return parse_response(resp, model)

    def get(self, model, id, cols=['id'], **kwargs):
        """returns a single record based on id"""

        url = self.base_url + model + '/' + str(id)
        params = {
            'cols': json.dumps(cols),
            'style': kwargs.get('style', self.style)
        }
        resp = self.session.get(url, params=params)
        return parse_response(resp, model)

    def delete(self, model, id):
        """deletes a single record based on id"""

        url = self.base_url + model + '/' + str(id)
        resp = self.session.delete(url)
        return resp

    def __getattr__(self, name):
        """Inserts Fluxx Models as first argument
        in request call.

        :attribute: Model Name
        :returns: Return value of function call

        """
        return FluxxMethod(self, name)
