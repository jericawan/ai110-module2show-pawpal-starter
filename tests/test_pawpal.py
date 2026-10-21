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


def test_filter_tasks_by_completed(home):
    household, jo, _, biscuit, mochi = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    feed = Task("Feed", 10, 1, pets=[mochi])
    household.add_task(walk)
    household.add_task(feed)
    walk.mark_complete(by=jo, on=DAY)

    scheduler = Scheduler(household)

    assert scheduler.filter_tasks(completed=True, day=DAY) == [walk]
    assert scheduler.filter_tasks(completed=False, day=DAY) == [feed]


def test_filter_tasks_by_pet_name(home):
    household, jo, _, biscuit, mochi = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    feed = Task("Feed", 10, 1, pets=[mochi])
    vet = Task("Vet visit", 60, 1, pets=[biscuit, mochi])
    for task in (walk, feed, vet):
        household.add_task(task)

    scheduler = Scheduler(household)

    assert scheduler.filter_tasks(pet_name="biscuit") == [walk, vet]
    assert scheduler.filter_tasks(pet_name="Rex") == []


def test_filter_tasks_combines_filters(home):
    household, jo, _, biscuit, mochi = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    meds = Task("Meds", 5, 1, pets=[biscuit])
    feed = Task("Feed", 10, 1, pets=[mochi])
    for task in (walk, meds, feed):
        household.add_task(task)
    walk.mark_complete(by=jo, on=DAY)

    scheduler = Scheduler(household)

    assert scheduler.filter_tasks(completed=False, pet_name="Biscuit", day=DAY) == [meds]
    assert scheduler.filter_tasks() == [walk, meds, feed]


def test_completing_daily_task_creates_tomorrows_copy(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit], frequency="daily", due_date=DAY)
    household.add_task(walk, assigned_to=jo)

    next_walk = household.check_off_task(walk, by=jo, on=DAY)

    assert next_walk is not walk
    assert next_walk.due_date == date(2026, 10, 19)
    assert not next_walk.is_done_on(DAY)
    assert next_walk.assigned_to is jo
    assert next_walk in household.tasks and next_walk in biscuit.tasks
    assert walk.is_done_on(DAY)  # the original stays completed


def test_completing_weekly_task_creates_next_weeks_copy(home):
    household, jo, _, _, mochi = home
    bath = Task("Bath", 20, 2, pets=[mochi], frequency="weekly", due_date=DAY)
    household.add_task(bath, assigned_to=jo)

    next_bath = household.check_off_task(bath, by=jo, on=DAY)

    assert next_bath.due_date == date(2026, 10, 25)


def test_one_time_task_does_not_repeat(home):
    household, jo, _, biscuit, _ = home
    vet = Task("Vet visit", 60, 1, pets=[biscuit])
    household.add_task(vet, assigned_to=jo)

    assert household.check_off_task(vet, by=jo, on=DAY) is None
    assert household.tasks == [vet]


def test_checking_off_twice_makes_only_one_copy(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit], frequency="daily", due_date=DAY)
    household.add_task(walk, assigned_to=jo)

    household.check_off_task(walk, by=jo, on=DAY)
    household.check_off_task(walk, by=jo, on=DAY)

    assert len(household.tasks) == 2


def test_plan_only_includes_repeating_tasks_due_that_day(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit], frequency="daily", due_date=DAY)
    household.add_task(walk, assigned_to=jo)
    next_walk = household.check_off_task(walk, by=jo, on=DAY)

    scheduler = Scheduler(household)

    assert scheduler.create_daily_plan(DAY) == []  # today's walk is done, tomorrow's not due
    tomorrow = [item.task for item in scheduler.create_daily_plan(date(2026, 10, 19))]
    assert tomorrow == [next_walk]


def test_invalid_frequency_is_rejected():
    with pytest.raises(ValueError):
        Task("Walk", 30, 1, frequency="hourly")


def test_warns_when_same_pet_is_double_booked(home):
    household, jo, sam, biscuit, _ = home
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), due_time=time(8, 0), assigned_to=jo)
    household.add_task(Task("Bath", 20, 1, pets=[biscuit]), due_time=time(8, 0), assigned_to=sam)
    sam.update_home_hours(time(7, 0), time(22, 0))

    scheduler = Scheduler(household)
    plan = scheduler.create_daily_plan(DAY)

    assert len(plan) == 2  # both stay in the plan; it only warns
    assert len(scheduler.warnings) == 1
    assert "Biscuit" in scheduler.warnings[0]
    assert "Warnings" in scheduler.explain_plan()


def test_no_warning_for_different_pets_and_people(home):
    household, jo, sam, biscuit, mochi = home
    sam.update_home_hours(time(7, 0), time(22, 0))
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), due_time=time(8, 0), assigned_to=jo)
    household.add_task(Task("Feed", 10, 1, pets=[mochi]), due_time=time(8, 0), assigned_to=sam)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert scheduler.warnings == []


def test_back_to_back_tasks_are_not_a_conflict(home):
    household, jo, sam, biscuit, _ = home
    sam.update_home_hours(time(7, 0), time(22, 0))
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), due_time=time(8, 0), assigned_to=jo)
    household.add_task(Task("Bath", 20, 1, pets=[biscuit]), due_time=time(8, 30), assigned_to=sam)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert scheduler.warnings == []


def test_sort_by_time_orders_earliest_first(home):
    household, jo, _, biscuit, mochi = home
    dinner = Task("Dinner", 10, 1, pets=[mochi])
    walk = Task("Walk", 30, 1, pets=[biscuit])
    meds = Task("Meds", 5, 1, pets=[biscuit])
    household.add_task(dinner, due_time=time(18, 0))
    household.add_task(walk, due_time=time(7, 30))
    household.add_task(meds, due_time=time(12, 0))

    assert Scheduler(household).sort_by_time() == [walk, meds, dinner]


def test_sort_by_time_puts_untimed_tasks_last(home):
    household, jo, _, biscuit, _ = home
    play = Task("Play", 20, 2, pets=[biscuit])
    walk = Task("Walk", 30, 1, pets=[biscuit])
    household.add_task(play)
    household.add_task(walk, due_time=time(7, 30))

    assert Scheduler(household).sort_by_time() == [walk, play]


def test_sort_by_time_does_not_change_original_list(home):
    household, jo, _, biscuit, _ = home
    late = Task("Late", 10, 1, pets=[biscuit])
    early = Task("Early", 10, 1, pets=[biscuit])
    household.add_task(late, due_time=time(20, 0))
    household.add_task(early, due_time=time(7, 0))

    Scheduler(household).sort_by_time()

    assert household.tasks == [late, early]


# --- sort_by_time working together with the other features ---


def test_sort_by_time_on_empty_household_returns_empty_list(home):
    household, *_ = home
    assert Scheduler(household).sort_by_time() == []


def test_sort_by_time_puts_midnight_first(home):
    household, jo, _, biscuit, _ = home
    noon = Task("Noon", 10, 1, pets=[biscuit])
    midnight = Task("Midnight", 10, 1, pets=[biscuit])
    household.add_task(noon, due_time=time(12, 0))
    household.add_task(midnight, due_time=time(0, 0))

    assert Scheduler(household).sort_by_time() == [midnight, noon]


def test_sort_by_time_keeps_added_order_for_equal_times(home):
    household, jo, _, biscuit, mochi = home
    first = Task("First", 10, 3, pets=[mochi])
    second = Task("Second", 10, 1, pets=[biscuit])
    household.add_task(first, due_time=time(8, 0))
    household.add_task(second, due_time=time(8, 0))

    # priority is ignored; Python's sort keeps ties in their original order
    assert Scheduler(household).sort_by_time() == [first, second]


def test_sort_by_time_with_pet_filter(home):
    household, jo, _, biscuit, mochi = home
    mochi_dinner = Task("Dinner", 10, 1, pets=[mochi])
    biscuit_walk = Task("Walk", 30, 1, pets=[biscuit])
    mochi_breakfast = Task("Breakfast", 10, 1, pets=[mochi])
    household.add_task(mochi_dinner, due_time=time(18, 0))
    household.add_task(biscuit_walk, due_time=time(7, 0))
    household.add_task(mochi_breakfast, due_time=time(8, 0))

    scheduler = Scheduler(household)
    mochi_tasks = scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi"))

    assert mochi_tasks == [mochi_breakfast, mochi_dinner]


def test_sort_by_time_with_completed_filter_after_check_off(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    meds = Task("Meds", 5, 1, pets=[biscuit])
    dinner = Task("Dinner", 10, 1, pets=[biscuit])
    household.add_task(dinner, due_time=time(18, 0))
    household.add_task(walk, due_time=time(7, 0))
    household.add_task(meds, due_time=time(12, 0))
    household.check_off_task(walk, by=jo, on=DAY)

    scheduler = Scheduler(household)
    still_to_do = scheduler.sort_by_time(scheduler.filter_tasks(completed=False, day=DAY))

    assert still_to_do == [meds, dinner]


def test_sort_by_time_includes_next_occurrence_of_repeating_task(home):
    household, jo, _, biscuit, mochi = home
    walk = Task("Walk", 30, 1, pets=[biscuit], frequency="daily", due_date=DAY)
    feed = Task("Feed", 10, 1, pets=[mochi])
    household.add_task(walk, due_time=time(9, 0), assigned_to=jo)
    household.add_task(feed, due_time=time(8, 0))

    next_walk = household.check_off_task(walk, by=jo, on=DAY)

    # the copy keeps the 9:00 time, so it sorts with the original after Feed
    assert next_walk.due_time == time(9, 0)
    assert Scheduler(household).sort_by_time() == [feed, walk, next_walk]


def test_sort_by_time_reflects_edited_due_time(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    meds = Task("Meds", 5, 1, pets=[biscuit])
    household.add_task(walk, due_time=time(7, 0))
    household.add_task(meds, due_time=time(12, 0))
    scheduler = Scheduler(household)

    household.edit_task(walk, due_time=time(19, 0))

    assert scheduler.sort_by_time() == [meds, walk]


def test_sort_by_time_leaves_out_removed_task(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    meds = Task("Meds", 5, 1, pets=[biscuit])
    household.add_task(walk, due_time=time(7, 0))
    household.add_task(meds, due_time=time(12, 0))

    household.remove_task(walk)

    assert Scheduler(household).sort_by_time() == [meds]


def test_sort_by_time_matches_plan_order_for_fixed_tasks(home):
    household, jo, sam, biscuit, mochi = home
    household.add_task(Task("Dinner", 10, 1, pets=[mochi]), due_time=time(18, 0), assigned_to=sam)
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), due_time=time(7, 0), assigned_to=jo)
    household.add_task(Task("Brush", 15, 3, pets=[biscuit]), due_time=time(20, 0), assigned_to=sam)
    household.add_task(Task("Feed", 10, 2, pets=[mochi]), due_time=time(8, 0), assigned_to=jo)

    scheduler = Scheduler(household)
    plan = scheduler.create_daily_plan(DAY)

    assert [item.task for item in plan] == scheduler.sort_by_time()


def test_sort_by_time_does_not_change_the_plan(home):
    household, jo, _, biscuit, mochi = home
    household.add_task(Task("Play", 20, 2, pets=[biscuit]), assigned_to=jo)
    household.add_task(Task("Feed", 10, 1, pets=[mochi]), due_time=time(8, 0), assigned_to=jo)
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), due_time=time(7, 0), assigned_to=jo)

    scheduler = Scheduler(household)
    before = [(item.task.name, item.start_time) for item in scheduler.create_daily_plan(DAY)]
    scheduler.sort_by_time()
    after = [(item.task.name, item.start_time) for item in scheduler.create_daily_plan(DAY)]

    assert before == after


def test_sort_by_time_shows_double_booked_tasks_side_by_side(home):
    household, jo, sam, biscuit, mochi = home
    sam.update_home_hours(time(7, 0), time(22, 0))
    grooming = Task("Grooming", 20, 2, pets=[biscuit])
    vet_call = Task("Vet call", 15, 1, pets=[biscuit])
    feed = Task("Feed", 10, 1, pets=[mochi])
    household.add_task(grooming, due_time=time(8, 0), assigned_to=jo)
    household.add_task(feed, due_time=time(7, 0), assigned_to=jo)
    household.add_task(vet_call, due_time=time(8, 0), assigned_to=sam)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert scheduler.sort_by_time() == [feed, grooming, vet_call]
    assert len(scheduler.warnings) == 1
    assert "Grooming" in scheduler.warnings[0] and "Vet call" in scheduler.warnings[0]


# --- Edge cases: recurring tasks ---


def test_overdue_daily_task_next_copy_counts_from_completion_day(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit], frequency="daily", due_date=date(2026, 10, 10))
    household.add_task(walk, assigned_to=jo)

    next_walk = household.check_off_task(walk, by=jo, on=DAY)

    # done late on Oct 18, so the next one is due Oct 19, not Oct 11
    assert next_walk.due_date == date(2026, 10, 19)
    assert not next_walk.is_pending_on(DAY)


def test_weekly_task_is_pending_from_due_date_until_done():
    bath = Task("Bath", 20, 2, frequency="weekly", due_date=DAY)

    assert not bath.is_pending_on(date(2026, 10, 17))
    assert bath.is_pending_on(DAY)
    assert bath.is_pending_on(date(2026, 10, 21))  # overdue still shows up


def test_weekly_task_repeats_across_new_year(home):
    household, jo, _, _, mochi = home
    bath = Task("Bath", 20, 2, pets=[mochi], frequency="weekly", due_date=date(2026, 12, 28))
    household.add_task(bath, assigned_to=jo)

    next_bath = household.check_off_task(bath, by=jo, on=date(2026, 12, 28))

    assert next_bath.due_date == date(2027, 1, 4)


def test_next_copy_has_its_own_pets_list(home):
    household, jo, _, biscuit, mochi = home
    walk = Task("Walk", 30, 1, pets=[biscuit], frequency="daily", due_date=DAY)
    household.add_task(walk, assigned_to=jo)

    next_walk = household.check_off_task(walk, by=jo, on=DAY)
    next_walk.pets.append(mochi)

    assert walk.pets == [biscuit]


def test_repeating_task_without_due_date_starts_today():
    walk = Task("Walk", 30, 1, frequency="daily")
    assert walk.due_date == date.today()


def test_not_completed_filter_leaves_out_tomorrows_copy(home):
    household, jo, _, biscuit, mochi = home
    walk = Task("Walk", 30, 1, pets=[biscuit], frequency="daily", due_date=DAY)
    feed = Task("Feed", 10, 1, pets=[mochi])
    household.add_task(walk, assigned_to=jo)
    household.add_task(feed, assigned_to=jo)
    next_walk = household.check_off_task(walk, by=jo, on=DAY)

    scheduler = Scheduler(household)

    assert scheduler.filter_tasks(completed=False, day=DAY) == [feed]  # tomorrow's walk isn't due
    assert next_walk in scheduler.filter_tasks(completed=False, day=date(2026, 10, 19))


# --- Edge cases: home hours ---


def test_tasks_at_the_edges_of_home_hours_fit(home):
    household, jo, _, biscuit, mochi = home  # Jo home 7-9 AM
    household.add_task(Task("Feed", 10, 1, pets=[mochi]), due_time=time(7, 0), assigned_to=jo)
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), due_time=time(8, 30), assigned_to=jo)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert planned_names(scheduler) == ["Feed", "Walk"]  # Walk ends exactly at 9:00


def test_task_ending_one_minute_after_home_hours_is_skipped(home):
    household, jo, _, biscuit, _ = home
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), due_time=time(8, 31), assigned_to=jo)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert skipped_names(scheduler) == ["Walk"]


def test_owner_without_home_hours_can_do_late_task():
    pat = Owner("Pat")  # no home hours = always home
    dog = Pet("Rex")
    household = Household("Pat's")
    household.add_member(pat)
    household.add_pet(dog)
    household.add_task(Task("Late walk", 20, 1, pets=[dog]), due_time=time(22, 0))

    scheduler = Scheduler(household)
    plan = scheduler.create_daily_plan(DAY)

    assert planned_names(scheduler) == ["Late walk"]
    assert plan[0].start_time == time(22, 0)


def test_unassigned_task_goes_to_member_home_for_the_whole_task(home):
    household, jo, sam, biscuit, _ = home  # Jo home until 9:00
    sam.update_home_hours(time(8, 30), time(10, 0))  # Sam has less free time than Jo
    walk = Task("Walk", 20, 1, pets=[biscuit])
    household.add_task(walk, due_time=time(8, 50))  # would run past Jo's 9:00

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert walk.assigned_to is sam
    assert planned_names(scheduler) == ["Walk"]
    assert scheduler.skipped == []


def test_owner_rejects_home_start_after_home_end():
    with pytest.raises(ValueError):
        Owner("Jo", home_start=time(18, 0), home_end=time(9, 0))


# --- Edge cases: slots and conflicts ---


def test_flexible_task_fills_gap_before_fixed_task(home):
    household, jo, _, biscuit, mochi = home
    household.add_task(Task("Meds", 10, 1, pets=[biscuit]), due_time=time(7, 30), assigned_to=jo)
    household.add_task(Task("Play", 30, 2, pets=[mochi]), assigned_to=jo)

    scheduler = Scheduler(household)
    plan = scheduler.create_daily_plan(DAY)

    assert [(item.task.name, item.start_time) for item in plan] == [
        ("Play", time(7, 0)),
        ("Meds", time(7, 30)),
    ]


def test_flexible_task_skipped_when_no_gap_is_long_enough(home):
    household, jo, _, biscuit, mochi = home  # Jo 7-9 AM
    household.add_task(Task("Vet call", 60, 1, pets=[biscuit]), due_time=time(7, 30), assigned_to=jo)
    household.add_task(Task("Bath", 45, 2, pets=[mochi]), assigned_to=jo)  # gaps are only 30 min

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert planned_names(scheduler) == ["Vet call"]
    assert "no free 45-min slot" in scheduler.skipped[0][1]


def test_one_minute_overlap_is_a_conflict(home):
    household, jo, sam, biscuit, _ = home
    sam.update_home_hours(time(7, 0), time(22, 0))
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), due_time=time(8, 0), assigned_to=jo)
    household.add_task(Task("Bath", 20, 1, pets=[biscuit]), due_time=time(8, 29), assigned_to=sam)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert len(scheduler.warnings) == 1


def test_flexible_task_avoids_time_pet_is_busy_with_someone_else(home):
    household, jo, sam, biscuit, _ = home
    sam.update_home_hours(time(7, 0), time(22, 0))
    household.add_task(Task("Vet call", 30, 1, pets=[biscuit]), due_time=time(7, 0), assigned_to=sam)
    household.add_task(Task("Brush", 30, 2, pets=[biscuit]), assigned_to=jo)

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    brush = next(item for item in scheduler.daily_plan if item.task.name == "Brush")
    assert brush.start_time == time(7, 30)  # waits until Biscuit is back from the vet call
    assert scheduler.warnings == []


# --- Edge cases: input checks ---


@pytest.mark.parametrize("minutes", [0, -10])
def test_task_rejects_non_positive_duration(minutes):
    with pytest.raises(ValueError):
        Task("Walk", minutes, 1)


def test_task_rejects_non_positive_duration_when_edited(home):
    household, _, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    household.add_task(walk)

    with pytest.raises(ValueError):
        household.edit_task(walk, duration_minutes=0)
    assert walk.duration_minutes == 30


def test_owner_with_only_start_time_is_home_from_then_on():
    jo = Owner("Jo", home_start=time(9, 0))

    assert not jo.is_home_at(time(8, 0))
    assert jo.is_home_at(time(22, 0))


def test_task_running_past_midnight_is_skipped_without_crashing():
    pat = Owner("Pat")  # home all day, until 23:59
    dog = Pet("Rex")
    household = Household("Pat's")
    household.add_member(pat)
    household.add_pet(dog)
    household.add_task(Task("Night walk", 30, 1, pets=[dog]), due_time=time(23, 45))

    scheduler = Scheduler(household)
    scheduler.create_daily_plan(DAY)

    assert skipped_names(scheduler) == ["Night walk"]


def test_daily_task_done_on_time_is_due_the_next_day(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit], frequency="daily", due_date=DAY)
    household.add_task(walk, assigned_to=jo)

    next_walk = household.check_off_task(walk, by=jo, on=DAY)
    third_walk = household.check_off_task(next_walk, by=jo, on=date(2026, 10, 19))

    assert third_walk.due_date == date(2026, 10, 20)


def test_fixed_tasks_for_the_same_pet_still_warn_instead_of_moving(home):
    household, jo, sam, biscuit, _ = home
    sam.update_home_hours(time(7, 0), time(22, 0))
    household.add_task(Task("Walk", 30, 1, pets=[biscuit]), due_time=time(8, 0), assigned_to=jo)
    household.add_task(Task("Bath", 20, 1, pets=[biscuit]), due_time=time(8, 15), assigned_to=sam)

    scheduler = Scheduler(household)
    plan = scheduler.create_daily_plan(DAY)

    assert [item.start_time for item in plan] == [time(8, 0), time(8, 15)]
    assert len(scheduler.warnings) == 1


# --- find_clashes (warning when a task is added) ---


def test_find_clashes_flags_duplicate_at_same_time(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    walk_again = Task("Walk", 30, 1, pets=[biscuit])
    household.add_task(walk, due_time=time(8, 0), assigned_to=jo)
    household.add_task(walk_again, due_time=time(8, 0), assigned_to=jo)

    assert Scheduler(household).find_clashes(walk_again) == [walk]


def test_find_clashes_flags_partial_overlap_for_same_person(home):
    household, jo, _, biscuit, mochi = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    feed = Task("Feed", 10, 1, pets=[mochi])
    household.add_task(walk, due_time=time(8, 0), assigned_to=jo)
    household.add_task(feed, due_time=time(8, 20), assigned_to=jo)

    assert Scheduler(household).find_clashes(feed) == [walk]


def test_find_clashes_ignores_back_to_back_tasks(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    bath = Task("Bath", 20, 1, pets=[biscuit])
    household.add_task(walk, due_time=time(8, 0), assigned_to=jo)
    household.add_task(bath, due_time=time(8, 30), assigned_to=jo)

    assert Scheduler(household).find_clashes(bath) == []


def test_find_clashes_ignores_different_pet_and_person(home):
    household, jo, sam, biscuit, mochi = home
    sam.update_home_hours(time(7, 0), time(22, 0))
    walk = Task("Walk", 30, 1, pets=[biscuit])
    feed = Task("Feed", 10, 1, pets=[mochi])
    household.add_task(walk, due_time=time(8, 0), assigned_to=jo)
    household.add_task(feed, due_time=time(8, 0), assigned_to=sam)

    assert Scheduler(household).find_clashes(feed) == []


def test_find_clashes_ignores_untimed_tasks(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit])
    play = Task("Play", 30, 1, pets=[biscuit])
    household.add_task(walk, due_time=time(8, 0), assigned_to=jo)
    household.add_task(play, assigned_to=jo)

    scheduler = Scheduler(household)

    assert scheduler.find_clashes(play) == []
    assert scheduler.find_clashes(walk) == []


def test_find_clashes_skips_finished_repeating_task_but_checks_its_next_copy(home):
    household, jo, _, biscuit, _ = home
    walk = Task("Walk", 30, 1, pets=[biscuit], frequency="daily", due_date=DAY)
    household.add_task(walk, due_time=time(8, 0), assigned_to=jo)
    next_walk = household.check_off_task(walk, by=jo, on=DAY)
    walk_again = Task("Walk", 30, 1, pets=[biscuit])
    household.add_task(walk_again, due_time=time(8, 0), assigned_to=jo)

    assert Scheduler(household).find_clashes(walk_again) == [next_walk]
