from tls_client import Session, response
from utilities.logger import Logger
from typing import Optional, Dict, Any

DEFAULT_TIMEOUT = 30


class Client:
    """
    A client for making HTTP requests with optional proxy and custom headers.
    """

    def __init__(self, logger: Logger):
        self._client: Optional[Session] = None
        self._timeout: int = DEFAULT_TIMEOUT
        self._logger: Logger = logger
        self._proxies: Optional[Dict[str, str]] = None
        self._headers: Optional[Dict[str, str]] = None

    def set_timeout(self, timeout: int) -> "Client":
        """
        Set the timeout for the client.
        """
        self._timeout = timeout
        return self

    def set_proxies(self, proxies: Dict[str, str]) -> "Client":
        """
        Set the proxies for the client.
        """
        self._proxies = proxies
        return self

    def set_headers(self, headers: Dict[str, str]) -> "Client":
        """
        Set the headers for the client.
        """
        self._headers = headers
        return self

    def init(self) -> "Client":
        """
        Initialize the client session with the configured headers, proxies, and timeout.
        """
        self._client = Session()
        if self._headers:
            self._client.set_headers(self._headers)

        if self._proxies:
            self._client.proxies = self._proxies

        self._client.timeout = self._timeout
        return self

    def get(self, url: str) -> "Response":
        """
        Perform a GET request to the specified URL.
        """
        try:
            self._logger.debug(f"GET {url}")
            response = self._client.get(url)
            return Response(response)
        except Exception as e:
            self._logger.debug(f"Failed to GET {url}: {e}")
            return Response(None)


class Response:
    """
    A wrapper for the HTTP response.
    """

    def __init__(self, resp: Optional[response.Response]):
        self._response: Optional[response.Response] = resp
        self._status_code: int = resp.status_code if resp else 0
        self._text: Optional[str] = resp.text if resp else None

    def status_code(self) -> int:
        """
        Get the status code of the response.
        """
        return self._status_code

    def ok(self) -> bool:
        """
        Get the status of the response.
        """
        return self.status_code() == 200

    def text(self) -> Optional[str]:
        """
        Get the text content of the response.
        """
        return self._text

    def json(self) -> Optional[Dict[str, Any]]:
        """
        Get the JSON content of the response.
        """
        return self._response.json() if self._response else None
