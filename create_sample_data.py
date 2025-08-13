#!/usr/bin/env python3
"""
Create sample data to demonstrate the new DARKBO structure
"""
import sys
import os
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

from kb_api.storage import FileStorageManager
from kb_api.models import FAQEntry, KBEntry

def create_sample_data():
    """Create sample data structure"""
    print("🗂️ Creating DARKBO data structure...")
    
    # Use data/ folder as the unified home for all data
    base_dir = Path("./data")
    storage = FileStorageManager(str(base_dir))
    
    # Create ACLU project (175)
    print("\n📁 Creating ACLU Project (ID: 175)")
    storage.create_or_update_project("175", "ACLU")
    
    # Add FAQs for ACLU
    aclu_faqs = [
        FAQEntry.from_qa("175", "When are phones staffed?", "Mon–Fri 9–5 MT", source="manual"),
        FAQEntry.from_qa("175", "What is the ACLU?", "The American Civil Liberties Union is a nonprofit organization that defends civil rights and liberties.", source="manual"),
        FAQEntry.from_qa("175", "How can I contact the ACLU?", "You can reach us by phone during business hours or visit our website at aclu.org", source="manual"),
        FAQEntry.from_qa("175", "What areas does the ACLU work in?", "We work in freedom of speech, religious liberty, privacy rights, and equal protection under law", source="manual")
    ]
    
    storage.save_faqs("175", aclu_faqs)
    print(f"   ✅ Added {len(aclu_faqs)} FAQ entries")
    
    # Add KB entries for ACLU
    aclu_kb = [
        KBEntry.from_content(
            "175", 
            "About the ACLU", 
            "The American Civil Liberties Union (ACLU) is a non-profit organization founded in 1920. Our mission is to defend and preserve the individual rights and liberties guaranteed by the Constitution and laws of the United States.",
            source="upload",
            source_file="aclu_about.txt"
        ),
        KBEntry.from_content(
            "175",
            "Our Work Areas",
            "We work through litigation, advocacy, and public education to protect civil liberties. Key areas include: Freedom of speech and expression, Religious liberty, Privacy rights, Equal protection under law, Criminal justice reform, and Immigrant rights.",
            source="upload",
            source_file="aclu_work.txt"
        ),
        KBEntry.from_content(
            "175",
            "Contact Information",
            "Phone: Available Monday through Friday, 9 AM to 5 PM Mountain Time. Website: www.aclu.org. Email: info@aclu.org. For legal emergencies, contact our 24-hour hotline.",
            source="upload", 
            source_file="aclu_contact.txt"
        )
    ]
    
    storage.save_kb_entries("175", aclu_kb)
    print(f"   ✅ Added {len(aclu_kb)} KB entries")
    
    # Create ASPCA project (95)
    print("\n📁 Creating ASPCA Project (ID: 95)")
    storage.create_or_update_project("95", "ASPCA")
    
    # Add FAQs for ASPCA
    aspca_faqs = [
        FAQEntry.from_qa("95", "What does ASPCA stand for?", "American Society for the Prevention of Cruelty to Animals", source="manual"),
        FAQEntry.from_qa("95", "How can I report animal cruelty?", "Call our 24-hour hotline at 1-800-THE-ASPCA or report online at aspca.org", source="manual"),
        FAQEntry.from_qa("95", "Do you provide veterinary services?", "Yes, we operate animal hospitals and mobile clinics in several cities", source="manual")
    ]
    
    storage.save_faqs("95", aspca_faqs)
    print(f"   ✅ Added {len(aspca_faqs)} FAQ entries")
    
    # Add KB entries for ASPCA
    aspca_kb = [
        KBEntry.from_content(
            "95",
            "Mission and History",
            "The ASPCA was founded in 1866 and was the first animal welfare organization in North America. Our mission is to provide effective means for the prevention of cruelty to animals throughout the United States.",
            source="upload",
            source_file="aspca_mission.txt"
        ),
        KBEntry.from_content(
            "95",
            "Services and Programs",
            "We provide animal rescue and placement, animal health services, anti-cruelty initiatives, and community outreach programs. Our work includes disaster response, animal behavior training, and legislative advocacy.",
            source="upload",
            source_file="aspca_services.txt"
        )
    ]
    
    storage.save_kb_entries("95", aspca_kb)
    print(f"   ✅ Added {len(aspca_kb)} KB entries")
    
    # Create some sample attachments
    print("\n📎 Creating sample attachments...")
    
    # ACLU attachment
    aclu_guide_content = """
ACLU Rights Guide

Your Rights
You have the right to remain silent when questioned by police.
You have the right to refuse searches of your person, car, or home.
You have the right to an attorney during police questioning.

Know Your Rights
During police encounters:
1. Stay calm and keep your hands visible
2. You have the right to remain silent
3. You have the right to refuse consent to search
4. Ask "Am I free to go?" If yes, you can leave

Contact Us
For rights violations or legal questions, contact:
Phone: (XXX) XXX-XXXX
Email: legal@aclu.org
Website: aclu.org/know-your-rights
"""
    
    storage.save_attachment("175", "aclu_rights_guide.txt", aclu_guide_content.encode())
    
    # ASPCA attachment
    aspca_care_content = """
Animal Care Guidelines

Basic Pet Care
- Provide fresh water daily
- Feed appropriate food for your pet's age and size
- Regular veterinary checkups
- Daily exercise and mental stimulation
- Safe, comfortable shelter

Signs of Animal Abuse
- Visible injuries or wounds
- Extreme thinness or malnutrition
- Lack of shelter from weather
- Chaining or tethering for extended periods
- Aggressive behavior due to fear

Reporting Cruelty
If you witness animal cruelty:
1. Document with photos/video if safe
2. Call local animal control or police
3. Contact ASPCA hotline: 1-800-THE-ASPCA
4. Provide detailed information about location and situation
"""
    
    storage.save_attachment("95", "animal_care_guide.txt", aspca_care_content.encode())
    print("   ✅ Sample attachments created")
    
    # Display the file structure
    print("\n📊 File Structure Created:")
    print_directory_tree(base_dir)
    
    # Show project mapping
    projects = storage.load_project_mapping()
    print(f"\n📋 Project Mapping ({len(projects)} projects):")
    for pid, name in projects.items():
        print(f"   {pid} → {name}")
    
    # Show data counts
    print("\n📈 Data Summary:")
    for project_id, project_name in projects.items():
        faqs = storage.load_faqs(project_id)
        kb_entries = storage.load_kb_entries(project_id)
        print(f"   {project_name} ({project_id}): {len(faqs)} FAQs, {len(kb_entries)} KB entries")
    
    print(f"\n🎉 Data created successfully in: {base_dir.absolute()}")
    print(f"📂 All project data is now stored in the unified data/ folder")
    return base_dir

def print_directory_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
    """Print directory tree structure"""
    if current_depth > max_depth:
        return
    
    if not path.exists():
        return
    
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
    
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{current_prefix}{item.name}")
        
        if item.is_dir() and current_depth < max_depth:
            next_prefix = prefix + ("    " if is_last else "│   ")
            print_directory_tree(item, next_prefix, max_depth, current_depth + 1)

if __name__ == "__main__":
    create_sample_data()