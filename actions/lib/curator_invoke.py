# pylint: disable=no-member

from utils import compact_dict, get_client
from curator.utils import chunk_index_list
from easydict import EasyDict
from collections import defaultdict
import curator
import logging
import sys

logger = logging.getLogger(__name__)


class CuratorInvoke(object):
    # Supported curator commands for indices and snapshots.
    SUPPORTS = {
        'snapshots': ['deletesnapshots', 'snapshot'],
        'cluster': ['clusterrouting'],
        'indices': ['alias', 'allocation', 'close', 'clusterrouting', 'createindex',
                    'deleteindices', 'forcemerge', 'indexsettings', 'open', 'reindex',
                    'replicas', 'restore', 'rollover', 'shrink']
    }

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
        if act_on not in ['indices', 'snapshots']:
            raise ValueError('invalid argument: %s', act_on)

        if act_on == 'indices':
            return curator.IndexList(self.client).working_list()
        else:
            return curator.SnapshotList(self.client).working_list()

    def command_kwargs(self, command):
        """
        Return kwargs dict for a specific command options or return empty dict.
        """
        opts = defaultdict(lambda: None, self.opts)

        kwargs = {
            'alias': ['name', 'extra_settings', 'remove'],
            'allocation': ['key', 'value', 'allocation_type', 'wait_for_completion',
                           'wait_interval', 'max_wait'],
            'close': ['delete_aliases'],
            'createindex': ['name'],
            'deleteindices': ['master_timeout'],
            'deletesnapshots': ['retry_interval', 'retry_count'],
            'forcemerge': ['max_num_segments', 'delay'],
            'indexsettings': ['index_settings', 'ignore_unavailable', 'preserve_existing'],
            'reindex': ['request_body', 'refresh', 'requests_per_second', 'slices', 'timeout',
                        'wait_for_active_shards', 'wait_for_completion', 'wait_interval',
                        'max_wait', 'remote_url_prefix', 'remote_ssl_no_validate',
                        'remote_certificate', 'remote_client_cert', 'remote_client_key',
                        'remote_aws_cert', 'remote_aws_key', 'remote_aws_region',
                        'remote_filters', 'migration_prefix', 'migration_suffix'],
            'replicas': ['count', 'wait_for_completion', 'wait_interval', 'max_wait'],
            'restore': ['name', 'indices', 'include_aliases', 'ignore_unavailable',
                        'include_global_state', 'partial', 'rename_pattern',
                        'extra_settings', 'wait_for_completion', 'wait_interval', 'max_wait',
                        'skip_repo_fs_check'],
            'rollover': ['name', 'conditions', 'extra_settings', 'wait_for_active_shards'],
            'shrink': ['shrink_node', 'node_filters', 'number_of_shards', 'number_of_replicas',
                       'shrink_prefix', 'shrink_suffix', 'copy_aliases', 'delete_after',
                       'post_allocation', 'wait_for_active_shards', 'extra_settings',
                       'wait_for_completion', 'wait_interval', 'max_wait'],
            'snapshot': ['repository', 'name', 'wait_for_completion', 'wait_interval',
                         'max_wait', 'ignore_unavailable', 'include_global_state',
                         'partial', 'skip_repo_fs_check']
        }
        kwargs.get(command, {})
        return compact_dict(kwargs)

    def _call_api(self, method, args, **kwargs):
        """Invoke curator action.
        """

        logger.debug("Performing do_action", method, args, kwargs)

        f = getattr(curator, method)
        m = f(args, **kwargs)

        # NOTE: do_action() raises an exception on failure
        m.do_action()

        # Return a true value to indicate a successful api call
        return True

    def command_on_indices(self, command, ilo):
        """Invoke command which acts on indices and perform an api call.
        """
        kwargs = self.command_kwargs(command)
        print 'kwargs = ' + str(kwargs)

        # TODO: Use one data structure for mdict, SUPPORTS and command_kwargs()
        mdict = {'alias': 'Alias',  # (add and remove requires ilo)
                 'allocation': 'Allocation',  # ilo
                 'close': 'Close',  # ilo
                 'clusterrouting': 'ClusterRouting',  # client
                 'createindex': 'CreateIndex',  # client
                 'deleteindices': 'DeleteIndices',  # ilo
                 'forcemerge': 'ForceMerge',  # ilo
                 'indexsettings': 'IndexSettings',  # ilo
                 'open': 'Open',  # ilo
                 'reindex': 'Reindex',  # ilo
                 'replicas': 'Replicas',  # ilo
                 'rollover': 'Rollover',  # client
                 'shrink': 'Shrink',  # ilo
                 'snapshot': 'Snapshot'}  # ilo

        method = mdict[command]

        # List is too big and it will be proceeded in chunks.
        if len(curator.utils.to_csv(ilo.working_list())) > 3072:
            logger.warn('Very large list of indices.  Breaking it up into smaller chunks.')
            success = True
            for indices in chunk_index_list(ilo):
                try:
                    # FIXME: Replace indices with ilo
                    self._call_api(method, indices, **kwargs)
                except Exception:
                    success = False
            return success
        else:
            if command == 'clusterrouting' or command == 'createindex' or command == 'rollover':
                return self._call_api(method, self.client, **kwargs)
            else:
                return self._call_api(method, ilo, **kwargs)

    def command_on_snapshots(self, command, ilo):
        """Invoke command which acts on snapshots and perform an api call.
        """
        # TODO: Handle command 'restore'
        if command == 'snapshot':
            method = 'create_snapshot'
            kwargs = self.command_kwargs(command)
            # The snapshot command should get the full (not chunked)
            # list of indices.
            kwargs['indices'] = ilo
            return self._call_api(method, **kwargs)

        elif command == 'delete':
            method = 'delete_snapshot'
            success = True
            for s in ilo:
                try:
                    self._call_api(method, repository=self.opts.repository, snapshot=s)
                except Exception:
                    success = False
            return success
        else:
            # should never get here
            raise RuntimeError("Unexpected method `{}.{}'".format('snapshots', command))

    def _get_filtered_ilo(self, command, act_on):
        ilo = curator.IndexList(self.client)

        opts = self.opts

        # Protect against accidental delete
        if command == 'delete':
            logger.info("Pruning Kibana-related indices to prevent accidental deletion.")
            ilo.filter_kibana()

        # If filter by disk space, filter the ilo by space:
        if ilo and command == 'delete':
            if opts.disk_space:
                ilo.filter_by_space(disk_space=float(opts.disk_space),
                                    reverse=(opts.reverse or True))

        # TODO: If JSON filter string is not defined, check if curator.yml exists (either
        # at a specified path, or the default path ~/.curator/curator.yml).

        # Iterate through all the filters defined in JSON filter string
        ilo.iterate_filters(json.loads(opts.filters))

        if not ilo.indices:
            logger.error('No %s matched provided args: %s', act_on, opts)
            print "ERROR. No {} found in Elasticsearch.".format(act_on)
            sys.exit(99)

        return ilo

    def invoke(self, command=None, act_on=None):
        """Invoke command through translating it to curator api call.
        """
        if act_on is None:
            raise ValueError("Requires act_on either on `indices' or `snapshots'")
        if command not in self.SUPPORTS[act_on]:
            raise ValueError("Unsupported curator command: {} {}".format(command, act_on))

        # Get the list of indices and apply filters
        ilo = self._get_filtered_ilo(command, act_on)

        if act_on == 'indices' and command != 'snapshot':
            return self.command_on_indices(command, ilo)
        else:
            # Command on snapshots and snapshot command (which
            # actually has selected indices before).
            return self.command_on_snapshots(command, ilo)
