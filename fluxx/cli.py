import os
import sys
import logging
import threading
import queue
import json
from datetime import datetime
from contextlib import contextmanager

import fire

import fluxx

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

DEFAULT_LOG_PATH = './logs'
DEFAULT_THREAD_COUNT = 5
DEFAULT_PER_PAGE = 100


@contextmanager
def write_operation(instance, model, threads):
    "Initialize queue, read input, start and end threads."
    json_data = sys.stdin.read()
    records = json.loads(json_data)

    if 'records' in records:
        records = records['records']

    yield records

    q = queue.Queue()
    for i, record in enumerate(records):
        record['index'] = i
        q.put(record)

    for _ in range(threads):
        worker = FluxxThread(q, instance, model)
        worker.daemon = True
        worker.start()

    q.join()


class FluxxThread(threading.Thread):

    """Spawns a new thread performing Fluxx API
    create and update requests."""

    def __init__(self, queue, instance=None, model=None):
        self.q = queue
        self.client = fluxx.FluxxClient.from_env(instance)
        self.model = model

        super().__init__()

    def run(self):
        while True:
            item = self.q.get()
            rec_id = item.pop('id', None)
            rec_method = item.get('method').upper()

            try:
                if rec_method == 'CREATE':
                    created = self.client.create(self.model, item)
                    log.info('Created %s', created['id'])

                elif rec_method == 'UPDATE':
                    updated = self.client.update(self.model, rec_id, item)
                    log.info('Updated %s', updated['id'])

                elif rec_method == 'DELETE':
                    deleted = self.client.delete(self.model, rec_id)
                    log.info('Deleted %s', deleted['id'])
                else:
                    log.error('Method not specified')
            except NotImplementedError:
                log.error('Process method not implemented.')

            except fluxx.FluxxError as error:
                log.error(error)

            finally:
                self.q.task_done()


class FluxxCLI(object):

    """Command line interface to this API wrapper, reads and writes JSON."""

    def __init__(self, instance=None, log_path=DEFAULT_LOG_PATH):
        self.instance = instance

        #  add file handler to module level logger
        log_file = '{}/{} | {}.log'.format(log_path, instance, datetime.now())
        handler = logging.FileHandler(log_file)
        log.addHandler(handler)

    def list(self, model, cols, page=1, per_page=DEFAULT_PER_PAGE):
        """Return a list of records according to the Page and PerPage
        settings. Page must be greater than 0.

        :model: The Fluxx ModelObject you wish to query
        :page: Section of the total list to retrieve, must be greater than 0.
        :per_page: Number of records to return per page.
        :returns: None

        """

        client = fluxx.FluxxClient.from_env(self.instance)
        records = client.list(model, cols=list(cols), page=page, per_page=per_page)

        sys.stdout.write(str(json.dumps(records)))

    def create(self, model, threads=DEFAULT_THREAD_COUNT):
        """Creates each record provided in the list.

        :model: The Fluxx Model Object you wish to create.
        :returns: None

        """

        with write_operation(self.instance, model, threads) as records:
            for record in records:
                record['method'] = 'CREATE'

    def update(self, model, threads=DEFAULT_THREAD_COUNT):
        """Updates each record provided in the list.
        Each record must have an id.

        :model: The Fluxx Model Object you wish to update.
        :returns: None

        """

        with write_operation(self.instance, model, threads) as records:
            for i, record in enumerate(records):
                record['method'] = 'UPDATE'

    def delete(self, model, threads=DEFAULT_THREAD_COUNT):
        """Deletes each record provided in the list.
        Each record must have an id.

        :model: The Fluxx Model Object you wish to update.
        :returns: None

        """

        with write_operation(self.instance, model, threads) as records:
            for i, record in enumerate(records):
                record['method'] = 'DELETE'

    def upsert(self, model, threads=DEFAULT_THREAD_COUNT):
        """Creates or updates a each record provided in the list.
        The non-null status of the 'id' attribute of every record determines
        whether it will be created or updated, with None value IDs defaulting
        to creation.

        :model: The Fluxx ModelObject you wish to create.
        :returns: None

        """

        with write_operation(self.instance, model, threads) as records:
            for i, record in enumerate(records):
                if 'id' in record:
                    record['method'] = 'UPDATE'
                else:
                    record['method'] = 'CREATE'


def main():
    fire.Fire(FluxxCLI)
