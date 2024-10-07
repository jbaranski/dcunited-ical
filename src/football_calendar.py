from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import cache
from hashlib import sha256
from typing import List

from icalendar import Calendar, Event

COMPETITION_TRANSLATE = {
    'Friendlies Clubs': 'Friendly'
}

TEAMS_FIX = {
}


@cache
def get_datetime_from_str(input_str) -> datetime:
    return datetime.fromisoformat(input_str)


@cache
def get_end_datetime(start_time, delta_hours) -> datetime:
    return start_time + timedelta(hours=delta_hours)


@cache
def get_competition_txt(input_str) -> str:
    return COMPETITION_TRANSLATE[input_str] if input_str in COMPETITION_TRANSLATE else input_str


@cache
def get_correct_team_name(input_team_name):
    return TEAMS_FIX[input_team_name] if input_team_name in TEAMS_FIX else input_team_name


@cache
def get_correct_venue_name(name, city):
    return f"{name}, {city}" if name and city else None


@dataclass(frozen=True)
class FootballCalendarEvent:
    summary: str
    location: str
    start_date: datetime
    end_date: datetime
    competition: str
    description: str

    @staticmethod
    def to_football_calendar_events(api_response: list[dict]):
        return [FootballCalendarEvent.to_football_calendar_event(x) for x in api_response]

    @staticmethod
    def to_football_calendar_event(fixture: dict):
        start_date = get_datetime_from_str(fixture['fixture']['date'])
        competition = get_competition_txt(fixture['league']['name'])
        summary = f"{get_correct_team_name(fixture['teams']['home']['name'])} vs. {get_correct_team_name(fixture['teams']['away']['name'])}"
        venue = get_correct_venue_name(fixture['fixture']['venue']['name'], fixture['fixture']['venue']['city'])
        return FootballCalendarEvent(
            summary=summary,
            location=venue,
            start_date=start_date,
            end_date=get_end_datetime(start_date, 2),
            competition=competition,
            description=f'{competition} - {summary}'
        )

    def to_event(self) -> Event:
        event = Event()
        event.add('summary', self.summary)
        if self.location:
            event.add('location', self.location)
        event.add('dtstart', self.start_date)
        event.add('dtend', self.end_date)
        event.add('competition', self.competition)
        event.add('description', self.description)
        return event


@dataclass()
class FootballCalendar:
    team_name: str
    season: int
    events: List[FootballCalendarEvent]
    cal_file_name: str = field(init=False)
    cal: Calendar | None = field(init=False)
    cal_bytes: bytes | None = field(init=False)
    cal_sha256_str: str | None = field(init=False)

    def __post_init__(self):
        self.team_name = get_correct_team_name(self.team_name)
        self.cal_file_name = f"{self.team_name.replace('.', '').replace(' ', '')}.ics"
        self.cal = None
        self.cal_bytes = None
        self.cal_sha256_str = None

    @staticmethod
    def to_football_calendar(team_name: str, season: int,
                             events: List[FootballCalendarEvent]):
        return FootballCalendar(
            team_name=team_name,
            season=season,
            events=events
        )

    def to_calendar(self) -> Calendar:
        if self.cal is None:
            cal = Calendar()
            # https://en.wikipedia.org/wiki/ICalendar
            cal.add('X-WR-CALNAME', self.team_name)
            cal.add('X-WR-CALDESC', f'All {self.team_name} fixtures for {self.season} season')
            cal.add('X-WR-RELCALID', f'{self.team_name}-{self.season}'.replace(' ', ''))
            cal.add('X-PUBLISHED-TTL', 'PT6H')
            cal.add('URL', f'https://raw.githubusercontent.com/jbaranski/dcunited-ical/refs/heads/main/calendar.ics')
            cal.add('METHOD', 'PUBLISH')
            cal.add('VERSION', '2.0')
            cal.add('PRODID', 'soccercalendar.jeffsoftware.com')
            cal.add('CALSCALE', 'GREGORIAN')
            cal.add('X-MICROSOFT-CALSCALE', 'GREGORIAN')
            for x in self.events:
                cal.add_component(x.to_event())
            self.cal = cal
        return self.cal

    def to_bytes(self) -> bytes:
        if self.cal_bytes is None:
            self.cal_bytes = self.to_calendar().to_ical(sorted=True)
        return self.cal_bytes

    def to_sha256_str(self) -> str:
        if self.cal_sha256_str is None:
            self.cal_sha256_str = sha256(self.to_bytes()).hexdigest()
        return self.cal_sha256_str
