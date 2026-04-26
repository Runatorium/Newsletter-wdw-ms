from pydantic import BaseModel


class PeriodCounts(BaseModel):
    """Counts of records created within the last day, week, and month (rolling windows)."""

    last_day: int
    last_week: int
    last_month: int
