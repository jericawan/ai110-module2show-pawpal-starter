"""PawPal+ system classes (skeleton based on diagrams/uml_draft.mmd)."""

from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, etc.)."""

    name: str
    duration_minutes: int
    priority: int  # 1 = most important
    assigned_to: str = ""
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass


@dataclass
class Pet:
    """A pet and the care it needs."""

    name: str
    breed: str = ""
    gender: str = ""
    age: int = 0
    birthday: Optional[date] = None
    special_needs: list[str] = field(default_factory=list)
    priority: str = ""
    required_tasks: list[Task] = field(default_factory=list)
    time_constraints: dict[str, time] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        pass

    def add_time_constraint(self, task_name: str, at: time) -> None:
        """Require a task to happen at a specific time (e.g. meds at 5 PM)."""
        pass

    def create_impending_task(self, name: str, duration: int, reason: str) -> Task:
        """Create an urgent task (e.g. medicine for a sickness) and add it."""
        pass

    def change_priority(self, new_priority: str) -> None:
        """Update this pet's priority."""
        pass


@dataclass
class Owner:
    """The pet owner and their availability."""

    name: str
    available_minutes: int = 0
    home_start: Optional[time] = None
    home_end: Optional[time] = None
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def update_availability(self, minutes: int) -> None:
        """Change how many minutes the owner has for pet care today."""
        pass

    def update_home_hours(self, start: time, end: time) -> None:
        """Change the time window the owner is home."""
        pass

    def is_home_at(self, t: time) -> bool:
        """Return True if the owner is home at time t."""
        pass

    def check_off_task(self, task: Task) -> None:
        """Mark a task in the task list as done."""
        pass


class Scheduler:
    """Builds a daily plan and checklist for an owner's pets."""

    def __init__(self, owner: Owner):
        self.owner = owner
        self.daily_plan: list[Task] = []
        self.checklist: list[Task] = []
        self.skipped: list[Task] = []

    def create_daily_plan(self) -> list[Task]:
        """Pick and order tasks that fit the owner's time and constraints."""
        pass

    def create_checklist(self) -> list[Task]:
        """Build a checklist from the daily plan."""
        pass

    def add_to_checklist(self, task: Task) -> None:
        """Add an extra task to the checklist."""
        pass

    def explain_plan(self) -> str:
        """Explain why tasks were included or skipped."""
        pass
