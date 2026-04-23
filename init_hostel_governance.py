"""
One-time initializer for Hostel Governance module
Safe to run multiple times (CREATE TABLE IF NOT EXISTS)
"""

from modules.hostel_governance.models import init_governance_tables

def main():
    init_governance_tables()
    print("✅ Hostel Governance tables initialized successfully.")

if __name__ == "__main__":
    main()
