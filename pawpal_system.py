from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
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
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as done and roll a recurring task forward.

        For ``DAILY`` and ``WEEKLY`` tasks this creates a fresh, incomplete
        copy for the next occurrence and attaches it to the same pet, so the
        recurring chore reappears automatically. Returns the newly created
        task, or ``None`` for one-off (``ONCE``) tasks.
        """
        self.completed = True
        return self.create_next_occurrence()

    def create_next_occurrence(self) -> Optional["Task"]:
        """Create the next instance of a recurring task, if it recurs.

        Returns a new, incomplete :class:`Task` for ``DAILY``/``WEEKLY``
        frequencies (attached to this task's pet), or ``None`` for ``ONCE``.
        """
        if self.frequency not in (Frequency.DAILY, Frequency.WEEKLY):
            return None

        # Advance the due date using timedelta so month/year rollovers and
        # leap years are handled correctly: daily -> +1 day, weekly -> +7 days.
        step = timedelta(days=1) if self.frequency is Frequency.DAILY else timedelta(days=7)
        next_due = date.today() + step

        next_task = Task(
            title=self.title,
            category=self.category,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            preferred_time=self.preferred_time,
            frequency=self.frequency,
            due_date=next_due,
        )
        # Attach to the same pet so the recurring chore shows up next time.
        if self.pet is not None:
            self.pet.add_task(next_task)
        return next_task

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
class Conflict:
    """Two tasks whose preferred time windows overlap.

    The tasks may belong to the same pet (the owner can't be in two
    places for one animal at once) or to different pets (the owner
    can't attend to both animals simultaneously). Either way it is a
    scheduling clash the owner needs to know about.
    """

    task_a: Task
    task_b: Task

    @property
    def same_pet(self) -> bool:
        """Return whether both tasks are for the same pet."""
        return (
            self.task_a.pet is not None
            and self.task_b.pet is not None
            and self.task_a.pet is self.task_b.pet
        )

    def __str__(self) -> str:
        """Return a human-readable one-line description of the clash."""
        def describe(task: Task) -> str:
            pet_name = task.pet.name if task.pet else "?"
            end = parse_time(task.preferred_time) + task.duration_minutes
            return (
                f"{task.preferred_time}-{format_time(end)} {task.title} "
                f"({pet_name})"
            )

        scope = "same pet" if self.same_pet else "different pets"
        return f"[{scope}] {describe(self.task_a)} overlaps {describe(self.task_b)}"


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

    def filter_tasks(
        self,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[Task]:
        """Return tasks matching the given completion status and/or pet name.

        Both filters are optional. Passing neither returns every task; passing
        both keeps only tasks that satisfy *both* conditions. ``pet_name`` is
        matched case-insensitively.
        """
        results = self.tasks
        if completed is not None:
            results = [task for task in results if task.completed == completed]
        if pet_name is not None:
            target = pet_name.lower()
            results = [
                task
                for task in results
                if task.pet is not None and task.pet.name.lower() == target
            ]
        return list(results)

    def detect_conflicts(self) -> List[Conflict]:
        """Find tasks whose preferred time windows overlap.

        Each task wants to run at its ``preferred_time`` for
        ``duration_minutes``. Two tasks clash when those intervals
        overlap — regardless of whether they belong to the same pet or
        different pets, since a single owner can't do both at once.

        Returns every clashing pair (a task with no ``preferred_time``
        is skipped, as it has no fixed slot to collide with).
        """
        self.collect_tasks()

        # Only tasks with a fixed preferred time can truly clash.
        timed = [task for task in self.tasks if task.preferred_time]

        conflicts: List[Conflict] = []
        for i, task_a in enumerate(timed):
            start_a = parse_time(task_a.preferred_time)
            end_a = start_a + task_a.duration_minutes
            for task_b in timed[i + 1:]:
                start_b = parse_time(task_b.preferred_time)
                end_b = start_b + task_b.duration_minutes
                # Half-open intervals overlap when each starts before the
                # other ends; touching end-to-end (e.g. 8:00-8:10 and
                # 8:10-8:20) is not a clash.
                if start_a < end_b and start_b < end_a:
                    conflicts.append(Conflict(task_a=task_a, task_b=task_b))
        return conflicts

    def explain_conflicts(self) -> str:
        """Return a plain-language summary of any scheduling clashes."""
        conflicts = self.detect_conflicts()
        if not conflicts:
            return "No scheduling conflicts detected."

        lines = [f"Detected {len(conflicts)} scheduling conflict(s):"]
        lines.extend(f"  {conflict}" for conflict in conflicts)
        return "\n".join(lines)

    def check_conflicts(self) -> str:
        """Lightweight conflict check that *always* returns a message.

        Unlike :meth:`detect_conflicts`, this never raises. It is meant for
        quick, best-effort sanity checks (e.g. a UI banner) where a bad time
        string or a missing duration should degrade into a warning rather
        than crash the caller.

        Returns one of:
          * an all-clear message when no clashes are found,
          * a summary line plus one line per detected clash,
          * a warning message if the task data could not be parsed.
        """
        try:
            conflicts = self.detect_conflicts()
        except (ValueError, TypeError, AttributeError) as error:
            return f"WARNING: Could not check for conflicts: {error}"

        if not conflicts:
            return "OK: No scheduling conflicts."

        summary = f"WARNING: {len(conflicts)} scheduling conflict(s) found:"
        return "\n".join([summary, *(f"  - {conflict}" for conflict in conflicts)])

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
