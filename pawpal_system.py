from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


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
    priority: str
    preferred_time: str
    recurring: bool = False

    def update_duration(self, duration_minutes: int) -> None:
        """Update the task duration."""
        pass

    def change_priority(self, priority: str) -> None:
        """Change the task priority level."""
        pass

    def is_high_priority(self) -> bool:
        """Return whether the task should be treated as high priority."""
        return False

    def fits_in_time_window(self, available_start: str, available_end: str) -> bool:
        """Check whether the task fits within the owner's time window."""
        return False


@dataclass
class Planner:
    owner: Owner | None = None
    pet: Pet | None = None
    tasks: List[Task] = field(default_factory=list)

    def generate_plan(self) -> List[Task]:
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
