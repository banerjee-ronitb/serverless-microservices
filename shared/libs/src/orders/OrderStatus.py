from enum import Enum


class OrderStatus(Enum):
    CREATED = "CREATED",
    CANCELLED = "CANCELLED",
    CONFIRMED = "CONFIRMED",


