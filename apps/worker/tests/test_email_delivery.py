from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import Mock, patch

import worker_tasks


def test_resend_transport_uses_https_api():
    message = MIMEMultipart("alternative")
    message["From"] = "Pacific North Systems <hello@pacificnorthsystems.com>"
    message["To"] = "lead@example.com"
    message["Subject"] = "Assessment results"
    message.attach(MIMEText("<p>Your results</p>", "html"))

    response = Mock()
    response.raise_for_status.return_value = None
    with patch.object(worker_tasks.httpx, "post", return_value=response) as post:
        worker_tasks._send_email({"resend_api_key": "test-key"}, message)

    request = post.call_args
    assert request.args[0] == "https://api.resend.com/emails"
    assert request.kwargs["json"]["to"] == ["lead@example.com"]
    assert request.kwargs["json"]["html"] == "<p>Your results</p>"
    assert request.kwargs["headers"]["Authorization"] == "Bearer test-key"
    response.raise_for_status.assert_called_once()

