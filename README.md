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

Today's Schedule
===========================
=============
07:30 AM - 08:00 AM  Morning walk (Biscuit) [priority 1]
08:15 AM - 08:25 AM  Breakfast (Mochi) [priority 1]
12:00 PM - 12:05 PM  Joint medicine (Biscuit) [priority 1]
03:00 PM - 03:10 PM  Clean litter box (Mochi) [priority 2]
06:00 PM - 06:20 PM  Evening fetch (Biscuit) [priority 2]
08:00 PM - 08:15 PM  Brushing (Mochi) [priority 3]

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

> Fill in once you've implemented scheduling logic.

                    | Feature               | Method(s)                         | Notes |
| Task sorting |    |priority of task       |scheduler.sort_by_time()           |-------|
| Filtering |       | filter by pet or task |scheduler.filter_tasks(),Pet.pending_tasks(), Owner.pending_tasks()
| Conflict handling | alerts when pets have multiple tasks at once, create household allowing multiple members complete/add tasks(more preventative)| detect_conflicts(),assign_unassigned_tasks()
| Recurring tasks | | repeat reaccuring tasks, check off tasks| task.next_occurrence(), Household.check_off_task()

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
