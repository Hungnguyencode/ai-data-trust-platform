from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """
    Logger đơn giản cho giai đoạn đầu.
    Sau này có thể nâng cấp sang YAML logging config.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)