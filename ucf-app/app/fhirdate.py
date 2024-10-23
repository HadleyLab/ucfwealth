import datetime
from typing import cast

import pytz

from app import config
from app.config import local_tz

FHIR_DATE_TIME_META_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
FHIR_DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
FHIR_TIME_FORMAT = "%H:%M:%S"
FHIR_DATE_FORMAT = "%Y-%m-%d"
HUMAN_DATE_FORMAT = "%d/%m/%Y"
HUMAN_TIME_FORMAT = "%H:%M"
# TODO: think about converting all human formats to unified format
HUMAN_DATE_TIME_FORMAT = "%d.%m.%Y %H:%M"


def get_now():
    return local_tz.normalize(pytz.utc.localize(datetime.datetime.utcnow().replace(microsecond=0)))


def parse_time(time: str):
    return datetime.datetime.strptime(time, FHIR_TIME_FORMAT).time()


def parse_date_time(date: str):
    try:
        return local_tz.normalize(
            pytz.utc.localize(datetime.datetime.strptime(date, FHIR_DATE_TIME_FORMAT))
        )
    except ValueError:
        return local_tz.localize(datetime.datetime.strptime(date, FHIR_DATE_FORMAT))


def parse_date(date: str):
    return datetime.datetime.strptime(date, FHIR_DATE_FORMAT).date()


def tz_min(date: datetime.datetime):
    return date.replace(hour=0, minute=0, second=0)


def tz_max(date: datetime.datetime):
    return date.replace(hour=23, minute=59, second=59)


def format_fhir_date(date: datetime.date | datetime.datetime):
    if isinstance(date, datetime.datetime):
        date = pytz.utc.normalize(date)

    return date.strftime(FHIR_DATE_FORMAT)


def format_fhir_date_time(date: datetime.datetime):
    return pytz.utc.normalize(date).strftime(FHIR_DATE_TIME_FORMAT)


def format_local_date(date: str | datetime.datetime | datetime.date):
    if isinstance(date, str):
        date = parse_date_time(date)

    return cast(datetime.datetime | datetime.date, date).strftime(HUMAN_DATE_FORMAT)


def format_local_time(date: str | datetime.datetime):
    if isinstance(date, str):
        date = parse_date_time(date)

    return cast(datetime.datetime | datetime.date, date).strftime(HUMAN_TIME_FORMAT)


def format_local_date_time(date: str | datetime.date):
    if isinstance(date, str):
        date = parse_date_time(date)

    return cast(datetime.datetime | datetime.date, date).strftime(HUMAN_DATE_TIME_FORMAT)


def format_timestamp_as_local_datetime(
    timestamp: int | None,
    dt_format: str,
) -> str | None:
    if timestamp:
        return (
            pytz.utc.localize(datetime.datetime.utcfromtimestamp(timestamp / 1000))
            .astimezone(config.local_tz)
            .strftime(dt_format)
        )

    return None


def extract_date(date: str):
    """
    >>> extract_date("2020-01-01T10:00:00Z")
    '2020-01-01'
    """
    return date[:10]
