import logging


class ends_with_brace(logging.Filter):
    def filter(self, record):
        return str(record.msg).endswith("}")
