# -*- coding: utf-8 -*-

"""
Fluxx API Python Client
Created at Wed  8 Jun 17:04:16 2016
"""

import os
import logging
import json
from functools import wraps

import requests

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

log = logging.getLogger(__name__)
log.addHandler(NullHandler())

ENV_INSTANCE_SUFFIX = 'INSTANCE'
ENV_APPLICATION_ID_SUFFIX = 'CLIENT'
ENV_SECRET_SUFFIX = 'SECRET'


def format_column_name(col):
    "Lowercases all words and removes spaces."
    return '_'.join(col.strip().lower().split())


def format_write_data(data):
    "Formats column headers and extracts column parameter."
    formatted_data = dict((format_column_name(k), v) for k, v in data.items())

    return {
        'cols': json.dumps(list(formatted_data.keys())),
        'data': json.dumps(formatted_data)
    }


def format_output(model, output):
    """Parses Requests response to return model,
    raises Fluxx Error is call was unsuccessful

    :model: <String>
    :output: <Dict>
    :returns: <Dict>

    """

    if 'error' in output:
        raise FluxxError(model, output.get('error'))

    if model.split('_')[0] == 'mac':
        model = 'machine_model'
    else:
        model = model.lower()

    if 'records' in output:
        return output['records'].get(model)

    return output.get(model)


def parse_response(func):
    """Retrieves relevent data from raw API response."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        model = args[1]
        response = func(*args, **kwargs)
        response.raise_for_status()
        return format_output(model, response.json())
    return wrapper


class FluxxError(IOError):

    """Fluxx error class,
    contains a message and code
    """

    def __init__(self, model, error):
        self.model = model
        self.message = error.get('message')
        self.code = error.get('code')

    def __str__(self):
        return 'Error performing request on %s. Code: %s. Messages: %s' % (
            self.model, self.code, self.message
        )


class FluxxClient(object):

    """Fluxx API Client Object,
    exposes Crud functionality for given objects following authentication
    """

    version = 'v2'

    def __init__(self, instance, client_id, client_secret, style='full'):
        if instance.split('.').pop() == 'preprod':
            domain = 'fluxxlabs'
            suffix = 'com'
        else:
            domain = 'fluxx'
            suffix = 'io'

        # generate urls
        base_url = 'https://{0}.{1}.{2}/'.format(instance, domain, suffix)
        token_url = base_url + 'oauth/token' 

        # set auth token retrieval parameters
        oauth_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }

        # initialize request session
        self.session = requests.Session()

        # retrieve OAuth auth token
        resp = self.session.post(token_url, data=oauth_data)
        content = resp.json()

        if 'access_token' not in content:
            raise IOError(content['error_description'])

        # set auth header
        self.auth_token = content['access_token']
        self.session.headers.update({
            'Authorization': 'Bearer {}'.format(self.auth_token),
        })

        # set instance variables
        self.base_url = base_url + 'api/rest/{}/'.format(self.version)
        self.style = style

    @classmethod
    def from_env(cls, instance='FLUXX'):
        """Initialize client from previously set environmental
        variables. The instance, client_id, and client_secret Fluxx API
        keys must be set the following suffixes: _INSTANCE, _CLIENT, _SECRET.

        For example, if the instance is variable is XYZ then XYZ_INSTANCE, 
        XYZ_CLIENT, and XYZ_SECRET must me set. If instance isn't specified
        'FLUXX' will be the assumed prefix.

        :instance: the prefix of the three required env variables
        :returns: <FluxxClient> instance

        """
        instance = instance.upper()
        try:
            ins = os.environ['_'.join((instance, ENV_INSTANCE_SUFFIX))]
            cli = os.environ['_'.join((instance, ENV_APPLICATION_ID_SUFFIX))]
            sec = os.environ['_'.join((instance, ENV_SECRET_SUFFIX ))]
            return cls(ins, cli, sec, 'full')

        except KeyError as e:
            cause, *_ = e.args
            raise ValueError('Instance environment parameter "{}" must be set.'.format(cause))

    @property
    def style(self):
        return self._style

    @style.setter
    def style(self, value):
        options = ('detail', 'compact', 'full')
        if value not in options:
            raise ValueError('Style must one of: {}'.format(str(options)))
        self._style = value

    @parse_response
    def create(self, model, data):
        """Create new fluxx database record and return its id"""

        url = self.base_url + model
        data = format_write_data(data)
        return self.session.post(url, data=data)

    @parse_response
    def update(self, model, rec_id, data):
        """Update an existing record and return it"""

        url = self.base_url + model + '/' + str(rec_id)
        data = format_write_data(data)
        return self.session.put(url, data=data)

    @parse_response
    def list(self, model, cols, page=1, per_page=100, fltr=None):
        """Returns list of relevent object with attributes specified
        by the columns parameter. Default 100 records per page.
        Current only supports GET requests.
        """
        if page < 1:
            raise ValueError('Page number must be greater than 0.')

        params = {
            'cols': json.dumps([format_column_name(col) for col in cols]),
            'page': page,
            'per_page': per_page
        }

        if fltr:
            params.update({'filter': json.dumps(fltr)})

        url = self.base_url + model
        return self.session.get(url, params=params)

    @parse_response
    def get(self, model, record_id, cols):
        """Returns a single record based on id"""

        params = {
            'cols': json.dumps(cols),
            'style': self.style
        }

        url = self.base_url + model + '/' + str(record_id)
        return self.session.get(url, params=params)

    def delete(self, model, record_id):
        """Deletes a single record based on id"""

        url = self.base_url + model + '/' + str(record_id)
        resp = self.session.delete(url)
        resp.raise_for_status()
        return {'id': record_id}
