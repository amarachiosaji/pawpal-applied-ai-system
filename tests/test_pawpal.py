"""Simple tests for the PawPal system."""

import os
import sys

# Make the project root importable when running this file directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task, Priority, Frequency


def make_task(title: str = "Morning walk") -> Task:
    """Build a basic task for use in tests."""
    return Task(
        title=title,
        category="Exercise",
        duration_minutes=30,
        priority=Priority.HIGH,
        preferred_time="07:30",
        frequency=Frequency.DAILY,
    )


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


if __name__ == "__main__":
    test_mark_complete_changes_status()
    test_add_task_increases_pet_task_count()
    print("All tests passed!")
