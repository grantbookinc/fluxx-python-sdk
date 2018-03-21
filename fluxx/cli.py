#!/usr/bin/env python3

import os
import sys
import logging
import threading
import queue
import json

import fire

import fluxx


logger = logging.getLogger(__name__)


class FluxxWorker(threading.Thread):

    """Spawns a new thread performing Fluxx API
    create and update requests."""

    def __init__(self, queue, instance=None, model=None):
        self.q = queue
        self.client = fluxx.get_fluxx_client(instance)
        self.model = model

        super().__init__()

    def run(self):
        while True:
            item = self.q.get()

            try:
                rec_id = item.get('id')
                if rec_id:
                    new = self.client.update(self.model, rec_id, item)
                    print('Updated', new['id'])
                else:
                    new = self.client.create(self.model, item)
                    print('Created', new['id'])

            except NotImplementedError:
                logger.error('Process method not implemented.')
            except fluxx.FluxxError as e:
                logger.error(e)
                print(e)
            finally:
                self.q.task_done()


class FluxxMigration(object):

    """Command line interface to this API wrapper, reads and writes JSON."""


    def __init__(self, instance=None):
        self.instance = instance


    def crud(self, model, threads=12):
        """Creates or updates a each record provided in the list.
        The non-null status of the 'id' attribute of every record determines
        whether it will be created or updated, with None value IDs defaulting
        to creation.

        :model: The Fluxx ModelObject you wish to create.
        :returns: None

        """
        q = queue.Queue()

        input_data = sys.stdin.read()
        for record in json.loads(input_data):
            q.put(record)

        for _ in range(threads):
            worker = FluxxWorker(q, self.instance, model)
            worker.daemon = True
            worker.start()

        q.join()

    def list(self, model, cols, page=1, per_page=100):
        """Return a list of records according to the Page and PerPage
        settings. Page must be greater than 0.

        :model: The Fluxx ModelObject you wish to query
        :page: Section of the total list to retrieve, must be greater than 0.
        :per_page: Number of records to return per page.
        :returns: None

        """
        client = fluxx.get_fluxx_client(self.instance)
        records = client.list(model, cols=list(cols), page=page, per_page=per_page)

        print(json.dumps(records))


def main():
    fire.Fire(FluxxMigration)


if __name__ == "__main__":
    fire.Fire(FluxxMigration)
