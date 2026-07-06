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
        pass

    def update_preferences(self, preferences: str) -> None:
        """Update the owner's care preferences."""
        pass

    def set_available_time(self, start: str, end: str) -> None:
        """Set the owner's available time window."""
        pass

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
        pass

    def add_task(self, task: "Task") -> None:
        """Attach a task to this pet and set its back-reference."""
        task.pet = self
        self.tasks.append(task)

    def update_profile(self, species: str, age: int, health_notes: str) -> None:
        """Update the core pet profile information."""
        pass

    def get_daily_requirements(self) -> List[str]:
        """Return the pet's daily care requirements."""
        return []


@dataclass
class Task:
    title: str
    category: str
    duration_minutes: int
    priority: Priority
    preferred_time: str
    frequency: Frequency = Frequency.DAILY
    pet: Optional["Pet"] = None

    def update_duration(self, duration_minutes: int) -> None:
        """Update the task duration."""
        pass

    def change_priority(self, priority: Priority) -> None:
        """Change the task priority level."""
        pass

    def is_high_priority(self) -> bool:
        """Return whether the task should be treated as high priority."""
        return self.priority is Priority.HIGH

    def fits_in_time_window(self, available_start: str, available_end: str) -> bool:
        """Check whether the task fits within the owner's time window."""
        return False


@dataclass
class PlanItem:
    """A task assigned to a concrete start time in the daily plan."""

    task: Task
    start_minutes: int

    @property
    def end_minutes(self) -> int:
        return self.start_minutes + self.task.duration_minutes

    def __str__(self) -> str:
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
        """Flatten tasks off every pet into the planner's working list."""
        self.tasks = [task for pet in self.pets for task in pet.tasks]

    def generate_plan(self) -> List[PlanItem]:
        """Create a daily care plan from the current tasks."""
        return []

    def sort_tasks(self) -> None:
        """Sort tasks according to planning rules."""
        pass

    def resolve_conflicts(self) -> None:
        """Resolve overlapping or incompatible tasks."""
        pass

    def explain_plan(self) -> str:
        """Return a plain-language explanation of the generated plan."""
        return ""
