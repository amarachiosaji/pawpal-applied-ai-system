"""Tests for the PawPal+ system.

Grouped into three parts:
  * data-model basics (Task/Pet state),
  * core scheduling behavior (sort, conflicts, plan, recurrence),
  * edge cases (empty data, exact-time clashes, bad input, windows).

The suite explicitly covers the three required behaviors:
  * Sorting correctness  -> test_sort_returns_chronological_order
  * Recurrence logic      -> test_mark_complete_spawns_next_daily_occurrence
  * Conflict detection     -> test_two_tasks_at_exact_same_time_conflict
"""

import os
import sys
from datetime import date, timedelta

# Make the project root importable when running this file directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import (
    Frequency,
    Owner,
    Pet,
    Planner,
    Priority,
    Task,
)


def make_task(
    title: str = "Morning walk",
    priority: Priority = Priority.HIGH,
    preferred_time: str = "07:30",
    duration_minutes: int = 30,
    frequency: Frequency = Frequency.DAILY,
) -> Task:
    """Build a task for use in tests, with sensible overridable defaults."""
    return Task(
        title=title,
        category="Exercise",
        duration_minutes=duration_minutes,
        priority=priority,
        preferred_time=preferred_time,
        frequency=frequency,
    )


def make_planner(*pets: Pet) -> Planner:
    """Build a Planner wired to an owner that owns the given pets."""
    owner = Owner(name="Amarachi", available_start="07:00", available_end="20:00")
    for pet in pets:
        owner.add_pet(pet)
    return Planner(owner=owner)


# --------------------------------------------------------------------------- #
# Data-model basics
# --------------------------------------------------------------------------- #

def test_mark_complete_changes_status():
    """Calling mark_complete() should flip the task's status to done."""
    task = make_task()

    # A brand-new task starts out not completed.
    assert task.completed is False

    task.mark_complete()

    # After marking complete, the status has changed.
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase that pet's task count by one."""
    pet = Pet(name="Rex", species="Dog", age=4)

    assert len(pet.tasks) == 0

    pet.add_task(make_task())

    assert len(pet.tasks) == 1


def test_add_task_sets_back_reference():
    """add_task() should wire the task's .pet back-reference to the pet."""
    pet = Pet(name="Rex", species="Dog", age=4)
    task = make_task()

    pet.add_task(task)

    assert task.pet is pet


# --------------------------------------------------------------------------- #
# Core scheduling behavior
# --------------------------------------------------------------------------- #

def test_sort_returns_chronological_order():
    """SORTING CORRECTNESS: equal-priority tasks come back in time order.

    Tasks are added out of order; after sorting, same-priority tasks must be
    returned chronologically by their preferred start time.
    """
    pet = Pet(name="Rex", species="Dog", age=4)
    pet.add_task(make_task("Dinner", priority=Priority.MEDIUM, preferred_time="18:00"))
    pet.add_task(make_task("Breakfast", priority=Priority.MEDIUM, preferred_time="08:00"))
    pet.add_task(make_task("Lunch", priority=Priority.MEDIUM, preferred_time="12:30"))

    planner = make_planner(pet)
    planner.collect_tasks()
    planner.sort_tasks()

    times = [task.preferred_time for task in planner.tasks]
    assert times == ["08:00", "12:30", "18:00"]


def test_sort_orders_by_priority_then_time():
    """Priority wins over the clock: a HIGH task beats an earlier LOW task."""
    pet = Pet(name="Rex", species="Dog", age=4)
    low_early = make_task("Litter", priority=Priority.LOW, preferred_time="06:00")
    high_late = make_task("Walk", priority=Priority.HIGH, preferred_time="09:00")
    high_early = make_task("Feed", priority=Priority.HIGH, preferred_time="07:00")
    pet.add_task(low_early)
    pet.add_task(high_late)
    pet.add_task(high_early)

    planner = make_planner(pet)
    planner.collect_tasks()
    planner.sort_tasks()

    assert [t.title for t in planner.tasks] == ["Feed", "Walk", "Litter"]


def test_mark_complete_spawns_next_daily_occurrence():
    """RECURRENCE LOGIC: completing a DAILY task creates tomorrow's copy."""
    pet = Pet(name="Rex", species="Dog", age=4)
    task = make_task(frequency=Frequency.DAILY)
    pet.add_task(task)

    next_task = task.mark_complete()

    # The original is done; exactly one new incomplete task is attached,
    # scheduled for the following day.
    assert task.completed is True
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task in pet.tasks
    assert len(pet.tasks) == 2


def test_mark_complete_spawns_next_weekly_occurrence():
    """Completing a WEEKLY task advances the due date by seven days."""
    pet = Pet(name="Rex", species="Dog", age=4)
    task = make_task(frequency=Frequency.WEEKLY)
    pet.add_task(task)

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(days=7)


def test_mark_complete_once_task_does_not_recur():
    """A ONCE task completes without spawning a follow-up."""
    pet = Pet(name="Rex", species="Dog", age=4)
    task = make_task(frequency=Frequency.ONCE)
    pet.add_task(task)

    next_task = task.mark_complete()

    assert task.completed is True
    assert next_task is None
    assert len(pet.tasks) == 1


def test_owner_all_tasks_flattens_across_pets():
    """Owner.all_tasks() returns every task across every pet."""
    rex = Pet(name="Rex", species="Dog", age=4)
    luna = Pet(name="Luna", species="Cat", age=2)
    rex.add_task(make_task("Walk"))
    luna.add_task(make_task("Feed"))
    owner = Owner(name="Amarachi")
    owner.add_pet(rex)
    owner.add_pet(luna)

    assert len(owner.all_tasks()) == 2


# --------------------------------------------------------------------------- #
# Edge cases
# --------------------------------------------------------------------------- #

def test_two_tasks_at_exact_same_time_conflict():
    """CONFLICT DETECTION: two tasks at the identical time are flagged."""
    pet = Pet(name="Rex", species="Dog", age=4)
    pet.add_task(make_task("Walk", preferred_time="08:00", duration_minutes=30))
    pet.add_task(make_task("Groom", preferred_time="08:00", duration_minutes=15))

    planner = make_planner(pet)
    conflicts = planner.detect_conflicts()

    assert len(conflicts) == 1
    assert conflicts[0].same_pet is True


def test_detect_conflicts_flags_overlap_across_pets():
    """Overlapping tasks on different pets are reported as a conflict."""
    rex = Pet(name="Rex", species="Dog", age=4)
    luna = Pet(name="Luna", species="Cat", age=2)
    rex.add_task(make_task("Walk", preferred_time="08:00", duration_minutes=30))
    luna.add_task(make_task("Feed", preferred_time="08:15", duration_minutes=30))

    planner = make_planner(rex, luna)
    conflicts = planner.detect_conflicts()

    assert len(conflicts) == 1
    assert conflicts[0].same_pet is False


def test_pet_with_no_tasks_produces_empty_plan():
    """A pet with no tasks yields an empty plan and a friendly message."""
    pet = Pet(name="Rex", species="Dog", age=4)
    planner = make_planner(pet)

    assert planner.generate_plan() == []
    assert planner.explain_plan() == "No tasks could be scheduled."


def test_touching_end_to_end_is_not_a_conflict():
    """Tasks that abut (08:00-08:10 and 08:10-08:20) do not clash."""
    pet = Pet(name="Rex", species="Dog", age=4)
    pet.add_task(make_task("A", preferred_time="08:00", duration_minutes=10))
    pet.add_task(make_task("B", preferred_time="08:10", duration_minutes=10))

    planner = make_planner(pet)

    assert planner.detect_conflicts() == []


def test_task_without_preferred_time_is_skipped_in_conflicts():
    """A task with no preferred_time has no fixed slot, so it never clashes."""
    pet = Pet(name="Rex", species="Dog", age=4)
    pet.add_task(make_task("Floating", preferred_time="", duration_minutes=30))
    pet.add_task(make_task("Walk", preferred_time="08:00", duration_minutes=30))

    planner = make_planner(pet)

    assert planner.detect_conflicts() == []


def test_generate_plan_produces_no_overlaps():
    """Scheduled items never overlap; a clashing task is pushed later."""
    pet = Pet(name="Rex", species="Dog", age=4)
    pet.add_task(make_task("Walk", preferred_time="08:00", duration_minutes=30))
    pet.add_task(make_task("Groom", preferred_time="08:00", duration_minutes=15))

    planner = make_planner(pet)
    plan = planner.generate_plan()

    for earlier, later in zip(plan, plan[1:]):
        assert later.start_minutes >= earlier.end_minutes


def test_task_that_overruns_window_is_dropped():
    """A task that cannot finish before the window closes is not scheduled."""
    pet = Pet(name="Rex", species="Dog", age=4)
    # Owner is available 07:00-08:00 only; a 90-minute task can't fit.
    pet.add_task(make_task("Long walk", preferred_time="07:30", duration_minutes=90))
    owner = Owner(name="Amarachi", available_start="07:00", available_end="08:00")
    owner.add_pet(pet)
    planner = Planner(owner=owner)

    assert planner.generate_plan() == []


def test_filter_tasks_by_completion_and_pet():
    """filter_tasks() narrows by completion state and (case-insensitive) pet."""
    rex = Pet(name="Rex", species="Dog", age=4)
    luna = Pet(name="Luna", species="Cat", age=2)
    done = make_task("Walk")
    done.completed = True
    rex.add_task(done)
    rex.add_task(make_task("Feed"))
    luna.add_task(make_task("Litter"))

    planner = make_planner(rex, luna)
    planner.collect_tasks()

    assert len(planner.filter_tasks(completed=True)) == 1
    assert len(planner.filter_tasks(completed=False)) == 2
    assert len(planner.filter_tasks(pet_name="rex")) == 2  # case-insensitive


def test_planner_with_no_owner_is_safe():
    """A planner with no owner collects zero tasks and does not crash."""
    planner = Planner()
    planner.collect_tasks()

    assert planner.tasks == []
    assert planner.generate_plan() == []


def test_check_conflicts_degrades_on_bad_time_string():
    """Malformed time data becomes a WARNING instead of raising."""
    pet = Pet(name="Rex", species="Dog", age=4)
    pet.add_task(make_task("Walk", preferred_time="not-a-time"))

    planner = make_planner(pet)
    result = planner.check_conflicts()

    assert result.startswith("WARNING:")


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
