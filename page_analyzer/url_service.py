import requests
from bs4 import BeautifulSoup
from typing import Dict, Union, Tuple, List
from urllib.parse import urlparse

NOT_FOUND = "Не найден"


class UrlService:
    def __init__(self, repo) -> None:
        self.repo = repo

    def fetch_web_content(self, url: str) -> Dict[str, Union[int, str]]:
        try:
            content, status_code = self._get_web_content(url)
            parsed_content = self._parse_web_content(content)
            parsed_content["status_code"] = status_code
            return parsed_content

        except requests.RequestException as e:
            return {"status_code": 500, "error": str(e)}

    def fetch_and_store_web_content(self, url_id: int) -> Dict[str, Union[int, str]]:
        url = self.repo.get_url_name_by_id(url_id)
        check_results = self.fetch_web_content(url)

        if "error" not in check_results:
            self.repo.insert_url_check(url_id, check_results)

        return check_results

    def get_combined_url_data(self) -> List[Dict]:
        basic_url_data = self.fetch_basic_url_data()
        basic_url_dict = {url[0]: url[1] for url in basic_url_data}
        latest_checks_data = self.fetch_latest_checks()
        latest_checks_dict = {
            check[0]: {"date": check[1], "status_code": check[2]}
            for check in latest_checks_data
        }

        url_data = []
        for url_id, url_name in basic_url_dict.items():
            latest_check = latest_checks_dict.get(url_id)
            if latest_check:
                url_data.append(
                    {
                        "url_id": url_id,
                        "url_name": url_name,
                        "latest_check_date": latest_check["date"],
                        "status_code": latest_check["status_code"],
                    }
                )
        return url_data

    # Repository Interaction Methods

    def get_url_data(self, url_id: int) -> Tuple:
        return self.repo.get_url_data(url_id)

    def get_url_checks(self, url_id: int) -> List:
        return self.repo.get_url_checks(url_id)

    def get_id_url_if_exists(self, url: str) -> int:
        return self.repo.get_url_id_by_name(url)

    def insert_url_and_return_id(self, url: str) -> None:
        return self.repo.insert_url_and_return_id(url)

    def fetch_basic_url_data(self) -> list:
        return self.repo.fetch_basic_url_data()

    def fetch_latest_checks(self) -> list:
        return self.repo.fetch_latest_checks()

    # Helper Methods

    def _get_web_content(self, url: str) -> Tuple[str, int]:
        url_response = requests.get(url)
        url_response.raise_for_status()
        return url_response.text, url_response.status_code

    def _parse_web_content(self, content: str) -> Dict[str, str]:
        soup = BeautifulSoup(content, "html.parser")
        h1 = self._get_element_text(soup, "h1")
        title = self._get_element_text(soup, "title")
        description = self._get_meta_description(soup)
        return {"h1": h1, "title": title, "description": description}

    def _get_element_text(self, soup, tag_name: str) -> str:
        element = soup.find(tag_name)
        return element.text.strip() if element else NOT_FOUND

    def _get_meta_description(self, soup) -> str:
        description = soup.find("meta", attrs={"name": "description"})
        return description.get("content", "").strip() if description else NOT_FOUND

    # URL Parsing Methods

    def parse_and_serialize_form(self, raw_url: str) -> str:
        url = raw_url.lower()
        parsed_url = urlparse(url)
        netloc = self._strip_www_from_netloc(parsed_url.netloc)
        return f"{parsed_url.scheme}://{netloc}"

    def _strip_www_from_netloc(self, netloc: str) -> str:
        return netloc[4:] if netloc.startswith("www.") else netloc
