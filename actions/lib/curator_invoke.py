# pylint: disable=no-member

from utils import compact_dict, get_client
from curator.utils import chunk_index_list
from easydict import EasyDict
from collections import defaultdict
from curator.defaults import settings
from curator.validators import options
import curator
import json
import logging
import sys

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

    def get_action_method(self, act_on, command):
        settings_map = {'indices': settings.index_actions,
                        'snapshots': settings.snapshot_actions,
                        'cluster': settings.cluster_actions}

        lookup = settings_map.get(act_on)
        if lookup is None:
            raise ValueError('invalid action: ' + act_on)

        if command not in set(lookup()):
            print 'Cannot find command ' + command + ' in ' + act_on
            sys.exit(3)

        method = command.title().replace('_', '')

        # This is the only exception to the above rule
        if method == 'Forcemerge':
            method = 'ForceMerge'

        return method

    def fetch(self, act_on, on_nofilters_showall=False):
        """
        Forwarder method to indices/snapshots selector.
        """
        if act_on not in ['indices', 'snapshots', 'cluster']:
            raise ValueError('invalid argument: ' + act_on)

        if act_on == 'indices':
            return curator.IndexList(self.client).working_list()
        elif act_on == 'snapshots':
            return curator.SnapshotList(self.client).working_list()
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
                kwargs.append(k)

        # Define each of the action specific options using values from the opts dict
        command_kwargs = dict()
        for key in kwargs:
            command_kwargs[key] = opts[key]

        return compact_dict(command_kwargs)

    def _call_api(self, act_on, command, method, args, **kwargs):
        """Invoke curator action.
        """

        logger.debug("Performing do_action", method, args, kwargs)

        # print 'Calling ' + method + ' on ' + str(args.indices)
        f = getattr(curator, method)

        o = f(args, **kwargs)
        o.do_action()

        return True

    def command_on_indices(self, act_on, command, ilo):
        """Invoke command which acts on indices and perform an api call.
        """
        kwargs = self.command_kwargs(command)
        print 'kwargs = ' + str(kwargs)

        method = self.get_action_method(act_on, command)

        # List is too big and it will be proceeded in chunks.
        if len(curator.utils.to_csv(ilo.working_list())) > 3072:
            logger.warn('Very large list of indices.  Breaking it up into smaller chunks.')
            success = True
            for indices in chunk_index_list(ilo):
                try:
                    # FIXME: Replace indices with ilo
                    self._call_api(act_on, command, method, indices, **kwargs)
                except Exception:
                    success = False
            return success
        else:
            if command == 'clusterrouting' or command == 'createindex' or command == 'rollover':
                return self._call_api(act_on, command, method, self.client, **kwargs)
            else:
                return self._call_api(act_on, command, method, ilo, **kwargs)

    def command_on_snapshots(self, act_on, command, slo):
        """Invoke command which acts on snapshots and perform an api call.
        """
        # TODO: Handle command 'restore'
        if command == 'snapshot':
            method = 'create_snapshot'
            kwargs = self.command_kwargs(command)
            # The snapshot command should get the full (not chunked)
            # list of indices.
            kwargs['indices'] = slo
            return self._call_api(act_on, command, method, **kwargs)

        elif command == 'delete':
            method = 'delete_snapshot'
            success = True
            for s in slo:
                try:
                    self._call_api(act_on, command, method, repository=self.opts.repository,
                                   snapshot=s)
                except Exception:
                    success = False
            return success
        else:
            # should never get here
            raise RuntimeError("Unexpected method `{}.{}'".format('snapshots', command))

    def _filter_working_list(self, act_on, command):

        working_list = None
        if act_on == 'indices':
            working_list = curator.IndexList(self.client)
        elif act_on == 'snapshots':
            working_list = curator.SnapshotList(self.client)

        opts = self.opts

        if working_list is None:
            logger.error('No %s matched provided args: %s', act_on, opts)
            print "ERROR. No {} found in Elasticsearch.".format(act_on)
            sys.exit(99)

        # Protect against accidental delete
        if command == 'delete_indices' or command == 'delete_snapshots':
            logger.info("Pruning Kibana-related indices to prevent accidental deletion.")
            working_list.filter_kibana()

        # If filter by disk space, filter the ilo by space:
        if working_list and command == 'delete':
            if opts.disk_space:
                working_list.filter_by_space(disk_space=float(opts.disk_space),
                                             reverse=(opts.reverse or True))

        # TODO: If JSON filter string is not defined, check if curator.yml exists (either
        # at a specified path, or the default path ~/.curator/curator.yml).

        # Iterate through all the filters defined in JSON filter string
        if opts.filters is None:
            opts.filters = '{"filtertype": "none"}'

        opts.filters = '{"filters": [' + opts.filters + ']}'
        working_list.iterate_filters(json.loads(opts.filters))

        if not working_list.indices:
            logger.error('No %s matched provided args: %s', act_on, opts)
            print "ERROR. No {} found in Elasticsearch.".format(act_on)
            sys.exit(99)

        return working_list

    def invoke(self, command=None, act_on=None):
        """Invoke command through translating it to curator api call.
        """
        if act_on is None:
            raise ValueError("Requires act_on on `indices', `snapshots', or `cluster'")

        # Get the list of indices and apply filters
        working_list = self._filter_working_list(act_on, command)

        if act_on == 'indices' and command != 'snapshot':
            return self.command_on_indices(act_on, command, working_list)
        elif act_on == 'snapshots':
            return self.command_on_snapshots(act_on, command, working_list)
        else:
            return self.command_on_cluster(act_on, command, working_list)
