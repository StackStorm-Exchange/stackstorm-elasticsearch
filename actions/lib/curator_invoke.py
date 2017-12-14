# pylint: disable=no-member

from utils import compact_dict, get_client
from easydict import EasyDict
from collections import defaultdict
from curator.validators import options
from curator.cli import process_action
import curator
import json
import logging
import os.path

logger = logging.getLogger(__name__)


class CuratorInvoke(object):

    def __init__(self, **opts):
        self.opts = EasyDict(opts)
        self._client = None

    @property
    def client(self):
        if not self._client:
            o = self.opts
            self._client = get_client(**({
                'host': o.host, 'port': o.port, 'url_prefix': o.url_prefix,
                'http_auth': o.http_auth, 'use_ssl': o.use_ssl,
                'master_only': o.master_only, 'timeout': o.timeout
            }))
        return self._client

    def fetch(self, act_on, on_nofilters_showall=False):
        """
        Forwarder method to indices/snapshots selector.
        """
        if act_on not in ['indices', 'snapshots', 'cluster']:
            raise ValueError('invalid argument: ' + act_on)

        if act_on == 'indices':
            return curator.IndexList(self.client)
        elif act_on == 'snapshots':
            return curator.SnapshotList(self.client)
        else:
            return []

    def command_kwargs(self, command):
        """
        Return kwargs dict for a specific command options or return empty dict.
        """
        opts = defaultdict(lambda: None, self.opts)

        kwargs = []

        # Get the available action specific options from curator
        dict_list = options.action_specific(command)

        for d in dict_list:
            for k in d:
                kwargs.append(str(k))

        # Define each of the action specific options using values from the opts dict
        command_kwargs = dict()
        for key in kwargs:
            command_kwargs[key] = opts[key]

        return compact_dict(command_kwargs)

    def run(self, act_on, command):
        """Invoke command which acts on indices and perform an api call.
        """
        kwargs = self.command_kwargs(command)

        config = {'action': command, 'filters': json.loads('[' + self.opts.filters + ']')}

        if command == 'alias':
            kwargs['warn_if_no_indices'] = self.opts.get('warn_if_no_indices', False)
            if self.opts.add is not None:
                config['add'] = json.loads('{"filters": [' + self.opts.add + ']}')
            if self.opts.remove is not None:
                config['remove'] = json.loads('{"filters": [' + self.opts.remove + ']}')
        elif command == 'reindex':
            kwargs['request_body'] = json.loads(self.opts.get('request_body', ''))

        config['options'] = kwargs

        process_action(self.client, config, **kwargs)

        return True

    def _get_filters_from_json(self, fn):
        """Read JSON-formatted filters from the specified file
        """
        filters = '{"filtertype": "none"}'
        name = os.path.expanduser(fn)
        if os.path.exists(name):
            f = open(fn, 'r')
            json_data = f.read().rstrip()
            if len(json_data) > 0:
                filters = json_data

        return filters

    def invoke(self, command=None, act_on=None):
        """Invoke command through translating it to curator api call.
        """
        if act_on is None:
            raise ValueError("Requires act_on on `indices', `snapshots', or `cluster'")

        # If no filters are passed in opts, then try reading them from file opts.curator_json
        if self.opts.filters is None:
            self.opts.filters = self._get_filters_from_json(self.opts.curator_json)

        return self.run(act_on, command)
