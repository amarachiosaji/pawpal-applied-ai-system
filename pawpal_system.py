from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Priority(Enum):
    """Task priority with an explicit ordering (lower rank = more urgent)."""

    HIGH = 0
    MEDIUM = 1
    LOW = 2

    @property
    def rank(self) -> int:
        """Return the numeric rank used for ordering (lower = more urgent)."""
        return self.value


class Frequency(Enum):
    """How often a task recurs."""

    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


def parse_time(value: str) -> int:
    """Convert an ``"HH:MM"`` string into minutes since midnight."""
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def format_time(minutes: int) -> str:
    """Convert minutes since midnight back into an ``"HH:MM"`` string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Owner:
    name: str
    preferences: str = ""
    available_start: str = ""
    available_end: str = ""
    pets: List["Pet"] = field(default_factory=list)

    def add_pet(self, pet: "Pet") -> None:
        """Attach a pet to this owner."""
        if pet not in self.pets:
            self.pets.append(pet)

    def update_preferences(self, preferences: str) -> None:
        """Update the owner's care preferences."""
        self.preferences = preferences

    def set_available_time(self, start: str, end: str) -> None:
        """Set the owner's available time window."""
        self.available_start = start
        self.available_end = end

    def all_tasks(self) -> List["Task"]:
        """Return every task across all of this owner's pets.

        This is the single entry point the Planner uses to ask the Owner
        for its pet data, so the Planner never has to reach into each
        pet's task list itself.
        """
        return [task for pet in self.pets for task in pet.tasks]

    def available_minutes(self) -> int:
        """Return the length of the owner's availability window in minutes."""
        if not self.available_start or not self.available_end:
            return 0
        return parse_time(self.available_end) - parse_time(self.available_start)


@dataclass
class Pet:
    name: str
    species: str
    age: int
    health_notes: str = ""
    care_needs: List[str] = field(default_factory=list)
    tasks: List["Task"] = field(default_factory=list)

    def add_care_need(self, care_need: str) -> None:
        """Add a new care need for this pet."""
        if care_need not in self.care_needs:
            self.care_needs.append(care_need)

    def add_task(self, task: "Task") -> None:
        """Attach a task to this pet and set its back-reference."""
        task.pet = self
        self.tasks.append(task)

    def update_profile(self, species: str, age: int, health_notes: str) -> None:
        """Update the core pet profile information."""
        self.species = species
        self.age = age
        self.health_notes = health_notes

    def get_daily_requirements(self) -> List[str]:
        """Return the pet's daily care requirements."""
        return [
            task.title
            for task in self.tasks
            if task.frequency is Frequency.DAILY
        ]


@dataclass
class Task:
    title: str
    category: str
    duration_minutes: int
    priority: Priority
    preferred_time: str
    frequency: Frequency = Frequency.DAILY
    pet: Optional["Pet"] = None
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def update_duration(self, duration_minutes: int) -> None:
        """Update the task duration."""
        self.duration_minutes = duration_minutes

    def change_priority(self, priority: Priority) -> None:
        """Change the task priority level."""
        self.priority = priority

    def is_high_priority(self) -> bool:
        """Return whether the task should be treated as high priority."""
        return self.priority is Priority.HIGH

    def fits_in_time_window(self, available_start: str, available_end: str) -> bool:
        """Check whether the task fits within the owner's time window."""
        if not available_start or not available_end:
            return False
        window_start = parse_time(available_start)
        window_end = parse_time(available_end)
        start = parse_time(self.preferred_time) if self.preferred_time else window_start
        # The task must start no earlier than the window opens and finish
        # before the window closes.
        return start >= window_start and start + self.duration_minutes <= window_end


@dataclass
class PlanItem:
    """A task assigned to a concrete start time in the daily plan."""

    task: Task
    start_minutes: int

    @property
    def end_minutes(self) -> int:
        """Return the minute the task finishes (start plus its duration)."""
        return self.start_minutes + self.task.duration_minutes

    def __str__(self) -> str:
        """Return a human-readable one-line summary of the scheduled item."""
        pet_name = self.task.pet.name if self.task.pet else "?"
        return (
            f"{format_time(self.start_minutes)} — {self.task.title} "
            f"({self.task.duration_minutes} min) "
            f"[pet: {pet_name}, priority: {self.task.priority.name.lower()}]"
        )


@dataclass
class Planner:
    owner: Owner | None = None
    pets: List[Pet] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)

    def collect_tasks(self) -> None:
        """Ask the Owner for its pets, then flatten their tasks.

        The Planner does not reach into each pet directly. It "talks" to
        the Owner: it reads ``owner.pets`` to know which pets exist and
        calls ``owner.all_tasks()`` to get every task in one call. This
        keeps the Owner as the single source of truth for pet data.
        """
        if self.owner is None:
            self.tasks = []
            return
        self.pets = list(self.owner.pets)
        self.tasks = self.owner.all_tasks()

    def sort_tasks(self) -> None:
        """Sort tasks by priority first, then by preferred start time."""
        self.tasks.sort(
            key=lambda task: (
                task.priority.rank,
                parse_time(task.preferred_time) if task.preferred_time else 0,
            )
        )

    def generate_plan(self) -> List[PlanItem]:
        """Create a conflict-free daily care plan from the current tasks."""
        self.collect_tasks()
        self.sort_tasks()

        plan: List[PlanItem] = []
        # Track the earliest minute the next task may start so nothing overlaps.
        next_free = (
            parse_time(self.owner.available_start)
            if self.owner and self.owner.available_start
            else 0
        )
        window_end = (
            parse_time(self.owner.available_end)
            if self.owner and self.owner.available_end
            else None
        )

        for task in self.tasks:
            preferred = parse_time(task.preferred_time) if task.preferred_time else next_free
            start = max(preferred, next_free)
            if window_end is not None and start + task.duration_minutes > window_end:
                # No room left in the owner's availability window; skip it.
                continue
            plan.append(PlanItem(task=task, start_minutes=start))
            next_free = start + task.duration_minutes

        return plan

    def resolve_conflicts(self) -> None:
        """Resolve overlapping tasks by re-sorting into planning order.

        Actual overlap handling happens in :meth:`generate_plan`, which
        pushes each task's start time past the previous one. Here we just
        ensure the working list is in the canonical order first.
        """
        self.sort_tasks()

    def explain_plan(self) -> str:
        """Return a plain-language explanation of the generated plan."""
        plan = self.generate_plan()
        if not plan:
            return "No tasks could be scheduled."

        owner_name = self.owner.name if self.owner else "the owner"
        lines = [f"Daily care plan for {owner_name}:"]
        lines.extend(f"  {item}" for item in plan)
        return "\n".join(lines)
