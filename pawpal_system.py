"""PawPal+ system classes (based on diagrams/uml_draft.mmd)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional

# Planning window used when a person hasn't set home hours ("always home").
DEFAULT_DAY_START = time(8, 0)
DEFAULT_DAY_END = time(21, 0)


def _to_minutes(t: time) -> int:
    """Convert a time to minutes since midnight (e.g. 17:30 -> 1050)."""
    return t.hour * 60 + t.minute


def _to_time(minutes: int) -> time:
    """Convert minutes since midnight back to a time."""
    return time(minutes // 60, minutes % 60)


# eq=False: two tasks with the same values are still different tasks
@dataclass(eq=False)
class Task:
    """A single pet care activity (walk, feeding, meds, etc.)."""

    name: str
    duration_minutes: int
    priority: int  # 1 = most important
    pets: list[Pet] = field(default_factory=list)  # pets this task involves
    due_time: Optional[time] = None  # None = can be done any time
    assigned_to: Optional[Owner] = field(default=None, repr=False)  # who is responsible
    last_completed: Optional[date] = None  # resets naturally each new day
    completed_by: Optional[Owner] = field(default=None, repr=False)  # who last did it

    def mark_complete(self, by: Owner, on: Optional[date] = None) -> None:
        """Record that a household member did this task on the given day (default: today)."""
        self.last_completed = on or date.today()
        self.completed_by = by

    def is_done_on(self, day: Optional[date] = None) -> bool:
        """Return True if this task was completed on the given day (default: today)."""
        return self.last_completed == (day or date.today())

    def pet_priority(self) -> int:
        """Return the most important priority among this task's pets (3 if no pets)."""
        return min((pet.priority for pet in self.pets), default=3)


@dataclass(eq=False)
class Pet:
    """A pet and the care it needs."""

    name: str
    breed: str = ""
    gender: str = ""
    age: int = 0
    birthday: Optional[date] = None
    special_needs: list[str] = field(default_factory=list)
    priority: int = 3  # 1 = most important; breaks ties between equal-priority tasks
    # Tasks this pet requires. Only changed by Household so it stays in sync.
    # repr=False avoids an endless Pet <-> Task loop when printing.
    tasks: list[Task] = field(default_factory=list, repr=False)

    def change_priority(self, new_priority: int) -> None:
        """Update this pet's priority (1 = most important)."""
        if new_priority < 1:
            raise ValueError("Priority must be 1 or higher (1 = most important).")
        self.priority = new_priority

    def pending_tasks(self, day: Optional[date] = None) -> list[Task]:
        """Return this pet's tasks that are not done yet on the given day."""
        return [task for task in self.tasks if not task.is_done_on(day)]


@dataclass(eq=False)
class Owner:
    """One person in the household and their availability.

    home_start/home_end set WHEN they can do tasks. available_minutes caps the
    TOTAL minutes of care they can give that day; None means their whole home window.
    """

    name: str
    home_start: Optional[time] = None
    home_end: Optional[time] = None
    available_minutes: Optional[int] = None
    # Tasks this person is responsible for. Only changed by Household.
    tasks: list[Task] = field(default_factory=list, repr=False)

    def update_availability(self, minutes: Optional[int]) -> None:
        """Change the total care minutes for today (None = whole home window)."""
        if minutes is not None and minutes < 0:
            raise ValueError("Available minutes can't be negative.")
        self.available_minutes = minutes

    def update_home_hours(self, start: time, end: time) -> None:
        """Change the time window this person is home."""
        if start >= end:
            raise ValueError("Home start time must be before end time.")
        self.home_start = start
        self.home_end = end

    def is_home_at(self, t: time) -> bool:
        """Return True if this person is home at time t.

        If home hours are not set, they count as always home.
        """
        if self.home_start is None or self.home_end is None:
            return True
        return self.home_start <= t < self.home_end

    def home_window(self) -> tuple[int, int]:
        """Return (start, end) in minutes since midnight for planning."""
        start = self.home_start or DEFAULT_DAY_START
        end = self.home_end or DEFAULT_DAY_END
        return _to_minutes(start), _to_minutes(end)

    def minutes_for_today(self) -> int:
        """Return the total care minutes this person can give today."""
        start, end = self.home_window()
        window = end - start
        if self.available_minutes is None:
            return window
        return min(self.available_minutes, window)

    def pending_tasks(self, day: Optional[date] = None) -> list[Task]:
        """Return this person's tasks that are not done yet on the given day."""
        return [task for task in self.tasks if not task.is_done_on(day)]


@dataclass(eq=False)
class Household:
    """The people who share the pets, plus the pets and all their tasks."""

    name: str
    members: list[Owner] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_member(self, owner: Owner) -> None:
        """Add a person to the household."""
        if owner not in self.members:
            self.members.append(owner)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet shared by the household."""
        if pet not in self.pets:
            self.pets.append(pet)

    def add_task(
        self,
        task: Task,
        due_time: Optional[time] = None,
        assigned_to: Optional[Owner] = None,
    ) -> None:
        """Add a task to the household and to each pet the task involves.

        If due_time is given, it overwrites task.due_time (e.g. meds at 5 PM).
        If assigned_to is given, that member becomes responsible for it;
        otherwise the Scheduler will pick someone.
        Every pet in task.pets must belong to this household.
        """
        for pet in task.pets:
            if pet not in self.pets:
                raise ValueError(f"{pet.name} is not in the {self.name} household.")
        if due_time is not None:
            task.due_time = due_time
        if task not in self.tasks:
            self.tasks.append(task)
        for pet in task.pets:
            if task not in pet.tasks:
                pet.tasks.append(task)
        if assigned_to is not None:
            self.assign_task(task, assigned_to)

    def assign_task(self, task: Task, owner: Owner) -> None:
        """Make a household member responsible for a task (moves it from anyone else)."""
        if owner not in self.members:
            raise ValueError(f"{owner.name} is not in the {self.name} household.")
        if task not in self.tasks:
            raise ValueError(f"'{task.name}' is not a {self.name} household task.")
        if task.assigned_to is not None and task in task.assigned_to.tasks:
            task.assigned_to.tasks.remove(task)
        task.assigned_to = owner
        owner.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from the household, each pet's list, and its owner's list."""
        if task in self.tasks:
            self.tasks.remove(task)
        for pet in task.pets:
            if task in pet.tasks:
                pet.tasks.remove(task)
        if task.assigned_to is not None and task in task.assigned_to.tasks:
            task.assigned_to.tasks.remove(task)
        task.assigned_to = None

    def edit_task(
        self,
        task: Task,
        name: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        priority: Optional[int] = None,
        due_time: Optional[time] = None,
    ) -> None:
        """Change any of a task's details; arguments left as None stay the same."""
        if task not in self.tasks:
            raise ValueError(f"'{task.name}' is not a {self.name} household task.")
        if name is not None:
            task.name = name
        if duration_minutes is not None:
            task.duration_minutes = duration_minutes
        if priority is not None:
            task.priority = priority
        if due_time is not None:
            task.due_time = due_time

    def unassigned_tasks(self) -> list[Task]:
        """Return household tasks nobody is responsible for yet."""
        return [task for task in self.tasks if task.assigned_to is None]

    def check_off_task(self, task: Task, by: Owner) -> None:
        """Mark a task done for today; any household member can do this.

        Refuses if `by` is not a member or the task isn't in this household.
        """
        if by not in self.members:
            raise ValueError(f"{by.name} is not in the {self.name} household.")
        if task not in self.tasks:
            raise ValueError(f"'{task.name}' is not a {self.name} household task.")
        task.mark_complete(by)


@dataclass
class ScheduledTask:
    """A task placed at a specific start time, for one member."""

    task: Task
    start_time: time
    assigned_to: Optional[Owner] = None  # anyone in the household can still check it off
    reason: str = ""

    def end_time(self) -> time:
        """Return when this task finishes."""
        return _to_time(_to_minutes(self.start_time) + self.task.duration_minutes)


class Scheduler:
    """Organizes a household's tasks into a daily plan, reading tasks from each owner."""

    def __init__(self, household: Household):
        self.household = household
        self.daily_plan: list[ScheduledTask] = []
        self.skipped: list[tuple[Task, str]] = []  # (task, why it was skipped)

    @staticmethod
    def _sort_key(task: Task) -> tuple:
        """Fixed-time tasks first (earliest first), then task priority, then pet priority."""
        has_no_due_time = task.due_time is None
        due = _to_minutes(task.due_time) if task.due_time else 0
        return (has_no_due_time, due, task.priority, task.pet_priority())

    def assign_unassigned_tasks(self, day: Optional[date] = None) -> None:
        """Give each task nobody owns to the member best able to do it.

        For fixed-time tasks, only members home at that time are considered.
        Among those, the member with the most free minutes left gets it.
        """
        load = {
            owner: sum(t.duration_minutes for t in owner.pending_tasks(day))
            for owner in self.household.members
        }
        for task in sorted(self.household.unassigned_tasks(), key=self._sort_key):
            if task.is_done_on(day):
                continue
            candidates = [
                owner
                for owner in self.household.members
                if task.due_time is None or owner.is_home_at(task.due_time)
            ]
            if not candidates:
                continue  # stays unassigned; create_daily_plan reports it
            best = max(candidates, key=lambda o: o.minutes_for_today() - load[o])
            self.household.assign_task(task, best)
            load[best] += task.duration_minutes

    def _plan_for_owner(self, owner: Owner, day: Optional[date]) -> None:
        """Place one owner's pending tasks into free time slots in their home window."""
        window_start, window_end = owner.home_window()
        minutes_left = owner.minutes_for_today()
        busy: list[tuple[int, int]] = []  # (start, end) minutes already booked

        def is_free(start: int, end: int) -> bool:
            return all(end <= b_start or start >= b_end for b_start, b_end in busy)

        for task in sorted(owner.pending_tasks(day), key=self._sort_key):
            if task.duration_minutes > minutes_left:
                self.skipped.append(
                    (task, f"{owner.name} only had {minutes_left} min left today")
                )
                continue

            if task.due_time is not None:
                start = _to_minutes(task.due_time)
                end = start + task.duration_minutes
                if start < window_start or end > window_end:
                    self.skipped.append(
                        (task, f"{owner.name} isn't home at {task.due_time:%H:%M}")
                    )
                    continue
                if not is_free(start, end):
                    self.skipped.append(
                        (task, f"conflicts with another fixed task at {task.due_time:%H:%M}")
                    )
                    continue
                reason = f"must be done at {task.due_time:%H:%M}"
            else:
                start = window_start
                while start + task.duration_minutes <= window_end and not is_free(
                    start, start + task.duration_minutes
                ):
                    start += 5  # try the next 5-minute slot
                end = start + task.duration_minutes
                if end > window_end:
                    self.skipped.append(
                        (task, f"no free {task.duration_minutes}-min slot in {owner.name}'s day")
                    )
                    continue
                reason = f"priority {task.priority}, earliest free slot"

            busy.append((start, end))
            minutes_left -= task.duration_minutes
            self.daily_plan.append(ScheduledTask(task, _to_time(start), owner, reason))

    def create_daily_plan(self, day: Optional[date] = None) -> list[ScheduledTask]:
        """Pick, order, and time tasks, reading each member's own task list.

        Clears daily_plan and skipped first so running it twice doesn't repeat tasks.
        Fixed-time tasks go first, then the rest by task priority, then pet priority.
        """
        self.daily_plan = []
        self.skipped = []
        self.assign_unassigned_tasks(day)

        for task in self.household.unassigned_tasks():
            if not task.is_done_on(day):
                self.skipped.append((task, "nobody is home at that time"))

        for owner in self.household.members:
            self._plan_for_owner(owner, day)

        self.daily_plan.sort(key=lambda item: _to_minutes(item.start_time))
        return self.daily_plan

    def create_checklist(self, day: Optional[date] = None) -> list[tuple[str, bool]]:
        """Return (task name, done on that day?) for each task in the daily plan."""
        return [(item.task.name, item.task.is_done_on(day)) for item in self.daily_plan]

    def add_to_checklist(
        self, task: Task, due_time: Optional[time] = None, assigned_to: Optional[Owner] = None
    ) -> None:
        """Add a task through the household, then rebuild the plan so time limits still apply."""
        self.household.add_task(task, due_time=due_time, assigned_to=assigned_to)
        self.create_daily_plan()

    def explain_plan(self) -> str:
        """Explain why tasks were included, who they went to, or why they were skipped."""
        if not self.daily_plan and not self.skipped:
            return "No tasks to plan. Run create_daily_plan() after adding tasks."

        lines = [f"Daily plan for the {self.household.name} household:"]
        for item in self.daily_plan:
            pets = ", ".join(pet.name for pet in item.task.pets) or "no pet"
            who = item.assigned_to.name if item.assigned_to else "anyone"
            lines.append(
                f"  {item.start_time:%H:%M}-{item.end_time():%H:%M}  {item.task.name} "
                f"({pets}) -> {who}  [{item.reason}]"
            )
        if self.skipped:
            lines.append("Skipped:")
            for task, why in self.skipped:
                lines.append(f"  {task.name}: {why}")
        return "\n".join(lines)
