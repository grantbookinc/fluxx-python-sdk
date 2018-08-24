import os
import time
import sys
import logging
import threading
import collections
import queue
import json
import csv
from datetime import datetime
from contextlib import contextmanager

import fire
import requests

import fluxx

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

DEFAULT_LOG_DIR = './logs'

SLEEP_TIME = 60
PER_PAGE_MAX = 100

INSTANCE = 'FLUXX'
MODEL = 'user'
THREAD_COUNT = 5


def start_workers(size, delete=False, migrate=False):
    """Starts FluxxWorkers.
    :returns: Pair of queues.

    """
    streams = (queue.Queue(), queue.Queue(maxsize=size))

    for _ in range(THREAD_COUNT):
        worker = FluxxWorker(streams, delete, migrate)
        worker.daemon = True
        worker.start()

    return streams


class FluxxWorker(threading.Thread):

    """Spawns a new thread performing Fluxx API
    create and update requests."""

    def __init__(self, qs, delete=False, migrate=False):
        self.in_q, self.out_q = qs
        self.client = fluxx.FluxxClient.from_env(INSTANCE)
        self.delete = delete
        self.migrate = migrate

        super().__init__()

    def run(self):
        while True:
            index, record = self.in_q.get()
            output = {
                'index': index,
                'id': None,
                'error': None
            }

            try:
                if self.migrate:
                    fltr = ["migrate_id", "eq", record['migrate_id']]
                    matches = self.client.list(MODEL, record['id'], fltr=fltr)
                    if (not isinstance(matches, collections.Iterable)) or (len(matches) != 1):
                        raise ValueError('Migrate ID invalid.')
                    record.update(matches[0])

                if ('id' in record) and record.get('id'):
                    if self.delete:
                        self.client.delete(MODEL, record['id'])
                        log.info('Deleted %s %d', MODEL, record['id'])
                        output.update({'id': record['id']})

                    else:
                        updated = self.client.update(MODEL, record['id'], record)
                        log.info('Updated %s %d', MODEL, updated['id'])
                        output.update({'id': updated['id']})
                else:
                    created = self.client.create(MODEL, record)
                    log.info('Created %s %d', MODEL, created['id'])
                    output.update({'id': created['id']})

                self.out_q.put(output)

            except requests.HTTPError as err:
                log.info('Retrying %s %d, %s', MODEL, index, err)

                time.sleep(SLEEP_TIME)
                self.in_q.put((index, record))

            except Exception as err:
                log.error(err)
                output.update({'error': str(err)})
                self.out_q.put(output)


class FluxxCLI(object):

    """Command line interface to this API wrapper, reads and writes JSON."""

    def __init__(self, instance=INSTANCE, log_dir=DEFAULT_LOG_DIR):
        global INSTANCE
        INSTANCE = instance

        #  setup logging
        log_dir = log_dir + '/' + instance
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file = '{}.log'.format(datetime.now().strftime('%x %X').replace('/', '-'))
        log_path = os.path.join(log_dir, log_file)

        #  add file handler to module level logger
        handler = logging.FileHandler(log_path, delay=True)
        log.addHandler(handler)

    def list(self, model, cols, filter=None, page=1, per_page=PER_PAGE_MAX):
        """Return a list of records according to the Page and PerPage
        settings. Page must be greater than 0.

        :model: The Fluxx ModelObject you wish to query
        :page: Section of the total list to retrieve, must be greater than 0.
        :per_page: Number of records to return per page.
        :returns: None

        """
        global MODEL
        MODEL = model

        client = fluxx.FluxxClient.from_env(INSTANCE)
        records = client.list(model, cols=list(cols), fltr=filter, page=page, per_page=per_page)

        sys.stdout.write(str(json.dumps(records)))

    def write(self, model, delete=False, migrate=False, threads=THREAD_COUNT):
        """Create records from input stream.

        --delete | Delete records rather than creating/updating them.
        --migrate | Use 'migrate_id' in place of regular id field.
        --threads | Number of connections to Fluxx API to use.

        """
        global MODEL
        MODEL = model
        global THREAD_COUNT
        THREAD_COUNT = threads

        records = self._read_input()
        records_num = len(records)
        in_q, out_q = start_workers(records_num, delete, migrate)

        for i, record in enumerate(records):
            in_q.put((i, record))

        while not out_q.full():
            output = list(out_q.queue)
            output_num = len(output)
            errors = list(filter(lambda x: x['error'] is not None, output))
            errors_num = len(errors)
            successes_num = output_num - errors_num
            progress_percentage = float(output_num) / float(records_num)

            header = '%s, on instance '
            progress_bar = '%d successes, %d failures of %d total. %.2f%% complete\r' \
                    % (successes_num, errors_num, records_num, progress_percentage*100)
            sys.stderr.write(progress_bar)
            sys.stderr.flush()

        output = list(out_q.queue)
        output = sorted(output, key=lambda k: k['index'])
        sys.stdout.write(json.dumps(output))

    def _read_input(self):
        """TODO: Docstring for _read_input.
        :returns: TODO

        """
        json_data = sys.stdin.read()
        records = json.loads(json_data)

        if 'records' in records:
            records = records['records']

        return records

    def csv_to_json(self, file_name):
        """TODO: Docstring for csv_to_json.

        :file_name: csv_file
        :returns: Outs

        """
        name, _ = file_name.split('.')
        jsonfile = name + '.json'

        with open(name + '.csv') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        with open(jsonfile, 'w') as f:
            json_file = json.dump(rows, f)
            sys.stdout.write(jsonfile)


def main():
    fire.Fire(FluxxCLI)
