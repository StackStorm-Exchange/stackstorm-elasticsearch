import unittest
from unittest.mock import patch
from curator_runner import CuratorRunner


class TestCuratorRunner(unittest.TestCase):

    @patch('curator_runner.CuratorAction.__init__', return_value=None)
    @patch('curator_runner.CuratorRunner.set_up_logging')
    @patch('curator_runner.CuratorRunner.do_command')
    def test_run_with_host_and_port(self, mock_do_command, mock_set_up_logging,
                                    mock_curator_action_init):
        # Arrange
        runner = CuratorRunner()
        runner.config = {'host': 'localhost', 'port': 9200}
        action = 'test_action'
        log_level = 'INFO'
        dry_run = True
        operation_timeout = 300
        mock_curator_action_init.return_value = None

        # Act
        runner.run(action=action, log_level=log_level, dry_run=dry_run,
                   operation_timeout=operation_timeout)

        # Assert
        self.assertEqual(runner._action, action)
        self.assertEqual(runner.config['timeout'], operation_timeout)
        self.assertEqual(runner.config['log_level'], log_level)
        self.assertEqual(runner.config['dry_run'], dry_run)
        self.assertEqual(runner.config['host'], 'localhost')
        self.assertEqual(runner.config['port'], 9200)
        mock_set_up_logging.assert_called_once()
        mock_do_command.assert_called_once()

    @patch('curator_runner.CuratorAction.__init__', return_value=None)
    @patch('curator_runner.CuratorRunner.set_up_logging')
    @patch('curator_runner.CuratorRunner.do_command')
    def test_run_without_host_and_port(self, mock_do_command, mock_set_up_logging,
                                       mock_curator_action_init):
        # Arrange
        runner = CuratorRunner()
        runner.config = {}
        action = 'test_action'
        log_level = 'INFO'
        dry_run = True
        operation_timeout = 300
        mock_curator_action_init.return_value = None

        # Act
        runner.run(action=action, log_level=log_level, dry_run=dry_run,
                   operation_timeout=operation_timeout)

        # Assert
        self.assertEqual(runner._action, action)
        self.assertEqual(runner.config['timeout'], operation_timeout)
        self.assertEqual(runner.config['log_level'], log_level)
        self.assertEqual(runner.config['dry_run'], dry_run)
        self.assertNotIn('host', runner.config)
        self.assertNotIn('port', runner.config)
        mock_set_up_logging.assert_called_once()
        mock_do_command.assert_called_once()


if __name__ == '__main__':
    unittest.main()
