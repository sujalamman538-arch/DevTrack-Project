from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# --- 1. Core Blueprints (Models) ---

class BaseEntity:
    def validate(self):
        raise NotImplementedError("Subclasses must implement the validate method.")

class Reporter(BaseEntity):
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email

    def validate(self):
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
        return f"{self.title} - {self.priority} priority"

    def validate(self):
        if not self.title:
            raise ValueError("Title cannot be empty")
        if self.status not in self.ALLOWED_STATUSES:
            raise ValueError(f"Status must be one of {self.ALLOWED_STATUSES}")
        if self.priority not in self.ALLOWED_PRIORITIES:
            raise ValueError(f"Priority must be one of {self.ALLOWED_PRIORITIES}")

class CriticalIssue(Issue):
    def describe(self):
        return f"{self.title.upper()} - CRITICAL ACTION REQUIRED"

class LowPriorityIssue(Issue):
    def describe(self):
        return f"{self.title} - low priority, handle when free"


# --- 2. In-Memory Storage Databases ---
reporters_db = []
issues_db = []

# Seed initial mock data so the list isn't empty when you refresh the browser!
reporters_db.append(Reporter(id=1, name="Alice Smith", email="alice@airtribe.live"))


# --- 3. Production Django API View Endpoints ---

def get_all_reporters_view(request):
    """GET /api/reporters/"""
    data = [{"id": r.id, "name": r.name, "email": r.email} for r in reporters_db]
    return JsonResponse(data, safe=False, status=200)

def get_single_reporter_view(request):
    """GET /api/reporters/?id=1"""
    reporter_id_str = request.GET.get('id')
    if not reporter_id_str:
        return JsonResponse({"error": "Missing id parameter"}, status=400)
        
    try:
        reporter_id = int(reporter_id_str)
    except ValueError:
        return JsonResponse({"error": "Invalid id format"}, status=400)
        
    for r in reporters_db:
        if r.id == reporter_id:
            return JsonResponse({"id": r.id, "name": r.name, "email": r.email}, status=200)
            
    return JsonResponse({"error": "Reporter not found"}, status=404)

@csrf_exempt
def create_issue_view(request):
    """POST /api/issues/"""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)
        
    reporter_id = data.get('reporter_id')
    
    # Validate if reporter exists
    if not any(r.id == reporter_id for r in reporters_db):
        return JsonResponse({"error": "Reporter not found"}, status=404)

    priority = data.get('priority', '').lower()

    # Polymorphic Class Instantiation
    if priority == 'critical':
        issue = CriticalIssue(data.get('id'), data.get('title'), data.get('description'), data.get('status'), data.get('priority'), reporter_id)
    elif priority == 'low':
        issue = LowPriorityIssue(data.get('id'), data.get('title'), data.get('description'), data.get('status'), data.get('priority'), reporter_id)
    else:
        issue = Issue(data.get('id'), data.get('title'), data.get('description'), data.get('status'), data.get('priority'), reporter_id)

    # Validation check
    try:
        issue.validate()
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    issues_db.append(issue)
    return JsonResponse({"message": "Issue created successfully", "description": issue.describe()}, status=201)

def get_issues_view(request):
    """GET /api/issues/ or GET /api/issues/?status=open or GET /api/issues/?id=101"""
    issue_id_str = request.GET.get('id')
    if issue_id_str:
        try:
            issue_id = int(issue_id_str)
        except ValueError:
            return JsonResponse({"error": "Invalid id format"}, status=400)
            
        for issue in issues_db:
            if issue.id == issue_id:
                return JsonResponse({"id": issue.id, "title": issue.title, "description": issue.description, "status": issue.status, "priority": issue.priority, "reporter_id": issue.reporter_id}, status=200)
        return JsonResponse({"error": "Issue not found"}, status=404)

    status_filter = request.GET.get('status')
    results = []
    for issue in issues_db:
        if status_filter and issue.status != status_filter.lower():
            continue
        results.append({"id": issue.id, "title": issue.title, "description": issue.description, "status": issue.status, "priority": issue.priority, "reporter_id": issue.reporter_id})
        
    return JsonResponse(results, safe=False, status=200)