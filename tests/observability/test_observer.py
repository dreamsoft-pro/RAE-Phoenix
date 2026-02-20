from unittest.mock import MagicMock, patch

from feniks.observability.observer import ObservabilityFacade


@patch("feniks.observability.observer.get_metrics_collector")
@patch("feniks.observability.observer.log")
def test_observability_record_event(mock_log, mock_metrics_getter):
    mock_metrics = MagicMock()
    mock_metrics_getter.return_value = mock_metrics

    obs = ObservabilityFacade()
    obs.record_event("user_login", {"user_id": "123"})

    mock_log.info.assert_called_with("Event: user_login", extra={"user_id": "123"})
    mock_metrics.inc.assert_called_with("event_user_login")


@patch("feniks.observability.observer.log")
@patch("feniks.observability.observer.get_metrics_collector")
def test_observability_record_metric(mock_metrics_getter, mock_log):
    obs = ObservabilityFacade()
    obs.record_metric("cpu_usage", 0.5)
    mock_log.debug.assert_called()
