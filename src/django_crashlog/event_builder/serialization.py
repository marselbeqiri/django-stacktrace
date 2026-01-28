import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import PurePath
from typing import Any

from django.utils.functional import Promise

JSON_SAFE_TYPES = (str, int, float, bool, type(None), datetime, uuid.UUID, Decimal)


class SerializationHelper:
    """
    Responsible for preparing data structures for DjangoJSONEncoder.
    Converts unknown types to strings to prevent serialization errors.
    """

    @classmethod
    def to_encodable(cls, obj: Any, depth: int = 0, max_depth: int = 5) -> Any:
        if depth > max_depth:
            return str(obj)

        if isinstance(obj, JSON_SAFE_TYPES):
            return obj

        if isinstance(obj, Promise):
            return str(obj)

        if isinstance(obj, dict):
            return {
                str(k): cls.to_encodable(v, depth + 1, max_depth)
                for k, v in obj.items()
            }

        if isinstance(obj, (list, tuple, set)):
            return [cls.to_encodable(item, depth + 1, max_depth) for item in obj]

        if isinstance(obj, PurePath):
            return str(obj)

        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8", errors="replace")
            except Exception:
                return repr(obj)

        try:
            return str(obj)
        except Exception:
            return "[Serialization Failed]"
