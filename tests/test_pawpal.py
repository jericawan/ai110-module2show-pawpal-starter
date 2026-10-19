"""Tests for the most important PawPal+ scheduling behaviors."""

from datetime import date, time

import pytest

from pawpal_system import Household, Owner, Pet, Scheduler, Task

DAY = date(2026, 10, 18)  # fixed day so tests don't depend on today's date


@pytest.fixture
def home():
    """A household with two members and two pets."""
    jo = Owner("Jo", home_start=time(7, 0), home_end=time(9, 0))
    sam = Owner("Sam", home_start=time(17, 0), home_end=time(22, 0))
    biscuit = Pet("Biscuit", breed="Golden Retriever", priority=1)
    mochi = Pet("Mochi", breed="Tabby Cat")

    household = Household("Wan")
    for member in (jo, sam):
        household.add_member(member)
    for pet in (biscuit, mochi):
        household.add_pet(pet)

    return household, jo, sam, biscuit, mochi


def planned_names(scheduler):
    return [item.task.name for item in scheduler.daily_plan]


def skipped_names(scheduler):
    return [task.name for task, _ in scheduler.skipped]


# --- Task ---------------------------------------------------------------


def test_mark_complete_records_day_and_person():
    jo = Owner("Jo")
    task = Task("Walk", 30, 1)

    task.mark_complete(by=jo, on=DAY)

    assert task.is_done_on(DAY)
    assert task.completed_by is jo


def test_mark_complete_changes_task_to_done():
    task = Task("Walk", 30, 1)
    assert not task.is_done_on(DAY)

    task.mark_complete(by=Owner("Jo"), on=DAY)

    assert task.is_done_on(DAY)


def test_completion_resets_on_a_new_day():
    task = Task("Walk", 30, 1)
    task.mark_complete(by=Owner("Jo"), on=DAY)

    assert not task.is_done_on(date(2026, 10, 19))


def test_tasks_with_same_values_are_different_tasks():
    assert Task("Walk", 30, 1) != Task("Walk", 30, 1)


# --- Pet ----------------------------------------------------------------


def test_change_priority_rejects_values_below_one():
    pet = Pet("Biscuit")
    with pytest.raises(ValueError):
        pet.change_priority(0)


# --- Owner --------------------------------------------------------------


def test_minutes_for_today_defaults_to_home_window():
    jo = Owner("Jo", home_start=time(7, 0), home_end=time(9, 0))
    assert jo.minutes_for_today() == 120


def test_available_minutes_caps_home_window():
    jo = Owner("Jo", home_start=time(7, 0), home_end=time(9, 0), available_minutes=60)
    assert jo.minutes_for_today() == 60


def test_owner_without_home_hours_is_always_home():
    assert Owner("Jo").is_home_at(time(3, 0))


def test_update_home_hours_rejects_start_after_end():
    jo = Owner("Jo")
    with pytest.raises(ValueError):
        jo.update_home_hours(time(18, 0), time(9, 0))


# --- Household ----------------------------------------------------------


def test_add_task_links_household_pet_and_owner(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit])

    household.add_task(walk, assigned_to=jo)

    assert walk in household.tasks
    assert walk in biscuit.tasks
    assert walk in jo.tasks
    assert walk.assigned_to is jo


def test_adding_task_increases_pet_task_count(home):
    household, _, _, biscuit, _ = home
    assert len(biscuit.tasks) == 0

    household.add_task(Task("Walk", 30, 1, pets=[biscuit]))

    assert len(biscuit.tasks) == 1


def test_add_task_due_time_overwrites_task_due_time(home):
    household, _, _, biscuit, _ = home
    meds = Task("Meds", 5, 1, pets=[biscuit], due_time=time(9, 0))

    household.add_task(meds, due_time=time(17, 0))

    assert meds.due_time == time(17, 0)


def test_add_task_rejects_pet_outside_household(home):
    household = home[0]
    stranger_pet = Pet("Rex")
    with pytest.raises(ValueError):
        household.add_task(Task("Walk", 30, 1, pets=[stranger_pet]))


def test_remove_task_removes_it_everywhere(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    household.add_task(walk, assigned_to=jo)

    household.remove_task(walk)

    assert walk not in household.tasks
    assert walk not in biscuit.tasks
    assert walk not in jo.tasks


def test_reassigning_moves_task_between_owners(home):
    household, jo, sam, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    household.add_task(walk, assigned_to=jo)

    household.assign_task(walk, sam)

    assert walk not in jo.tasks
    assert walk in sam.tasks


def test_any_member_can_check_off_a_shared_task(home):
    household, jo, sam, biscuit, _ = home
    meds = Task("Meds", 5, 1, pets=[biscuit])
    household.add_task(meds, assigned_to=sam)

    household.check_off_task(meds, by=jo)

    assert meds.is_done_on()
    assert meds.completed_by is jo


def test_non_member_cannot_check_off_task(home):
    household, _, _, biscuit, _ = home
    meds = Task("Meds", 5, 1, pets=[biscuit])
    household.add_task(meds)

    with pytest.raises(ValueError):
        household.check_off_task(meds, by=Owner("Stranger"))


# --- Scheduler ----------------------------------------------------------


def test_fixed_time_task_is_placed_at_its_due_time(home):
    household, _, sam, biscuit, _ = home
    household.add_task(Task("Meds", 5, 1, pets=[biscuit]), due_time=time(17, 0))

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert len(scheduler.daily_plan) == 1
    item = scheduler.daily_plan[0]
    assert item.start_time == time(17, 0)
    assert item.assigned_to is sam  # only Sam is home at 5 PM


def test_higher_priority_tasks_come_first(home):
    household, jo, _, biscuit, mochi = home
    household.add_task(Task("Brush", 15, 3, pets=[mochi]), assigned_to=jo)
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), assigned_to=jo)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert planned_names(scheduler) == ["Walk", "Brush"]


def test_pet_priority_breaks_ties(home):
    household, jo, _, biscuit, mochi = home  # Biscuit priority 1, Mochi priority 3
    household.add_task(Task("Feed Mochi", 10, 1, pets=[mochi]), assigned_to=jo)
    household.add_task(Task("Feed Biscuit", 10, 1, pets=[biscuit]), assigned_to=jo)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert planned_names(scheduler) == ["Feed Biscuit", "Feed Mochi"]


def test_tasks_do_not_overlap(home):
    household, jo, _, biscuit, mochi = home
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), assigned_to=jo)
    household.add_task(Task("Feed", 10, 1, pets=[mochi]), assigned_to=jo)

    scheduler = Scheduler(household)
    plan = scheduler.create_daily_plan(DAY)

    first, second = plan
    assert first.end_time() <= second.start_time


def test_task_skipped_when_owner_runs_out_of_minutes(home):
    household, jo, _, biscuit, _ = home  # Jo has 120 min
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), assigned_to=jo)
    household.add_task(Task("Long hike", 120, 2, pets=[biscuit]), assigned_to=jo)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert planned_names(scheduler) == ["Walk"]
    assert skipped_names(scheduler) == ["Long hike"]


def test_task_skipped_when_nobody_is_home(home):
    household, _, _, biscuit, _ = home  # Jo 7-9 AM, Sam 5-10 PM
    household.add_task(Task("Vet call", 10, 2, pets=[biscuit]), due_time=time(12, 0))

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert scheduler.daily_plan == []
    assert skipped_names(scheduler) == ["Vet call"]


def test_conflicting_fixed_tasks_skip_the_second(home):
    household, _, sam, biscuit, mochi = home
    household.add_task(Task("Meds", 10, 1, pets=[biscuit]), due_time=time(17, 0), assigned_to=sam)
    household.add_task(Task("Feed", 10, 2, pets=[mochi]), due_time=time(17, 5), assigned_to=sam)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert planned_names(scheduler) == ["Meds"]
    assert skipped_names(scheduler) == ["Feed"]


def test_unassigned_task_goes_to_member_with_more_free_time(home):
    household, jo, sam, biscuit, _ = home  # Jo 120 min, Sam 300 min
    walk = Task("Walk", 30, 1, pets=[biscuit])
    household.add_task(walk)

    Scheduler(household).create_daily_plan(DAY)

    assert walk.assigned_to is sam


def test_completed_tasks_are_left_out_of_plan(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    household.add_task(walk, assigned_to=jo)
    walk.mark_complete(by=jo, on=DAY)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert scheduler.daily_plan == []


def test_running_plan_twice_does_not_repeat_tasks(home):
    household, jo, _, biscuit, _ = home
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), assigned_to=jo)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)
    scheduler.create_daily_plan(DAY)

    assert planned_names(scheduler) == ["Walk"]


def test_checklist_shows_done_status(home):
    household, jo, _, biscuit, mochi = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    feed = Task("Feed", 10, 2, pets=[mochi])
    household.add_task(walk, assigned_to=jo)
    household.add_task(feed, assigned_to=jo)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)
    walk.mark_complete(by=jo, on=DAY)

    assert scheduler.create_checklist(DAY) == [("Walk", True), ("Feed", False)]


def test_explain_plan_mentions_planned_and_skipped(home):
    household, jo, _, biscuit, _ = home
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), assigned_to=jo)
    household.add_task(Task("Vet call", 10, 2), due_time=time(12, 0))

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)
    explanation = scheduler.explain_plan()

    assert "Walk" in explanation
    assert "Skipped" in explanation
    assert "nobody is home" in explanation
