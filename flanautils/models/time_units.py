from dataclasses import dataclass

from flanautils import constants, strings
from flanautils.models.bases import FlanaBase


@dataclass(unsafe_hash=True)
class TimeUnits(FlanaBase):
    """
    Represents the time information grouping it into typical units.

    You can represent that tense in textual form according to the language.

    >>> time_units = TimeUnits(hours=1.5, seconds=120.5)
    >>> time_units
    TimeUnits(years=0, months=0, weeks=0, days=0, hours=1, minutes=32, seconds=0.5)
    >>> time_units.to_words()
    '1 hora y 32 minutos'
    >>> time_units.to_words(integer_seconds=False)
    '1 hora, 32 minutos y 0.5 segundos'
    >>> time_units = TimeUnits(years=1/12, days=1, minutes=0.1)
    >>> time_units
    TimeUnits(years=0, months=1, weeks=0, days=1, hours=0, minutes=0, seconds=6.0)
    >>> time_units.to_words()
    '1 mes, 1 día y 6 segundos'
    >>> time_units = TimeUnits(days=180)
    >>> time_units
    TimeUnits(years=0, months=5, weeks=3, days=6, hours=21, minutes=59, seconds=54.23999999868329)
    >>> time_units.to_words()
    '5 meses, 3 semanas, 6 días, 21 horas, 59 minutos y 54 segundos'
    >>> time_units.to_years()
    0.49315046875595886
    >>> time_units.to_months()
    5.917805625071506
    >>> time_units.to_weeks()
    25.714285714285715
    >>> time_units.to_days()
    180.0
    >>> time_units.to_hours()
    4320.0
    >>> time_units.to_minutes()
    259200.0
    >>> time_units.to_seconds()
    15552000.0
    """

    years: int = 0
    months: int = 0
    weeks: int = 0
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: float = 0

    def __init__(self, years: float = 0, months: float = 0, weeks: float = 0, days: float = 0, hours: float = 0, minutes: float = 0, seconds: float = 0):
        quotient, remainder = divmod(seconds, 60)
        seconds = remainder
        minutes += quotient

        quotient, remainder = divmod(minutes, 60)
        minutes = remainder
        hours += quotient

        quotient, remainder = divmod(hours, 24)
        hours = remainder
        days += quotient

        quotient, remainder = divmod(days, 7)
        days = remainder
        weeks += quotient

        quotient, remainder = divmod(weeks, constants.WEEKS_IN_A_MONTH)
        weeks = remainder
        months += quotient

        quotient, remainder = divmod(months, 12)
        months = remainder
        years += quotient

        months += years % 1 * 12
        weeks += months % 1 * constants.WEEKS_IN_A_MONTH
        days += weeks % 1 * 7
        hours += days % 1 * 24
        minutes += hours % 1 * 60
        seconds += minutes % 1 * 60

        self.years = int(years)
        self.months = int(months)
        self.weeks = int(weeks)
        self.days = int(days)
        self.hours = int(hours)
        self.minutes = int(minutes)
        self.seconds = seconds

    def to_years(self) -> float:
        return self.to_months() / 12

    def to_months(self) -> float:
        return self.to_weeks() / constants.WEEKS_IN_A_MONTH

    def to_weeks(self) -> float:
        return self.to_days() / 7

    def to_days(self) -> float:
        return self.to_hours() / 24

    def to_hours(self) -> float:
        return self.to_minutes() / 60

    def to_minutes(self) -> float:
        return self.to_seconds() / 60

    def to_seconds(self) -> float:
        months = 12 * self.years
        weeks = constants.WEEKS_IN_A_MONTH * (self.months + months)
        days = 7 * (self.weeks + weeks)
        hours = 24 * (self.days + days)
        minutes = 60 * (self.hours + hours)
        seconds = 60 * (self.minutes + minutes)

        return self.seconds + seconds

    total_seconds = to_seconds

    def to_words(self, language='es', integer_seconds=True) -> str:
        if language == 'es':
            translation = {
                'years': {'singular': 'año', 'plural': 'años'},
                'months': {'singular': 'mes', 'plural': 'meses'},
                'weeks': {'singular': 'semana', 'plural': 'semanas'},
                'days': {'singular': 'día', 'plural': 'días'},
                'hours': {'singular': 'hora', 'plural': 'horas'},
                'minutes': {'singular': 'minuto', 'plural': 'minutos'},
                'seconds': {'singular': 'segundo', 'plural': 'segundos'}
            }
            separator = ', '
            last_separator = ' y '
        elif language == 'en':
            translation = {
                'years': {'singular': 'year', 'plural': 'years'},
                'months': {'singular': 'month', 'plural': 'months'},
                'weeks': {'singular': 'week', 'plural': 'weeks'},
                'days': {'singular': 'day', 'plural': 'days'},
                'hours': {'singular': 'hour', 'plural': 'hours'},
                'minutes': {'singular': 'minute', 'plural': 'minutes'},
                'seconds': {'singular': 'second', 'plural': 'seconds'}
            }
            separator = ', '
            last_separator = ' and '
        else:
            raise NotImplementedError('not implemented for that language')

        self_vars = vars(self).copy()
        if integer_seconds:
            self_vars['seconds'] = int(self_vars['seconds'])
        words = (f"{v} {translation[k]['singular'] if v == 1 else translation[k]['plural']}" for k, v in self_vars.items() if v)
        return strings.join_last_separator(words, separator, last_separator)
