import argparse
import requests
import logging
import pandas as pd
from abc import ABC, abstractmethod

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
            response.raise_for_status()
            data = response.json()
            all_data.extend(data['results'])

            url = data.get('next')

        return all_data


class EntityProcessor(ABC):
    @abstractmethod
    def process(self, json_data: list) -> pd.DataFrame:
        pass


class PeopleProcessor(EntityProcessor):
    def process(self, json_data: list) -> pd.DataFrame:
        df = pd.DataFrame(json_data)
        df['full_name'] = df['name']
        return df


class PlanetsProcessor(EntityProcessor):
    def process(self, json_data: list) -> pd.DataFrame:
        df = pd.DataFrame(json_data)
        df['population'] = pd.to_numeric(df['population'], errors='coerce')  # Перетворення population на числовий формат
        return df


class FilmsProcessor(EntityProcessor):

    def process(self, json_data: list) -> pd.DataFrame:
        df = pd.DataFrame(json_data)
        df['release_year'] = pd.to_datetime(df['release_date']).dt.year  # Додавання року випуску
        return df


class SWAPIDataManager:
    def __init__(self, client: SWAPIClient):
        self.client = client
        self.processors = {}
        self.data = {}

    def register_processor(self, endpoint: str, processor: EntityProcessor):
        self.processors[endpoint] = processor

    def fetch_entity(self, endpoint: str):
        if endpoint not in self.processors:
            raise ValueError(f"Процесор для '{endpoint}' не зареєстрований.")

        raw_data = self.client.fetch_json(endpoint)
        processor = self.processors[endpoint]
        self.data[endpoint] = processor.process(raw_data)

    def save_to_excel(self, filename: str):
        with pd.ExcelWriter(filename) as writer:
            for endpoint, df in self.data.items():
                df.to_excel(writer, sheet_name=endpoint.capitalize(), index=False)


def main():
    parser = argparse.ArgumentParser(description="SWAPI Data Manager")
    parser.add_argument('--endpoint', required=True,
                        help="Список сутностей через кому (наприклад, people,planets,films)")
    parser.add_argument('--output', required=True, help="Ім'я вихідного Excel-файлу")
    args = parser.parse_args()

    client = SWAPIClient(base_url="https://swapi.dev/api/")
    manager = SWAPIDataManager(client)

    manager.register_processor("people", PeopleProcessor())
    manager.register_processor("planets", PlanetsProcessor())
    manager.register_processor("films", FilmsProcessor())

    for endpoint in args.endpoint.split(','):
        manager.fetch_entity(endpoint)

    manager.save_to_excel(args.output)
    print(f"Дані успішно збережено у файл {args.output}")


if __name__ == "__main__":
    main()
