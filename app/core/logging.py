import logging
from typing import Any

class CustomFormatter(logging.Formatter):
    def format(self, record: Any) -> str:
        if hasattr(record, 'request_id'):
            record.request_id_str = f'[{record.request_id}]'
        else:
            record.request_id_str = ''
        return super().format(record)

def setup_logging() -> None:
    formatter = CustomFormatter(
        '%(asctime)s %(request_id_str)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

setup_logging()