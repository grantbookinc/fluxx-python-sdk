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
    return '_'.join(col.strip().lower().split())


def format_request_body(dt):
    data = dict((format_column_name(k), v) for k, v in dt.items())
    return {'cols': json.dumps(list(data.keys())), 'data': json.dumps(data)}


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


def write_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        args = list(args)
        data = args.pop()
        body = format_request_body(data)
        method = args[1]

        args.append(body)
        resp = func(*args, **kwargs)
        return parse_response(resp, method)
    return wrapper


def read_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        method = args[1]
        if 'cols' in kwargs:
            cols = kwargs.pop('cols')
            kwargs['cols'] = [format_column_name(col) for col in cols]

        resp = func(*args, **kwargs)
        return parse_response(resp, method)
    return wrapper


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
    def from_env(cls, instance):
        """Initialize client from previously set environmental
        variables. The instance, client_id, and client_secret Fluxx API
        keys must be set the following suffixes: _INSTANCE, _CLIENT, _SECRET.

        For example, if the instance is variable is XYZ then XYZ_INSTANCE, 
        XYZ_CLIENT, and XYZ_SECRET must me set.

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
        options = ['detail', 'compact', 'full']
        if value not in options:
            raise ValueError('Style must one of: {}'.format(str(options)))
        self._style = value

    @write_request
    def create(self, model, body):
        """create new fluxx database record and return its id"""

        url = self.base_url + model
        return self.session.post(url, data=body)

    @write_request
    def update(self, model, id, body):
        """update an existing record and return it"""

        url = self.base_url + model + '/' + str(id)
        return self.session.put(url, data=body)

    @read_request
    def list(self, model, cols=['id'], page=1, per_page=100, fltr=None):
        """Returns list of relevent object with attributes specified
        by the columns parameter. Default 100 records per page.
        Current only supports GET requests.
        """
        if page < 1:
            raise ValueError('Page number must be greater than 0.')

        params = {
            'cols': json.dumps(cols),
            'page': page,
            'per_page': per_page
        }

        if fltr:
            params.update({'filter': json.dumps(filter)})

        url = self.base_url + model
        return self.session.get(url, params=params)

    @read_request
    def get(self, model, id, cols=['id'], style=None):
        """returns a single record based on id"""
        if not style:
            style = self.style

        params = {'cols': json.dumps(cols), 'style': style}
        url = self.base_url + model + '/' + str(id)
        return self.session.get(url, params=params)

    def delete(self, model, record_id):
        """deletes a single record based on id"""

        url = self.base_url + model + '/' + str(record_id)
        self.session.delete(url)
        return {'id': record_id}
