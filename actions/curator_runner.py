# pylint: disable=no-member

from easydict import EasyDict
from lib.curator_action import CuratorAction
import logging

logger = logging.getLogger(__name__)


class CuratorRunner(CuratorAction):

    def run(self, action=None, log_level='WARNING', dry_run=False, operation_timeout=600, **kwargs):
        """Curator based action entry point
        """
        self._action = action
        kwargs.update({
            'timeout': int(operation_timeout),
            'log_level': log_level,
            'dry_run': dry_run,
        })

        config = EasyDict(self.config)
        self.config = EasyDict(kwargs)

        if config.get('host') is not None:
            self.config.update({'host': config.get('host')})
        if config.get('port') is not None:
            self.config.update({'port': config.get('port')})

        self.set_up_logging()
        self.do_command()
