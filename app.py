from datetime import date, time

import streamlit as st

from pawpal_system import Household, Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")

# [AI-added] st.session_state change: store one Owner in the session "vault".
# Streamlit reruns this whole script on every click, so without this check a new
# Owner would be created (and reset) each time.
if "owner" not in st.session_state:  # only true on the first run
    st.session_state.owner = Owner(name=owner_name)  # create and save the Owner once
owner = st.session_state.owner  # reuse the same saved Owner on every rerun
owner.name = owner_name  # keep the stored owner in sync with the text box
# [end AI-added st.session_state change]

# [AI-added] st.session_state change: store one Household in the session "vault".
# Pets and tasks belong to a Household (see diagrams/uml_draft.mmd), so it must
# survive reruns too. The Owner is added as its first member.
if "household" not in st.session_state:  # only true on the first run
    st.session_state.household = Household(name="My Household")
    st.session_state.household.add_member(owner)
household = st.session_state.household  # reuse the same saved Household on every rerun
# [end AI-added st.session_state change]

pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

# [AI-added] Map the dropdown labels to Task priority ints (1 = most important)
PRIORITY_TO_INT = {"high": 1, "medium": 2, "low": 3}

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

# [AI-added] Optional due time, matching Household.add_task(task, due_time=...)
has_due_time = st.checkbox("Must be done at a set time")
due_time = st.time_input("Due time", value=time(17, 0)) if has_due_time else None

# [AI-added] Repeating tasks: matches Task(frequency=..., due_date=...)
REPEAT_OPTIONS = {"does not repeat": None, "daily": "daily", "weekly": "weekly"}
repeat = st.selectbox("Repeats", list(REPEAT_OPTIONS))
frequency = REPEAT_OPTIONS[repeat]
first_due = st.date_input("First due date", value=date.today()) if frequency else None

if st.button("Add task"):
    # [AI-added] Find the pet by name in the household, or create and add it
    pet = next((p for p in household.pets if p.name == pet_name), None)
    if pet is None:
        pet = Pet(name=pet_name, breed=species)
        household.add_pet(pet)

    # [AI-added] Build a Task and add it through the Household (per the UML),
    # which also adds it to the pet's and owner's task lists
    task = Task(
        name=task_title,
        duration_minutes=int(duration),
        priority=PRIORITY_TO_INT[priority],
        pets=[pet],
        frequency=frequency,
        due_date=first_due,
    )
    household.add_task(task, due_time=due_time, assigned_to=owner)
    st.success(f"Added '{task_title}' for {pet_name}.")

    # [AI-added] Warn right away if the new task overlaps another timed task
    # for the same pet or person; the task is still added
    for other in Scheduler(household).find_clashes(task):
        same_task = other.name.strip().lower() == task.name.strip().lower()
        kind = "Possible duplicate" if same_task else "Time clash"
        message = (
            f"{kind}: '{task.name}' at {task.due_time:%I:%M %p} overlaps "
            f"'{other.name}' ({', '.join(p.name for p in other.pets)}) "
            f"at {other.due_time:%I:%M %p}."
        )
        st.warning(f"⚠️ {message}")
        st.toast(message, icon="⚠️")

# [AI-added] Show tasks from the Household instead of the old st.session_state.tasks list
if household.tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "title": t.name,
                "pet": ", ".join(p.name for p in t.pets),
                "duration_minutes": t.duration_minutes,
                "priority": t.priority,
                "due_time": t.due_time.strftime("%I:%M %p") if t.due_time else "any time",
                "assigned_to": t.assigned_to.name if t.assigned_to else "",
                "repeats": t.frequency or "no",
                "due_date": t.due_date.strftime("%b %d") if t.due_date else "every day",
                "done": "yes" if t.last_completed else "",
            }
            for t in Scheduler(household).sort_by_time()  # [AI-added] earliest first
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# [AI-added] One day picker shared by check-off and the schedule, so you can
# check a repeating task off and then see its next copy on a later day
plan_day = st.date_input("Day", value=date.today())

st.subheader("Check Off a Task")
if "check_off_message" in st.session_state:
    st.success(st.session_state.pop("check_off_message"))
pending = [t for t in household.tasks if t.is_pending_on(plan_day)]
if pending:
    # Choose by position: Streamlit hands back a copy of object options, and
    # Household only recognizes the original Task objects
    choice = st.selectbox(
        "Task to mark complete",
        range(len(pending)),
        format_func=lambda i: f"{pending[i].name} ({', '.join(p.name for p in pending[i].pets)})",
    )
    to_check = pending[choice]
    if st.button("Mark complete"):
        # [AI-added] Household.check_off_task returns the next copy for daily/weekly tasks
        next_task = household.check_off_task(to_check, by=owner, on=plan_day)
        if next_task is not None:
            message = f"Done! Next '{next_task.name}' added for {next_task.due_date:%A, %b %d}."
        else:
            message = f"Done! '{to_check.name}' is complete."
        st.session_state.check_off_message = message  # survives the rerun below
        st.rerun()  # refresh the task table and list right away
else:
    st.info("Nothing left to do on this day.")

st.divider()

st.subheader("Build Schedule")
st.caption("Plans the tasks still to do on the chosen day.")

if st.button("Generate schedule"):
    # [AI-added] Connect the Scheduler; it only plans tasks pending on plan_day
    scheduler = Scheduler(household)
    plan = scheduler.create_daily_plan(plan_day)
    if plan:
        st.table(
            [
                {
                    "time": f"{item.start_time:%I:%M %p} - {item.end_time():%I:%M %p}",
                    "task": item.task.name,
                    "pet": ", ".join(p.name for p in item.task.pets),
                    "why": item.reason,
                }
                for item in plan
            ]
        )
    else:
        st.info("No tasks to schedule on this day.")
    for task, reason in scheduler.skipped:
        st.warning(f"Skipped {task.name}: {reason}")
    # [AI-added] Overlaps stay in the plan; we only warn about them
    for warning in scheduler.warnings:
        st.warning(f"⚠️ {warning}")
