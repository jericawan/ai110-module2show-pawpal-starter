"""Demo: build one owner with two pets and print today's schedule."""

from datetime import time

from pawpal_system import Household, Owner, Pet, Scheduler, Task


def main() -> None:
    # Owner is home 7 AM - 9 PM
    jo = Owner("Jo", home_start=time(7, 0), home_end=time(21, 0))

    biscuit = Pet("Biscuit", breed="Golden Retriever", gender="Male", age=4, priority=1)
    mochi = Pet("Mochi", breed="Tabby Cat", gender="Female", age=2)

    # Pets and tasks belong to a household; Jo is its only member
    household = Household("Jo's Home")
    household.add_member(jo)
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


if __name__ == "__main__":
    main()
