from tls_client import Session, response
from utilities.logger import Logger

class Client:
    
    _client:Session = None
    _timeout:int = 30
    _logger:Logger = None
    _proxies:dict = None
    _headers:dict = None
    
    def __init__(self, logger:Logger):
        self._logger = logger

    def set_timeout(self, timeout:int) -> 'Client':
        self._timeout = timeout
        return self

    def set_proxies(self, proxies:dict) -> 'Client':
        self._proxies = proxies
        return self
    
    def set_headers(self, headers:dict) -> 'Client':
        self._headers = headers
        return self
    
    def init(self) -> 'Client':
        self._client = Session()
        self._client.set_headers(self._headers)
        
        if self._proxies:
            self._client.proxies = self._proxies
            
        self._client.timeout = self._timeout
        return self
        
    def get(self, url:str) -> 'Response':
        try:
            self._logger.info(f"GET {url}")
            return Response(self._client.get(url))
        except:
            self._logger.error(f"Failed to GET {url}")
            return Response(None)

class Response:
    
    _response:response = None
    _status_code:int = 0
    _status:bool = False
    _text:str = None
    
    def __init__(self, response:response):
        if not response:
            return
        self._response = response
        self._status_code = response.status_code
        self._status = response.status
        self._text = response.text
    
    def status_code(self) -> int:
        return self._status_code

    def status(self) -> bool:
        return self._status
    
    def text(self) -> str:
        return self._text
    
    def json(self) -> dict:
        return self._response.json() if self._response else None
    
    