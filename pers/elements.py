import logging
import requests

from requests.exceptions import RequestException

from attrs import define, field

logger = logging.getLogger()


@define
class ElementsClient:
    user: str
    password: str
    proxies: dict = field(default=None)

    def get(self, url: str = ""):
        response = requests.get(
            url,
            auth=(self.user, self.password),
            proxies=self.proxies,
            timeout=10,
        )
        response.raise_for_status()
        return response

    def authenticate(self, url: str):
        try:
            self.get(url)
            logger.info(f"Successfully authenticated to Symplectic Elements.")
        except RequestException:
            logger.info("Failed to authenticate to Symplectic Elements.")
            raise
