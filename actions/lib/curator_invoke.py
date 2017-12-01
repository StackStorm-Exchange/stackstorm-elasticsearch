# pylint: disable=no-member

from items_selector import ItemsSelector
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
        'indices': [
            'alias', 'allocation', 'close', 'clusterrouting', 'createindex', 'deleteindices',
            'forcemerge', 'indexsettings', 'open', 'reindex', 'replicas',
            'restore', 'rollover', 'shrink'
        ]
    }

    def __init__(self, **opts):
        self.opts = EasyDict(opts)
        self._client = None
        self._iselector = None

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

    @property
    def iselector(self):
        """
        Used to fetch indices/snapshots and apply filter to them.
        """
        if not self._iselector:
            self._iselector = ItemsSelector(self.client, **self.opts)
        return self._iselector

    def fetch(self, act_on, on_nofilters_showall=False):
        """
        Forwarder method to indices/snapshots selector.
        """
        return self.iselector.fetch(act_on=act_on, on_nofilters_showall=on_nofilters_showall)

    def command_kwargs(self, command):
        """
        Return kwargs dict for a specific command options or return empty dict.
        """
        opts = defaultdict(lambda: None, self.opts)

        kwargs = {
            'alias': {'name': opts['name'],
                      'extra_settings': {},
                      'remove': opts['remove']},
            'allocation': {'key': opts['key'],
                           'value': opts[''],
                           'allocation_type': opts['allocation_type'],
                           'wait_for_completion': opts['wait_for_completion'],
                           'wait_interval': opts['wait_interval'],
                           'max_wait': opts['max_wait']},
            'close': {'delete_aliases': opts['delete_aliases']},
            'clusterrouting': {'routing': opts['routing_type'],
                               'setting': opts['setting'],
                               'value': opts['value'],
                               'wait_for_completion': opts['wait_for_completion'],
                               'wait_interval': opts['wait_interval'],
                               'max_wait': opts['max_wait']},
            'createindex': {'name': opts['name']},
            'deleteindices': {'master_timeout': opts['master_timeout']},
            'deletesnapshots': {'retry_interval': opts['retry_interval'],
                                'retry_count': opts['retry_count']},
            'forcemerge': {'max_num_segments': opts['max_num_segments'],
                           'delay': opts['delay']},
            'indexsettings': {'index_settings': {},
                              'ignore_unavailable': opts['ignore_unavailable'],
                              'preserve_existing': opts['preserve_existing']},
            'reindex': {'request_body': opts['request_body'],
                        'refresh': opts['refresh'],
                        'requests_per_second': opts['requests_per_second'],
                        'slices': opts['slices'],
                        'timeout': opts['timeout'],
                        'wait_for_active_shards': opts['wait_for_active_starts'],
                        'wait_for_completion': opts['wait_for_completion'],
                        'wait_interval': opts['wait_interval'],
                        'max_wait': opts['max_wait'],
                        'remote_url_prefix': opts['remote_url_prefix'],
                        'remote_ssl_no_validate': opts['remote_ssl_no_validate'],
                        'remote_certificate': opts['remote_certificate'],
                        'remote_client_cert': opts['remote_client_cert'],
                        'remote_client_key': opts['remote_client_key'],
                        'remote_aws_cert': opts['remote_aws_cert'],
                        'remote_aws_key': opts['remote_aws_key'],
                        'remote_aws_region': opts['remote_aws_region'],
                        'remote_filters': opts['remote_filters'],
                        'migration_prefix': opts['migration_prefix'],
                        'migration_suffix': opts['migration_suffix']},
            'replicas': {'count': opts['count'],
                         'wait_for_completion': opts['wait_for_completion'],
                         'wait_interval': opts['wait_interval'],
                         'max_wait': opts['max_wait']},
            'restore': {'name': opts['name'],
                        'indices': [],
                        'include_aliases': opts['include_alises'],
                        'ignore_unavailable': opts['ignore_unavailable'],
                        'include_global_state': opts['include_global_state'],
                        'partial': opts['partial'],
                        'rename_pattern': opts['rename_pattern'],
                        'extra_settings': {},
                        'wait_for_completion': opts['wait_for_completion'],
                        'wait_interval': opts['wait_interval'],
                        'max_wait': opts['max_wait'],
                        'skip_repo_fs_check': opts['skip_repo_fs_check']},
            'rollover': {'name': opts['name'],
                         'conditions': opts['rollover'],
                         'extra_settings': None or {},
                         'wait_for_active_shards': opts['wait_for_active_shards']},
            'shrink': {'shrink_node': opts['shrink_node'],
                       'node_filters': {},
                       'number_of_shards': opts['number_of_shards'],
                       'number_of_replicas': opts['number_of_replicas'],
                       'shrink_prefix': opts['shrink_prefix'],
                       'shrink_suffix': opts['shrink_suffix'],
                       'copy_aliases': opts['copy_aliases'],
                       'delete_after': opts['delete_after'],
                       'post_allocation': {},
                       'wait_for_active_shards': opts['wait_for_active_shards'],
                       'extra_settings': {},
                       'wait_for_completion': opts['wait_for_completion'],
                       'wait_interval': opts['wait_interval'],
                       'max_wait': opts['max_wait']},
            'snapshot': {'repository': opts['repository'],
                         'name': opts['name'],
                         'wait_for_completion': opts['wait_for_completion'],
                         'wait_interval': opts['wait_interval'],
                         'max_wait': opts['max_wait'],
                         'ignore_unavailable': opts['ignore_unavailable'],
                         'include_global_state': opts['include_global_state'],
                         'partial': opts['partial'],
                         'skip_repo_fs_check': opts['skip_repo_fs_check']}
        }.get(command, {})
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
        mdict = {'alias': 'Alias',
                 'allocation': 'Allocation',
                 'close': 'Close',
                 'clusterrouting': 'ClusterRouting',
                 'createindex': 'CreateIndex',
                 'deleteindices': 'DeleteIndices',
                 'forcemerge': 'ForceMerge',
                 'indexsettings': 'IndexSettings',
                 'open': 'Open',
                 'reindex': 'Reindex',
                 'replicas': 'Replicas',
                 'restore': 'Restore',
                 'rollover': 'Rollover',
                 'shrink': 'Shrink',
                 'snapshot': 'Snapshot'}

        method = mdict[command]

        # List is too big and it will be proceeded in chunks.
        if len(curator.utils.to_csv(ilo.indices)) > 3072:
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
            return self._call_api(method, ilo, **kwargs)

    def command_on_snapshots(self, command, ilo):
        """Invoke command which acts on snapshots and perform an api call.
        """
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

        # Timebase filtering
        if opts.source is not None:
            # TODO: Check if other required variables used by filter_by_age are required
            ilo.filter_by_age(source=opts.source, direction=opts.direction,
                              timestring=opts.timestring, unit=opts.time_unit,
                              unit_count=opts.unit_count, unit_count_pattern=None, field=None,
                              stats_result=None, epoch=None, exclude=False)

        # Regex filtering
        if opts.timestring is not None:
            ilo.filter_by_regex(kind='timestamp', value=opts.timestring, exclude=opts.exclude)

        patternbased = zip(('suffix', 'prefix', 'regex'),
                           (opts.suffix, opts.prefix, opts.regex))

        for opt, value in patternbased:
            if value is None:
                continue
            ilo.filter_by_regex(kind=opt, value=value, exclude=opts.exclude)

        if ilo and command == 'close':
            ilo.filter_closed(exclude=True)

        if ilo and command == 'open':
            print 'command == open'
            ilo.filter_opened(exclude=True)

        if ilo and command == 'forcemerge':
            ilo.filter_forceMerged(max_num_segments=opts.max_num_segments, exclude=True)

# TODO: Need to determine if it makes sense to run the following filters - how should we pass
# the parameters?

#        if ilo and command == 'allocate':
#            ilo.filter_allocated(key=None, value=None, allocation_type='require', exclude=True)
#
#        if ilo and command == 'alias':
#            ilo.filter_by_alias(aliases=None, exclude=False)
#
#        ilo.filter_by_count(count=opts.count, reverse=opts.reverse, use_age=opts.use_age,
#                            pattern=opts.pattern, source=opts.source, timestring=opts.timestring,
#                            field=opts.field, stats_result=opts.stats_result, exclude=opts.exclude)
#
#        ilo.filter_period(period_type='relative', source='name', range_from=None,
#                          range_to=None, date_from=None, date_to=None, date_from_format=None,
#                          date_to_format=None, timestring=None, unit=None, field=None,
#                          stats_result='min_value', intersect=False, week_starts_on='sunday',
#                          epoch=None, exclude=False)

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
