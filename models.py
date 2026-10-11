class BaseEntity:
    """Abstract base class that forces all models to implement a validation method."""
    def validate(self):
        raise NotImplementedError("Subclasses must implement the validate method.")


class Reporter(BaseEntity):
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email

    def validate(self):
        # Validation checks based on project constraints
        if not self.name:
            raise ValueError("Name cannot be empty")
        if "@" not in self.email:
            raise ValueError("Invalid email layout")


class Issue(BaseEntity):
    ALLOWED_STATUSES = {"open", "in-progress", "resolved"}
    ALLOWED_PRIORITIES = {"low", "medium", "high", "critical"}

    def __init__(self, id: int, title: str, description: str, status: str, priority: str, reporter_id: int):
        self.id = id
        self.title = title
        self.description = description
        self.status = status.lower() if status else ""
        self.priority = priority.lower() if priority else ""
        self.reporter_id = reporter_id

    def describe(self):
        """Polymorphic method to summarize the issue."""
        return f"{self.title} - {self.priority} priority"

    def validate(self):
        if not self.title:
            raise ValueError("Title cannot be empty")
        if self.status not in self.ALLOWED_STATUSES:
            raise ValueError(f"Status must be one of {self.ALLOWED_STATUSES}")
        if self.priority not in self.ALLOWED_PRIORITIES:
            raise ValueError(f"Priority must be one of {self.ALLOWED_PRIORITIES}")


# --- Subclasses with Overridden Polymorphic Behavior ---

class CriticalIssue(Issue):
    def describe(self):
        # Custom logic for critical tracking tasks
        return f"{self.title.upper()} - CRITICAL ACTION REQUIRED"


class LowPriorityIssue(Issue):
    def describe(self):
        # Custom logic for lower level backend tracker updates
        return f"{self.title} - low priority, handle when free"
        