"""Testing ground: verify the PawPal scheduling logic end-to-end in the terminal."""

from pawpal_system import Owner, Pet, Task, Planner, Priority, Frequency


def main() -> None:
    # --- Create an owner and set their availability window ---
    owner = Owner(name="Amarachi", preferences="Morning person, prefers walks early")
    owner.set_available_time("07:00", "20:00")

    # --- Create at least two pets ---
    rex = Pet(name="Rex", species="Dog", age=4, health_notes="Needs joint supplement")
    luna = Pet(name="Luna", species="Cat", age=2)

    owner.add_pet(rex)
    owner.add_pet(luna)

    # --- Add at least three tasks with different times to the pets ---
    rex.add_task(Task(
        title="Morning walk",
        category="Exercise",
        duration_minutes=30,
        priority=Priority.HIGH,
        preferred_time="07:30",
        frequency=Frequency.DAILY,
    ))
    rex.add_task(Task(
        title="Dinner",
        category="Feeding",
        duration_minutes=15,
        priority=Priority.MEDIUM,
        preferred_time="18:00",
        frequency=Frequency.DAILY,
    ))
    luna.add_task(Task(
        title="Feed & fresh water",
        category="Feeding",
        duration_minutes=10,
        priority=Priority.HIGH,
        preferred_time="08:00",
        frequency=Frequency.DAILY,
    ))
    luna.add_task(Task(
        title="Litter box cleaning",
        category="Hygiene",
        duration_minutes=10,
        priority=Priority.LOW,
        preferred_time="12:00",
        frequency=Frequency.DAILY,
    ))

    # --- Build the plan and print Today's Schedule ---
    planner = Planner(owner=owner)
    plan = planner.generate_plan()

    print("=" * 40)
    print("TODAY'S SCHEDULE")
    print("=" * 40)
    for item in plan:
        print(item)
    print("=" * 40)

    # Plain-language explanation from the planner as a bonus sanity check.
    print()
    print(planner.explain_plan())


if __name__ == "__main__":
    main()
