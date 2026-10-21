"""PawPal+ system classes (based on diagrams/uml_draft.mmd)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
from typing import Optional

# Planning window used when a person hasn't set home hours ("always home").
# Ends at 23:59, not midnight, since time(24, 0) isn't a valid time.
DEFAULT_DAY_START = time(0, 0)
DEFAULT_DAY_END = time(23, 59)

# How far ahead the next copy of a repeating task is due.
REPEAT_INTERVALS = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


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
    frequency: Optional[str] = None  # "daily", "weekly", or None for a one-time task
    due_date: Optional[date] = None  # None = undated; repeating tasks default to today

    def __post_init__(self) -> None:
        """Check duration and frequency, and give repeating tasks a due date to count from."""
        if self.duration_minutes <= 0:
            raise ValueError("Duration must be at least 1 minute.")
        if self.frequency is not None and self.frequency not in REPEAT_INTERVALS:
            raise ValueError(f"Frequency must be one of {list(REPEAT_INTERVALS)} or None.")
        if self.frequency is not None and self.due_date is None:
            self.due_date = date.today()

    def mark_complete(self, by: Owner, on: Optional[date] = None) -> None:
        """Record that a household member did this task on the given day (default: today)."""
        self.last_completed = on or date.today()
        self.completed_by = by

    def is_done_on(self, day: Optional[date] = None) -> bool:
        """Return True if this task was completed on the given day (default: today)."""
        return self.last_completed == (day or date.today())

    def is_pending_on(self, day: Optional[date] = None) -> bool:
        """Return True if this task still needs doing on the given day (default: today).

        How it works:
            1. Undated tasks reset each day: pending unless completed on `day`.
            2. Dated tasks (e.g. repeating ones) are pending from their due date
               onward, overdue ones included, until they are completed once.

        Args:
            day: The day to check. Defaults to today.

        Returns:
            True if the task should appear in that day's plan.
        """
        day = day or date.today()
        if self.due_date is None:
            return not self.is_done_on(day)
        return self.last_completed is None and self.due_date <= day

    def next_occurrence(self) -> Optional[Task]:
        """Return a fresh, not-yet-done copy due one interval later (None if one-time).

        How it works:
            1. One-time tasks (frequency None) don't repeat, so return None.
            2. Count from the due date, or from the day it was done if that's
               later, so a task done late doesn't leave an overdue copy behind.
            3. Copy the task, moving that day forward by one day ("daily") or
               seven days ("weekly") using REPEAT_INTERVALS.
            4. Clear the completion record so the copy starts out not done.

        The copy has no owner yet; Household.check_off_task adds and assigns it.

        Returns:
            The next occurrence as a new Task, or None for a one-time task.
        """
        if self.frequency is None:
            return None
        counted_from = max(self.due_date, self.last_completed or self.due_date)
        return replace(
            self,
            pets=list(self.pets),
            due_date=counted_from + REPEAT_INTERVALS[self.frequency],
            assigned_to=None,
            last_completed=None,
            completed_by=None,
        )

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
        return [task for task in self.tasks if task.is_pending_on(day)]


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

    def __post_init__(self) -> None:
        """Check that home hours, if both are set, start before they end."""
        if self.home_start is not None and self.home_end is not None:
            self._check_home_hours(self.home_start, self.home_end)

    @staticmethod
    def _check_home_hours(start: time, end: time) -> None:
        """Raise ValueError if start isn't before end."""
        if start >= end:
            raise ValueError("Home start time must be before end time.")

    def update_availability(self, minutes: Optional[int]) -> None:
        """Change the total care minutes for today (None = whole home window)."""
        if minutes is not None and minutes < 0:
            raise ValueError("Available minutes can't be negative.")
        self.available_minutes = minutes

    def update_home_hours(self, start: time, end: time) -> None:
        """Change the time window this person is home."""
        self._check_home_hours(start, end)
        self.home_start = start
        self.home_end = end

    def is_home_at(self, t: time) -> bool:
        """Return True if this person is home at time t.

        If home hours are not set, they count as always home.
        """
        start, end = self.home_window()
        return start <= _to_minutes(t) < end

    def can_fit(self, start: time, duration_minutes: int) -> bool:
        """Return True if a task starting at `start` ends before this person leaves."""
        window_start, window_end = self.home_window()
        begin = _to_minutes(start)
        return window_start <= begin and begin + duration_minutes <= window_end

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
        return [task for task in self.tasks if task.is_pending_on(day)]


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
            if duration_minutes <= 0:
                raise ValueError("Duration must be at least 1 minute.")
            task.duration_minutes = duration_minutes
        if priority is not None:
            task.priority = priority
        if due_time is not None:
            task.due_time = due_time

    def unassigned_tasks(self) -> list[Task]:
        """Return household tasks nobody is responsible for yet."""
        return [task for task in self.tasks if task.assigned_to is None]

    def check_off_task(
        self, task: Task, by: Owner, on: Optional[date] = None
    ) -> Optional[Task]:
        """Mark a task done (default: today); any household member can do this.

        How it works:
            1. Check that `by` is a member and the task belongs to this household.
            2. Record the completion on the task.
            3. If the task was already done, stop, so checking off twice doesn't
               create a second copy.
            4. For a daily or weekly task, add its next occurrence to the
               household, kept with the same person.

        Args:
            task: The household task to mark done.
            by: The member who did it.
            on: The day it was done. Defaults to today.

        Returns:
            The newly added next occurrence, or None if the task doesn't repeat.

        Raises:
            ValueError: If `by` is not a member or the task isn't in this household.
        """
        if by not in self.members:
            raise ValueError(f"{by.name} is not in the {self.name} household.")
        if task not in self.tasks:
            raise ValueError(f"'{task.name}' is not a {self.name} household task.")
        already_done = task.due_date is not None and task.last_completed is not None
        task.mark_complete(by, on)
        if already_done:
            return None  # checking off twice shouldn't create a second copy
        next_task = task.next_occurrence()
        if next_task is not None:
            self.add_task(next_task, assigned_to=task.assigned_to)
        return next_task


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
        """Start with an empty plan and skipped list for the given household."""
        self.household = household
        self.daily_plan: list[ScheduledTask] = []
        self.skipped: list[tuple[Task, str]] = []  # (task, why it was skipped)
        self.warnings: list[str] = []  # overlaps found in the plan; nothing is removed
        # Booked (start, end) minutes while planning, per member and per pet
        self._owner_busy: dict[Owner, list[tuple[int, int]]] = {}
        self._pet_busy: dict[Pet, list[tuple[int, int]]] = {}
        self._minutes_left: dict[Owner, int] = {}

    @staticmethod
    def _sort_key(task: Task) -> tuple:
        """Return the sort key that orders tasks for planning.

        Python compares tuples item by item, so tasks are ordered by:
            1. Fixed-time tasks before flexible ones (False sorts before True).
            2. Earlier due time first.
            3. Task priority (1 = most important).
            4. Pet priority, as a final tie-breaker.

        Args:
            task: The task to build a key for.

        Returns:
            A tuple (has_no_due_time, due_minutes, task_priority, pet_priority).
        """
        has_no_due_time = task.due_time is None
        due = _to_minutes(task.due_time) if task.due_time else 0
        return (has_no_due_time, due, task.priority, task.pet_priority())

    def sort_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks in clock order, earliest due time first.

        How it works:
            1. Use the given tasks, or every household task if none are given.
            2. Sort with a lambda key of (has no due time, "HH:MM" text).
               Zero-padded "HH:MM" text sorts in the same order as the times.
            3. Tasks with no due time sort to the end, since True sorts after False.

        Unlike _sort_key, this ignores priority; it's for showing a timeline.

        Args:
            tasks: The tasks to sort. Defaults to all household tasks.

        Returns:
            A new sorted list; the original list is not changed.
        """
        if tasks is None:
            tasks = self.household.tasks
        return sorted(
            tasks,
            key=lambda task: (
                task.due_time is None,
                task.due_time.strftime("%H:%M") if task.due_time else "",
            ),
        )

    def assign_unassigned_tasks(self, day: Optional[date] = None) -> None:
        """Give each task nobody owns to the member best able to do it.

        How it works (a greedy choice, one task at a time):
            1. Total up how many minutes each member is already booked for.
            2. Go through unassigned tasks in planning order (see _sort_key).
            3. For a fixed-time task, keep only members home for the whole task.
            4. Give the task to the candidate with the most free minutes left,
               then add its duration to that member's total.

        Tasks with no candidate stay unassigned; create_daily_plan reports them.

        Args:
            day: The day being planned. Defaults to today.
        """
        load = {
            owner: sum(t.duration_minutes for t in owner.pending_tasks(day))
            for owner in self.household.members
        }
        for task in sorted(self.household.unassigned_tasks(), key=self._sort_key):
            if not task.is_pending_on(day):
                continue
            candidates = [
                owner
                for owner in self.household.members
                if task.due_time is None or owner.can_fit(task.due_time, task.duration_minutes)
            ]
            if not candidates:
                continue  # stays unassigned; create_daily_plan reports it
            best = max(candidates, key=lambda o: o.minutes_for_today() - load[o])
            self.household.assign_task(task, best)
            load[best] += task.duration_minutes

    @staticmethod
    def _overlaps(slots: list[tuple[int, int]], start: int, end: int) -> bool:
        """Return True if start-end overlaps any (start, end) slot in slots."""
        return any(start < b_end and end > b_start for b_start, b_end in slots)

    def _plan_for_owner(self, owner: Owner, day: Optional[date], fixed: bool) -> None:
        """Place one owner's fixed-time or flexible pending tasks into their home window.

        How it works:
            1. Go through the owner's pending tasks in planning order (see _sort_key),
               keeping only fixed-time tasks (fixed=True) or flexible ones (fixed=False).
            2. Skip a task if it's longer than the owner's remaining minutes today.
            3. Fixed-time task: book it at its due time, unless that's outside
               the owner's home hours or overlaps the owner's other bookings.
               A clash with a pet's booking is allowed; detect_conflicts warns.
            4. Flexible task: step through the home window 5 minutes at a time
               and book the first slot where the owner and every pet are free.
            5. Each booked task is added to daily_plan; each skipped one is
               added to skipped with the reason.

        Args:
            owner: The member whose tasks are being placed.
            day: The day being planned.
            fixed: True to place fixed-time tasks, False for flexible ones.
        """
        window_start, window_end = owner.home_window()
        busy = self._owner_busy[owner]

        def is_free(task: Task, start: int, end: int) -> bool:
            """Return True if the owner and all of the task's pets are free start-end."""
            if self._overlaps(busy, start, end):
                return False
            return not any(
                self._overlaps(self._pet_busy.get(pet, []), start, end) for pet in task.pets
            )

        for task in sorted(owner.pending_tasks(day), key=self._sort_key):
            if (task.due_time is not None) != fixed:
                continue
            minutes_left = self._minutes_left[owner]
            if task.duration_minutes > minutes_left:
                self.skipped.append(
                    (task, f"{owner.name} only had {minutes_left} min left today")
                )
                continue

            if fixed:
                start = _to_minutes(task.due_time)
                end = start + task.duration_minutes
                if not owner.can_fit(task.due_time, task.duration_minutes):
                    self.skipped.append(
                        (task, f"{owner.name} isn't home at {task.due_time:%H:%M}")
                    )
                    continue
                if self._overlaps(busy, start, end):
                    self.skipped.append(
                        (task, f"conflicts with another fixed task at {task.due_time:%H:%M}")
                    )
                    continue
                reason = f"must be done at {task.due_time:%H:%M}"
            else:
                start = window_start
                while start + task.duration_minutes <= window_end and not is_free(
                    task, start, start + task.duration_minutes
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
            for pet in task.pets:
                self._pet_busy.setdefault(pet, []).append((start, end))
            self._minutes_left[owner] -= task.duration_minutes
            self.daily_plan.append(ScheduledTask(task, _to_time(start), owner, reason))

    def create_daily_plan(self, day: Optional[date] = None) -> list[ScheduledTask]:
        """Pick, order, and time tasks, reading each member's own task list.

        How it works:
            1. Clear daily_plan and skipped, so running it twice doesn't repeat tasks.
            2. Give unassigned tasks to a member (assign_unassigned_tasks).
            3. Report any task still unassigned as skipped.
            4. Place every member's fixed-time tasks, then everyone's flexible
               tasks (_plan_for_owner), so flexible tasks can work around a
               pet's fixed bookings with any member.
            5. Sort the plan by start time and check it for clashes
               (detect_conflicts), saving them in warnings.

        Args:
            day: The day to plan. Defaults to today.

        Returns:
            The scheduled tasks, earliest first. Also saved as daily_plan.
        """
        self.daily_plan = []
        self.skipped = []
        self.assign_unassigned_tasks(day)

        for task in self.household.unassigned_tasks():
            if task.is_pending_on(day):
                self.skipped.append((task, "nobody is home at that time"))

        members = self.household.members
        self._owner_busy = {owner: [] for owner in members}
        self._pet_busy = {}
        self._minutes_left = {owner: owner.minutes_for_today() for owner in members}
        for fixed in (True, False):
            for owner in members:
                self._plan_for_owner(owner, day, fixed)

        self.daily_plan.sort(key=lambda item: _to_minutes(item.start_time))
        self.warnings = self.detect_conflicts()
        return self.daily_plan

    def detect_conflicts(self) -> list[str]:
        """Return a warning for each pair of planned tasks that clash.

        Two tasks clash when their times overlap and they share a pet or a
        person. Tasks that only touch (one ends as the other starts) don't clash.

        How it works:
            1. Compare every pair of tasks in daily_plan once.
            2. Skip the pair if their time ranges don't overlap.
            3. Collect any pets in both tasks, plus the person if both are
               assigned to the same one.
            4. If anything is shared, add a warning naming it.

        This only reports; it never changes the plan or raises an error.

        Returns:
            One message per clashing pair, e.g. "Biscuit double-booked: ...".
            An empty list means no clashes.
        """
        warnings = []
        for i, first in enumerate(self.daily_plan):
            first_start = _to_minutes(first.start_time)
            first_end = first_start + first.task.duration_minutes
            for second in self.daily_plan[i + 1:]:
                second_start = _to_minutes(second.start_time)
                second_end = second_start + second.task.duration_minutes
                if second_start >= first_end or first_start >= second_end:
                    continue  # no time overlap

                clashes = [pet.name for pet in first.task.pets if pet in second.task.pets]
                if first.assigned_to is not None and first.assigned_to is second.assigned_to:
                    clashes.append(first.assigned_to.name)
                if clashes:
                    warnings.append(
                        f"{' and '.join(clashes)} double-booked: '{first.task.name}' at "
                        f"{first.start_time:%H:%M} overlaps '{second.task.name}' at "
                        f"{second.start_time:%H:%M}"
                    )
        return warnings

    def find_clashes(self, task: Task) -> list[Task]:
        """Return the other household tasks that overlap this task's time slot.

        How it works:
            1. Untimed tasks can move, so they never clash; return [].
            2. Skip the task itself, untimed tasks, and dated tasks already done
               (they won't come back; a repeating task's next copy is checked instead).
            3. Keep tasks whose time ranges overlap and that share a pet or
               the same assigned person. Back-to-back tasks don't overlap.

        Unlike detect_conflicts, this works on the task list, so it can warn
        as soon as a task is added, before any plan is built.

        Args:
            task: The task to check, usually one just added.

        Returns:
            The clashing tasks, in the order they were added.
        """
        if task.due_time is None:
            return []
        start = _to_minutes(task.due_time)
        end = start + task.duration_minutes
        clashes = []
        for other in self.household.tasks:
            if other is task or other.due_time is None:
                continue
            if other.due_date is not None and other.last_completed is not None:
                continue
            other_start = _to_minutes(other.due_time)
            if not (start < other_start + other.duration_minutes and end > other_start):
                continue
            shares_pet = any(pet in other.pets for pet in task.pets)
            same_person = task.assigned_to is not None and task.assigned_to is other.assigned_to
            if shares_pet or same_person:
                clashes.append(other)
        return clashes

    def create_checklist(self, day: Optional[date] = None) -> list[tuple[str, bool]]:
        """Return (task name, done on that day?) for each task in the daily plan."""
        return [(item.task.name, item.task.is_done_on(day)) for item in self.daily_plan]

    def filter_tasks(
        self,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
        day: Optional[date] = None,
    ) -> list[Task]:
        """Return household tasks matching the given filters; None means don't filter on it.

        How it works:
            1. Start with every household task.
            2. If `completed` is True, keep tasks done on `day`; if False, keep
               tasks still to do that day (not done and already due).
            3. If `pet_name` is given, keep tasks involving a pet with that name.
            Filters combine, so both together narrow the list further.

        Args:
            completed: True = only tasks done on `day`; False = only tasks still
                to do on `day` (a repeating task's future copy is left out).
            pet_name: Only tasks involving this pet (case-insensitive).
            day: The day to check completion for. Defaults to today.

        Returns:
            The matching tasks, in the order they were added.
        """
        tasks = self.household.tasks
        if completed is True:
            tasks = [task for task in tasks if task.is_done_on(day)]
        elif completed is False:
            tasks = [task for task in tasks if task.is_pending_on(day)]
        if pet_name is not None:
            wanted = pet_name.strip().lower()
            tasks = [
                task for task in tasks
                if any(pet.name.lower() == wanted for pet in task.pets)
            ]
        return tasks

    def add_to_checklist(
        self, task: Task, due_time: Optional[time] = None, assigned_to: Optional[Owner] = None
    ) -> None:
        """Add a task through the household, then rebuild the plan so time limits still apply."""
        self.household.add_task(task, due_time=due_time, assigned_to=assigned_to)
        self.create_daily_plan()

    def explain_plan(self) -> str:
        """Explain why tasks were included, who they went to, or why they were skipped."""
        if not self.daily_plan and not self.skipped and not self.warnings:
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
        if self.warnings:
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  {warning}")
        return "\n".join(lines)
