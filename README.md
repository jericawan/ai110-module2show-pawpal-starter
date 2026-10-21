# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Today's Schedule
========================================
07:30 AM - 08:00 AM  Morning walk (Biscuit) [priority 1]
08:15 AM - 08:25 AM  Breakfast (Mochi) [priority 1]
10:00 AM - 10:20 AM  Grooming (Biscuit) [priority 2]
10:00 AM - 10:15 AM  Vet call (Biscuit) [priority 1]
12:00 PM - 12:05 PM  Joint medicine (Biscuit) [priority 1]
03:00 PM - 03:10 PM  Clean litter box (Mochi) [priority 2]
06:00 PM - 06:20 PM  Evening fetch (Biscuit) [priority 2]
08:00 PM - 08:15 PM  Brushing (Mochi) [priority 3]
WARNING: Biscuit double-booked: 'Grooming' at 10:00 overlaps 'Vet call' at 10:00
```

## 🧪 Testing PawPal+
Phase 2 Step 4:
The Task class represents a single  activity. It stores how long the task takes, how important it is, and when it needs to be done, and it keeps track of whether it has been completed and by whom. The Pet class holds each animal's information and the list of tasks it requires. It can update the pet's priority and show which of its tasks are still unfinished. The Owner class represents one person in the household and manages their availability, including when they will be home and how much time they have for pet care. The Household class brings everyone together: it adds people and pets, and it lets members add, edit, assign, complete, and remove tasks. Finally, the Scheduler organizes the day. It assigns tasks to whoever is available, builds a timed daily plan and checklist, and explains why any tasks were skipped.

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

### ✨ Features

**Scheduling**
- **Priority-based planning order.** Tasks are ranked by a four-part key:
  1. fixed-time tasks before flexible ones
  2. earlier due time
  3. task priority (1 = most important)
  4. the pet's priority, which breaks ties

  `Scheduler._sort_key()`, `Scheduler.create_daily_plan()`
- **Greedy time-slot placement.** Fixed-time tasks are booked at their due time. Flexible tasks are then placed in the earliest free slot, checking every 5 minutes. Everyone's fixed tasks are placed before anyone's flexible tasks, so flexible tasks fit around them. `Scheduler._plan_for_owner()`
- **Time limits and home hours.** Each person's tasks must fit inside their home hours and their daily minutes (`available_minutes`). A task that doesn't fit is skipped, with the reason recorded. An owner with no home hours set is available all day. `Owner.can_fit()`, `Owner.home_window()`, `Owner.minutes_for_today()`
- **Automatic task assignment.** Each unassigned task goes to the household member who is home for the whole task and has the most free minutes left. This spreads the work evenly. `Scheduler.assign_unassigned_tasks()`

**Sorting and filtering**
- **Sort by time.** Lists tasks earliest first, with untimed tasks at the end. Tasks with the same time stay in the order they were added. The app's task table uses this. `Scheduler.sort_by_time()`
- **Filtering.** Filters tasks by status ("done" or "still to do" on a given day) and by pet name, which ignores capitalization. The two filters can be combined. `Scheduler.filter_tasks()`, `Pet.pending_tasks()`, `Owner.pending_tasks()`

**Recurring tasks**
- **Daily and weekly repeats.** Checking off a repeating task automatically creates its next copy. The copy goes to the same person and is due one day or one week later. `Task.next_occurrence()`, `Household.check_off_task()`
- **Late check-offs.** The next copy counts from the day the task was done if that's after its due date, so finishing a task late doesn't leave an overdue copy behind. Unfinished tasks keep showing up until they're done. `Task.is_pending_on()`
- **Duplicate protection.** Checking off the same task twice creates only one next copy.

**Conflicts**
- **Double-booking detection.** After planning, every pair of tasks is compared. If two tasks overlap in time and share a pet or a person, a warning is added. Back-to-back tasks don't count. Tasks are flagged, never removed. `Scheduler.detect_conflicts()`
- **Pet double-booking avoidance.** Flexible tasks are moved to avoid times when a pet is already booked with another household member. `Scheduler._plan_for_owner()`
- **Instant clash warning.** When a task is added in the app, it's checked against existing timed tasks right away. A pop-up and a warning say "Possible duplicate" or "Time clash". `Scheduler.find_clashes()`

**Explanations and safety checks**
- **Plan explanations.** Every scheduled task has a reason, such as "must be done at 17:00" or "priority 1, earliest free slot". Every skipped task says why it was skipped. `Scheduler.explain_plan()`, plus the "why" column in the app.
- **Input validation.** Durations of 0 or less, unknown repeat frequencies, home hours that end before they start, and pets or people from outside the household are all rejected with clear errors.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. Open application and owner can create an object for theirself and their pet. 
2. Add "morning walk", 15 minutes, "priority high" with set time 8:00 AM
3.Add "feed breakfast", 10 minutes, "priority high" with set time 8:00 AM
4. See warning appear on the screen of conflicting times. 
5. Add "clean paws", 5 minutes, "priority high", at 8:20 AM. 
6. Click generate schedule 
7. check off when task is complete. 

CLI output: (base) jericawan@Mac codepath26 % python -u "/Users/jericawan/Desktop/codepath26/AI110/project_2_ai110/main.py"
Today's Schedule
========================================
07:30 AM - 08:00 AM  Morning walk (Biscuit) [priority 1]
08:15 AM - 08:25 AM  Breakfast (Mochi) [priority 1]
10:00 AM - 10:20 AM  Grooming (Biscuit) [priority 2]
10:00 AM - 10:15 AM  Vet call (Biscuit) [priority 1]
12:00 PM - 12:05 PM  Joint medicine (Biscuit) [priority 1]
03:00 PM - 03:10 PM  Clean litter box (Mochi) [priority 2]
06:00 PM - 06:20 PM  Evening fetch (Biscuit) [priority 2]
08:00 PM - 08:15 PM  Brushing (Mochi) [priority 3]
WARNING: Biscuit double-booked: 'Grooming' at 10:00 overlaps 'Vet call' at 10:00


Tasks in the order they were added
========================================
20:00  Brushing
07:30  Morning walk
15:00  Clean litter box
12:00  Joint medicine
08:15  Breakfast

Tasks sorted by time
========================================
07:30  Morning walk
08:15  Breakfast
12:00  Joint medicine
15:00  Clean litter box
20:00  Brushing

Completed today: ['Morning walk']
Still to do: ['Brushing', 'Clean litter box', 'Joint medicine', 'Breakfast']
Mochi's tasks: ['Brushing', 'Clean litter box', 'Breakfast']

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
## Testing PawPal+
```
(.venv) (base) jericawan@Mac project_2_ai110 % python -m pytest
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/jericawan/Desktop/codepath26/AI110/project_2_ai110
plugins: anyio-4.15.1
collected 83 items

tests/test_pawpal.py ................................................... [ 61%]
................................                                         [100%]

============================== 83 passed in 0.04s ==============================
```


Confidence Level:3