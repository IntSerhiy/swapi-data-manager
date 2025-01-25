import argparse
import json
import requests
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class SWAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def fetch_json(self, endpoint: str) -> list:
        all_data = []
        url = f"{self.base_url}{endpoint}/"

        while url:
            logger.info(f"Отримання даних з: {url}")

            response = requests.get(url)
            response.raise_for_status()  # Генерація помилки для невдалих запитів
            data = response.json()
            all_data.extend(data['results'])

            url = data.get('next')

        return all_data


class SWAPIDataManager:
    def __init__(self, client: SWAPIClient):
        self.client = client
        self.data = {}

    def fetch_entity(self, endpoint: str):
        raw_data = self.client.fetch_json(endpoint)
        self.data[endpoint] = pd.DataFrame(raw_data)

    def apply_filter(self, endpoint: str, columns_to_drop: list):
        if endpoint in self.data:
            self.data[endpoint].drop(columns=columns_to_drop, inplace=True)

    def save_to_excel(self, filename: str):
        with pd.ExcelWriter(filename) as writer:
            for endpoint, df in self.data.items():
                df.to_excel(writer, sheet_name=endpoint.capitalize(), index=False)


def main():
    parser = argparse.ArgumentParser(description="SWAPI Data Manager")
    parser.add_argument('--endpoint', required=True,
                        help="Список сутностей через кому (наприклад, people,planets,films)")
    parser.add_argument('--output', required=True, help="Ім'я вихідного Excel-файлу")
    parser.add_argument('--filters', required=True, help="JSON-рядок з фільтрами для кожної сутності")

    args = parser.parse_args()

    client = SWAPIClient(base_url="https://swapi.dev/api/")

    manager = SWAPIDataManager(client)

    filters = json.loads(args.filters)

    for endpoint in args.endpoint.split(','):
        manager.fetch_entity(endpoint)
        if endpoint in filters:
            manager.apply_filter(endpoint, filters[endpoint])

    manager.save_to_excel(args.output)
    print(f"Дані успішно збережено у файл {args.output}")


if __name__ == "__main__":
    main()


