import sqlite3
import json

# SQL statements for creating all tables
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS revisions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    master_spec TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS innovations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    approval_count INTEGER DEFAULT 0,
    rejection_count INTEGER DEFAULT 0,
    acceptance_rate REAL DEFAULT 0.0,
    business_impact TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id TEXT PRIMARY KEY,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode TEXT NOT NULL,
    success_rate REAL NOT NULL,
    average_latency REAL NOT NULL,
    total_cost REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_results (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    prompt_id TEXT NOT NULL,
    prompt_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    latency REAL NOT NULL,
    cost REAL NOT NULL,
    validation_errors TEXT,
    repair_count INTEGER DEFAULT 0,
    FOREIGN KEY (run_id) REFERENCES eval_runs(id)
);

-- PHASE 3 TABLES --

CREATE TABLE IF NOT EXISTS industry_patterns (
    category TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    description TEXT NOT NULL,
    business_value TEXT NOT NULL,
    recommendation_reason TEXT NOT NULL,
    PRIMARY KEY (category, feature_name)
);

CREATE TABLE IF NOT EXISTS community_innovations (
    innovation_id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    description TEXT NOT NULL,
    approval_count INTEGER DEFAULT 0,
    rejection_count INTEGER DEFAULT 0,
    acceptance_rate REAL DEFAULT 0.0,
    impact_score REAL DEFAULT 0.0,
    times_suggested INTEGER DEFAULT 0,
    suggested_with TEXT NOT NULL,
    innovation_origin TEXT NOT NULL DEFAULT 'community',
    last_approved_at TEXT,
    last_rejected_at TEXT,
    average_confidence REAL DEFAULT 0.0,
    community_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS approval_history (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    item_type TEXT NOT NULL,
    item_name TEXT NOT NULL,
    status TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS blueprint_modifications (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    action TEXT NOT NULL,
    component_type TEXT NOT NULL,
    name TEXT NOT NULL,
    details TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS architecture_memory (
    project_id TEXT PRIMARY KEY,
    prompt TEXT NOT NULL,
    domain TEXT NOT NULL,
    subdomain TEXT NOT NULL,
    dna TEXT NOT NULL,
    actors TEXT NOT NULL,
    entities TEXT NOT NULL,
    workflows TEXT NOT NULL,
    business_rules TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pattern_repository (
    domain TEXT PRIMARY KEY,
    common_actors TEXT NOT NULL,
    common_entities TEXT NOT NULL,
    common_workflows TEXT NOT NULL,
    common_rules TEXT NOT NULL,
    evidence_count INTEGER DEFAULT 0
);
"""

# Seed data for community innovations repository
SEED_INNOVATIONS = [
    {
        "id": "inn_001",
        "name": "AI Trainer Matching",
        "description": "Matches users with gym trainers using a dynamic preferences and goals questionnaire.",
        "category": "Gym",
        "approval_count": 89,
        "rejection_count": 11,
        "acceptance_rate": 0.89,
        "business_impact": "Improves member onboarding conversion by 15% and increases class bookings."
    },
    {
        "id": "inn_002",
        "name": "Smart Class Waitlist auto-fill",
        "description": "Automatically books waitlisted users into a fitness class when another user cancels, optimized by attendance history score.",
        "category": "Gym",
        "approval_count": 75,
        "rejection_count": 10,
        "acceptance_rate": 0.88,
        "business_impact": "Reduces empty class slots by 22% and increases booking satisfaction."
    },
    {
        "id": "inn_003",
        "name": "Predictive Stock Alert",
        "description": "Monitors stock quantities and uses historical sales patterns to warn administrators before stock depletion.",
        "category": "E-commerce",
        "approval_count": 92,
        "rejection_count": 8,
        "acceptance_rate": 0.92,
        "business_impact": "Reduces out-of-stock occurrences by 35% and maintains steady sales pipelines."
    },
    {
        "id": "inn_004",
        "name": "Dynamic Subtask Progress Visualizer",
        "description": "Computes completion percentages based on subtask weights and displays progress bars across parent workflows.",
        "category": "Task Manager",
        "approval_count": 81,
        "rejection_count": 19,
        "acceptance_rate": 0.81,
        "business_impact": "Enhances visibility of long-running operations and increases productivity."
    }
]

# Phase 3 Industry Pattern seed data
SEED_INDUSTRY_PATTERNS = [
    ("Gym", "Membership Management", "Tracks member registrations, subscription plans, renewals, and cancellations.", "Reduces member churn and automates billing cycles.", "Standard operational core for any fitness facility app."),
    ("Gym", "Attendance Tracking", "Enables QR code scanner or check-in kiosk at facility entrance.", "Provides metrics on gym usage and peak slot occupancy.", "Crucial to optimize staff scheduling and class capacities."),
    ("Gym", "Class Scheduling & Booking", "Allows members to view calendars, book spots, and cancel class reservations.", "Maintains even attendance and prevents classroom overcrowding.", "Drives overall class occupancy and scheduling automation."),
    ("Gym", "Trainer Assignment", "Assigns certified instructors to specific fitness classes and personal training sessions.", "Improves staff allocation and tracks trainer-driven bookings.", "Important for payroll tracking and trainer class feedback."),
    
    ("CRM", "Contact Management", "Maintains clean directory profiles of prospects and clients, logging communications.", "Provides a 360-degree timeline of client interactions.", "The ultimate baseline feature of client management."),
    ("CRM", "Lead Pipeline Tracking", "Visualizes prospect deals moving through sequential conversion stages.", "Increases conversion velocity by alerting agents to stalled deals.", "Essential to forecast revenues and track sales efficiency."),
    ("CRM", "Follow-up Reminders", "Auto-schedules prompts for sales agents to contact prospects based on last touchpoint.", "Ensures high contact response rates and prevents deal slippage.", "Improves client satisfaction and follow-up reliability."),
    
    ("School", "Class Timetable Scheduling", "Orchestrates course schedules, teacher assignments, and classroom bookings.", "Prevents time slots and physical room reservation conflicts.", "Core structural system for school day coordination."),
    ("School", "Student Grade Reporting", "Enables teachers to record exam results and report transcripts directly to student portals.", "Streamlines academic reports compilation and student progress visibility.", "Required educational performance tracking mechanism."),
    ("School", "Homework Assignment Portal", "Allows teachers to post project specifications and students to upload homework files.", "Replaces paper handout workflows with centralized grading digital folders.", "Crucial for remote studies and digital coursework tracking."),

    ("Hospital", "Patient Appointment Scheduler", "Manages scheduling matching doctors, clinics, and patient requests.", "Reduces queue wait times and optimizes doctor clinic hours.", "Primary intake mechanism for patient workflows."),
    ("Hospital", "Electronic Medical Records", "Stores encrypted secure records of clinical notes, patient history, and vitals.", "Enables immediate diagnostics access across department specialists.", "Core regulatory and HIPAA baseline record keeper."),
    ("Hospital", "E-Prescription Dispenser", "Sends digital prescriptions directly to patients and participating pharmacies.", "Eliminates handwriting translation errors and speeds medication access.", "Crucial safety step in pharmaceutical compliance."),

    ("Inventory", "Stock Levels Tracker", "Logs stock quantities, serial IDs, and bin location assignments.", "Prevents stockouts and tracking loss across locations.", "Crucial to maintain continuous supply flow."),
    ("Inventory", "Supplier Catalog directory", "Keeps profiles, pricing books, and lead time profiles for wholesale vendors.", "Speeds up sourcing cycles and purchase orders creation.", "Essential for supply chain procurement management.")
]

# Phase 3 Community Innovations seed data
SEED_COMMUNITY_INNOVATIONS = [
    ("inn_c01", "Gym", "AI Trainer Matching", "Matches users with gym trainers using a dynamic preferences and goals questionnaire.", 89, 11, 0.89, 9.1, 100, '["Class Scheduling & Booking", "Trainer Assignment"]', "community", 8.10),
    ("inn_c02", "Gym", "Smart Class Waitlist auto-fill", "Automatically books waitlisted users into a fitness class when another user cancels, optimized by attendance history score.", 75, 10, 0.88, 8.7, 85, '["Class Scheduling & Booking", "Attendance Tracking"]', "community", 7.66),
    ("inn_c03", "CRM", "Lead Score Predictor", "Analyzes lead profile properties and communication logs to estimate probability of closing.", 90, 10, 0.90, 9.3, 120, '["Lead Pipeline Tracking", "Contact Management"]', "community", 8.37),
    ("inn_c04", "School", "Dynamic Progress Visualizer", "Computes course completion percentages and renders them as animated progress bars.", 81, 19, 0.81, 8.0, 60, '["Homework Assignment Portal", "Student Grade Reporting"]', "industry", 6.48),
    ("inn_c05", "Inventory", "Predictive Stock Alert", "Monitors stock quantities and uses historical sales patterns to warn administrators before stock depletion.", 92, 8, 0.92, 9.5, 150, '["Stock Levels Tracker", "Supplier Catalog directory"]', "industry", 8.74)
]

SEED_PATTERN_REPOS = [
    (
        "Gym Management",
        json.dumps([{"name": "GymMember", "frequency": 1.0}, {"name": "GymTrainer", "frequency": 1.0}, {"name": "Admin", "frequency": 0.9}]),
        json.dumps([{"name": "Member", "frequency": 1.0}, {"name": "Trainer", "frequency": 1.0}, {"name": "ClassSchedule", "frequency": 0.95}, {"name": "ClassBooking", "frequency": 0.95}]),
        json.dumps([{"name": "Class Booking", "frequency": 1.0}, {"name": "Membership Purchase", "frequency": 1.0}]),
        json.dumps([{"rule": "Members can book a maximum of 3 classes per day.", "frequency": 0.9}, {"rule": "Cancellations must be done at least 2 hours before class starts.", "frequency": 0.85}]),
        10
    ),
    (
        "CRM Application",
        json.dumps([{"name": "SalesAgent", "frequency": 1.0}, {"name": "SalesManager", "frequency": 0.9}]),
        json.dumps([{"name": "Customer", "frequency": 1.0}, {"name": "Lead", "frequency": 1.0}, {"name": "InteractionLog", "frequency": 0.9}, {"name": "Deal", "frequency": 0.8}]),
        json.dumps([{"name": "Lead Conversion Flow", "frequency": 1.0}, {"name": "Follow Up Flow", "frequency": 1.0}]),
        json.dumps([{"rule": "Only managers can mark deals as Deleted.", "frequency": 0.9}, {"rule": "Lead assignments require active sales agents.", "frequency": 0.85}]),
        10
    ),
    (
        "School Management",
        json.dumps([{"name": "Student", "frequency": 1.0}, {"name": "Teacher", "frequency": 1.0}, {"name": "Admin", "frequency": 0.9}, {"name": "Parent", "frequency": 0.7}]),
        json.dumps([{"name": "Course", "frequency": 1.0}, {"name": "Classroom", "frequency": 0.9}, {"name": "Grade", "frequency": 1.0}, {"name": "Assignment", "frequency": 1.0}, {"name": "Attendance", "frequency": 0.8}]),
        json.dumps([{"name": "Class Timetable Scheduling", "frequency": 0.9}, {"name": "Student Grade Reporting", "frequency": 1.0}, {"name": "Homework Assignment Portal", "frequency": 0.95}]),
        json.dumps([{"rule": "Grades can only be entered by the assigned course teacher.", "frequency": 0.95}, {"rule": "Class schedule changes must be approved by the administrator.", "frequency": 0.9}]),
        10
    ),
    (
        "Healthcare",
        json.dumps([{"name": "Patient", "frequency": 1.0}, {"name": "Doctor", "frequency": 1.0}, {"name": "Admin", "frequency": 0.9}, {"name": "Nurse", "frequency": 0.8}]),
        json.dumps([{"name": "Patient", "frequency": 1.0}, {"name": "Doctor", "frequency": 1.0}, {"name": "Appointment", "frequency": 1.0}, {"name": "MedicalRecord", "frequency": 0.95}, {"name": "Prescription", "frequency": 0.9}]),
        json.dumps([{"name": "Schedule Appointment", "frequency": 1.0}, {"name": "Consultation", "frequency": 1.0}, {"name": "Prescription Management", "frequency": 0.9}]),
        json.dumps([{"rule": "Medical records access must be logged for auditing.", "frequency": 1.0}, {"rule": "Prescriptions can only be written by certified doctors.", "frequency": 0.95}]),
        10
    ),
    (
        "Inventory Management",
        json.dumps([{"name": "InventoryManager", "frequency": 1.0}, {"name": "Supplier", "frequency": 0.8}, {"name": "ProcurementOfficer", "frequency": 0.9}]),
        json.dumps([{"name": "Item", "frequency": 1.0}, {"name": "Supplier", "frequency": 0.9}, {"name": "StockLevel", "frequency": 1.0}, {"name": "PurchaseOrder", "frequency": 0.95}]),
        json.dumps([{"name": "Stock Levels Tracker", "frequency": 1.0}, {"name": "Supplier Catalog directory", "frequency": 0.9}]),
        json.dumps([{"rule": "Stock count adjustments require manager approval.", "frequency": 0.95}, {"rule": "Reorder triggers automatically when stock falls below safety levels.", "frequency": 0.9}]),
        10
    ),
    (
        "Restaurant Management",
        json.dumps([{"name": "Customer", "frequency": 1.0}, {"name": "RestaurantOwner", "frequency": 1.0}, {"name": "Staff", "frequency": 0.85}]),
        json.dumps([{"name": "Menu", "frequency": 1.0}, {"name": "MenuItem", "frequency": 1.0}, {"name": "Order", "frequency": 1.0}, {"name": "Reservation", "frequency": 0.9}, {"name": "Payment", "frequency": 0.95}, {"name": "Review", "frequency": 0.7}]),
        json.dumps([{"name": "Browse Menu", "frequency": 1.0}, {"name": "Place Order", "frequency": 1.0}, {"name": "Checkout", "frequency": 1.0}, {"name": "Reserve Table", "frequency": 0.85}, {"name": "Leave Review", "frequency": 0.75}]),
        json.dumps([{"rule": "Only paid orders can be fulfilled.", "frequency": 0.9}, {"rule": "Reservations require available tables.", "frequency": 0.8}, {"rule": "Refunds require manager approval.", "frequency": 0.75}]),
        10
    ),
    (
        "E-Commerce",
        json.dumps([{"name": "Buyer", "frequency": 1.0}, {"name": "Seller", "frequency": 0.9}, {"name": "Admin", "frequency": 0.9}]),
        json.dumps([{"name": "Product", "frequency": 1.0}, {"name": "Cart", "frequency": 1.0}, {"name": "Order", "frequency": 1.0}, {"name": "Payment", "frequency": 1.0}, {"name": "Shipment", "frequency": 0.85}]),
        json.dumps([{"name": "Product Search", "frequency": 1.0}, {"name": "Add to Cart", "frequency": 1.0}, {"name": "Checkout & Pay", "frequency": 1.0}, {"name": "Track Shipment", "frequency": 0.85}]),
        json.dumps([{"rule": "Orders can only ship after full payment confirmation.", "frequency": 0.95}, {"rule": "Inventory must decrement upon successful order placement.", "frequency": 0.9}]),
        10
    ),
    (
        "Marketplace Platform",
        json.dumps([{"name": "Buyer", "frequency": 1.0}, {"name": "Merchant", "frequency": 1.0}, {"name": "Moderator", "frequency": 0.8}, {"name": "Admin", "frequency": 0.9}]),
        json.dumps([{"name": "Listing", "frequency": 1.0}, {"name": "Order", "frequency": 1.0}, {"name": "Payout", "frequency": 0.9}, {"name": "Dispute", "frequency": 0.75}]),
        json.dumps([{"name": "Create Listing", "frequency": 1.0}, {"name": "Purchase Item", "frequency": 1.0}, {"name": "Escrow Release", "frequency": 0.85}, {"name": "Raise Dispute", "frequency": 0.75}]),
        json.dumps([{"rule": "Funds are held in escrow until buyer confirms receipt.", "frequency": 0.95}, {"rule": "Merchant payouts are processed weekly.", "frequency": 0.9}]),
        10
    ),
    (
        "Hospitality Management",
        json.dumps([{"name": "Guest", "frequency": 1.0}, {"name": "HotelManager", "frequency": 1.0}, {"name": "Housekeeping", "frequency": 0.8}]),
        json.dumps([{"name": "Room", "frequency": 1.0}, {"name": "Booking", "frequency": 1.0}, {"name": "Guest", "frequency": 1.0}, {"name": "Payment", "frequency": 0.95}, {"name": "CleaningLog", "frequency": 0.8}]),
        json.dumps([{"name": "Search Rooms", "frequency": 1.0}, {"name": "Book Room", "frequency": 1.0}, {"name": "Payment", "frequency": 1.0}, {"name": "Check In", "frequency": 0.9}]),
        json.dumps([{"rule": "Rooms must be vacated by checkout time.", "frequency": 0.9}, {"rule": "Booking status updates require guest check-in confirmation.", "frequency": 0.85}]),
        10
    ),
    (
        "Banking System",
        json.dumps([{"name": "Customer", "frequency": 1.0}, {"name": "BankClerk", "frequency": 0.9}, {"name": "Admin", "frequency": 0.9}]),
        json.dumps([{"name": "Account", "frequency": 1.0}, {"name": "Transaction", "frequency": 1.0}, {"name": "Card", "frequency": 0.8}, {"name": "Loan", "frequency": 0.75}]),
        json.dumps([{"name": "Transfer Funds", "frequency": 1.0}, {"name": "Deposit Cash", "frequency": 0.9}, {"name": "Approve Loan", "frequency": 0.8}]),
        json.dumps([{"rule": "Transfers above $10,000 require secondary manager approval.", "frequency": 0.98}, {"rule": "Overdraft fees apply when account balance drops below zero.", "frequency": 0.95}]),
        10
    )
]

def initialize_database(db_path: str):
    """Initializes the database schema and seeds all tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Force drop old tables to perform a clean seed migration
    cursor.execute("DROP TABLE IF EXISTS community_innovations;")
    cursor.execute("DROP TABLE IF EXISTS industry_patterns;")
    cursor.execute("DROP TABLE IF EXISTS approval_history;")
    cursor.execute("DROP TABLE IF EXISTS blueprint_modifications;")
    cursor.execute("DROP TABLE IF EXISTS revisions;")
    cursor.execute("DROP TABLE IF EXISTS projects;")
    cursor.execute("DROP TABLE IF EXISTS innovations;")
    cursor.execute("DROP TABLE IF EXISTS eval_results;")
    cursor.execute("DROP TABLE IF EXISTS eval_runs;")
    cursor.execute("DROP TABLE IF EXISTS architecture_memory;")
    cursor.execute("DROP TABLE IF EXISTS pattern_repository;")
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.executescript(CREATE_TABLES_SQL)
    conn.commit()

    # Seed old innovations table (Phase 1)
    cursor.execute("SELECT COUNT(*) FROM innovations;")
    if cursor.fetchone()[0] == 0:
        for inn in SEED_INNOVATIONS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO innovations (id, name, description, category, approval_count, rejection_count, acceptance_rate, business_impact)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (inn["id"], inn["name"], inn["description"], inn["category"], inn["approval_count"], inn["rejection_count"], inn["acceptance_rate"], inn["business_impact"])
            )
        conn.commit()

    # Seed Phase 3 Industry Patterns
    cursor.execute("SELECT COUNT(*) FROM industry_patterns;")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT OR IGNORE INTO industry_patterns (category, feature_name, description, business_value, recommendation_reason)
            VALUES (?, ?, ?, ?, ?);
            """,
            SEED_INDUSTRY_PATTERNS
        )
        conn.commit()

    # Seed Phase 3 Community Innovations
    cursor.execute("SELECT COUNT(*) FROM community_innovations;")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT OR IGNORE INTO community_innovations (
                innovation_id, category, feature_name, description, approval_count, rejection_count, 
                acceptance_rate, impact_score, times_suggested, suggested_with, innovation_origin, community_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            SEED_COMMUNITY_INNOVATIONS
        )
        conn.commit()
    
    # Seed Pattern Repository
    cursor.execute("SELECT COUNT(*) FROM pattern_repository;")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT OR IGNORE INTO pattern_repository (
                domain, common_actors, common_entities, common_workflows, common_rules, evidence_count
            )
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            SEED_PATTERN_REPOS
        )
        conn.commit()
        
    conn.close()

