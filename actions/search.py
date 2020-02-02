# pylint: disable=no-member
from __future__ import print_function

from easydict import EasyDict
from lib.esbase_action import ESBaseAction
import curator
import logging
import sys
import elasticsearch
import json

logger = logging.getLogger(__name__)


class SearchRunner(ESBaseAction):

    def __init__(self, config=None):
        super(SearchRunner, self).__init__(config=config)
        self._return_object = False

    def run(self, action=None, log_level='WARNING', operation_timeout=600, **kwargs):
        kwargs.update({
            'timeout': int(operation_timeout),
            'log_level': log_level
        })

        config = EasyDict(self.config)
        self.config = EasyDict(kwargs)

        if config.get('host') is not None:
            self.config.update({'host': config.get('host')})
        if config.get('port') is not None:
            self.config.update({'port': config.get('port')})

        self.set_up_logging()

        self._return_object = kwargs.get('return_object', False)

        if action.endswith('.q'):
            return self.simple_search()
        else:
            return self.full_search()

    def simple_search(self):
        """Perform URI-based request search.
        """
        accepted_params = ('q', 'df', 'default_operator', 'from', 'size')
        kwargs = {k: self.config[k] for k in accepted_params if self.config[k]}
        wl = curator.IndexList(self.client)
        indices = ','.join(wl.working_list())

        try:
            result = self.client.search(index=indices, **kwargs)
        except elasticsearch.ElasticsearchException as e:
            logger.error(e.message)
            sys.exit(2)

        if self._return_object:
            return True, result
        else:
            self._pp_exit(result)
            return None

    def full_search(self):
        """Perform search using Query DSL.
        """
        accepted_params = ('from', 'size')
        kwargs = {k: self.config[k] for k in accepted_params if self.config[k]}
        try:
            result = self.client.search(index=self.config.index,
                                        body=self.config.body, **kwargs)
        except elasticsearch.ElasticsearchException as e:
            logger.error(e.message)
            sys.exit(2)

        if self._return_object:
            return True, result
        else:
            self._pp_exit(result)
            return None

    def _pp_exit(self, data):
        """Print Elastcsearch JSON response and exit.
        """
        kwargs = {}
        if self.config.pretty:
            kwargs = {'indent': 4}
        print(json.dumps(data, **kwargs))

        if data['hits']['total'] > 0:
            sys.exit(0)
        else:
            sys.exit(1)
