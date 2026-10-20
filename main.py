"""Demo: build a household with two pets and print today's schedule."""

from datetime import time

from pawpal_system import Household, Owner, Pet, Scheduler, Task


def main() -> None:
    """Build a two-person household, plan today, and print the schedule.

    Includes two tasks for Biscuit at 10:00 with different people, so the
    scheduler's double-booking warning is printed at the end.
    """
    # Jo is home 7 AM - 9 PM; Sam is home 9 AM - 5 PM
    jo = Owner("Jo", home_start=time(7, 0), home_end=time(21, 0))
    sam = Owner("Sam", home_start=time(9, 0), home_end=time(17, 0))

    biscuit = Pet("Biscuit", breed="Golden Retriever", gender="Male", age=4, priority=1)
    mochi = Pet("Mochi", breed="Tabby Cat", gender="Female", age=2)

    # Pets and tasks belong to a household shared by Jo and Sam
    household = Household("Jo's Home")
    household.add_member(jo)
    household.add_member(sam)
    household.add_pet(biscuit)
    household.add_pet(mochi)

    # Three tasks for Biscuit
    household.add_task(Task("Morning walk", 30, 1, pets=[biscuit]), due_time=time(7, 30), assigned_to=jo)
    household.add_task(Task("Joint medicine", 5, 1, pets=[biscuit]), due_time=time(12, 0), assigned_to=jo)
    household.add_task(Task("Evening fetch", 20, 2, pets=[biscuit]), due_time=time(18, 0), assigned_to=jo)

    # Three tasks for Mochi
    household.add_task(Task("Breakfast", 10, 1, pets=[mochi]), due_time=time(8, 15), assigned_to=jo)
    household.add_task(Task("Clean litter box", 10, 2, pets=[mochi]), due_time=time(15, 0), assigned_to=jo)
    household.add_task(Task("Brushing", 15, 3, pets=[mochi]), due_time=time(20, 0), assigned_to=jo)

    # Two tasks at the same time: Biscuit can't be with Jo and Sam at once
    household.add_task(Task("Grooming", 20, 2, pets=[biscuit]), due_time=time(10, 0), assigned_to=jo)
    household.add_task(Task("Vet call", 15, 1, pets=[biscuit]), due_time=time(10, 0), assigned_to=sam)

    scheduler = Scheduler(household)
    plan = scheduler.create_daily_plan()

    print("Today's Schedule")
    print("=" * 40)
    for item in plan:
        pets = ", ".join(pet.name for pet in item.task.pets)
        print(
            f"{item.start_time:%I:%M %p} - {item.end_time():%I:%M %p}  "
            f"{item.task.name} ({pets}) [priority {item.task.priority}]"
        )

    if scheduler.skipped:
        print("\nSkipped:")
        for task, reason in scheduler.skipped:
            print(f"  {task.name}: {reason}")

    for warning in scheduler.warnings:
        print(f"WARNING: {warning}")


def out_of_order_demo() -> None:
    """Add tasks in a scrambled time order, then show them sorted and filtered."""
    jo = Owner("Jo", home_start=time(7, 0), home_end=time(21, 0))
    biscuit = Pet("Biscuit", breed="Golden Retriever", priority=1)
    mochi = Pet("Mochi", breed="Tabby Cat")

    household = Household("Jo's Home")
    household.add_member(jo)
    household.add_pet(biscuit)
    household.add_pet(mochi)

    # Added deliberately out of time order
    household.add_task(Task("Brushing", 15, 3, pets=[mochi]), due_time=time(20, 0), assigned_to=jo)
    household.add_task(Task("Morning walk", 30, 1, pets=[biscuit]), due_time=time(7, 30), assigned_to=jo)
    household.add_task(Task("Clean litter box", 10, 2, pets=[mochi]), due_time=time(15, 0), assigned_to=jo)
    household.add_task(Task("Joint medicine", 5, 1, pets=[biscuit]), due_time=time(12, 0), assigned_to=jo)
    household.add_task(Task("Breakfast", 10, 1, pets=[mochi]), due_time=time(8, 15), assigned_to=jo)

    print("\n\nTasks in the order they were added")
    print("=" * 40)
    for task in household.tasks:
        print(f"{task.due_time:%H:%M}  {task.name}")

    scheduler = Scheduler(household)
    print("\nTasks sorted by time")
    print("=" * 40)
    for task in scheduler.sort_by_time():
        print(f"{task.due_time:%H:%M}  {task.name}")

    # Check off one task, then try the filters
    household.check_off_task(household.tasks[1], by=jo)  # Morning walk

    print("\nCompleted today:", [t.name for t in scheduler.filter_tasks(completed=True)])
    print("Still to do:", [t.name for t in scheduler.filter_tasks(completed=False)])
    print("Mochi's tasks:", [t.name for t in scheduler.filter_tasks(pet_name="mochi")])


if __name__ == "__main__":
    main()
    out_of_order_demo()
