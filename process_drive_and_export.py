"""
Script to process Google Drive link and export all data to a file
"""
import json
import os
from datetime import datetime
from Backend.DriveProcessor import process_drive_link
from Backend.SalesMemory import sales_memory_manager

def export_drive_data(drive_link: str, output_file: str = None):
    """
    Process a Google Drive link and export all extracted data to a file
    
    Args:
        drive_link: Google Drive folder or file link
        output_file: Optional output file path (default: Data/drive_data_export.json)
    """
    if not output_file:
        # Create Data directory if it doesn't exist
        os.makedirs("Data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"Data/drive_data_export_{timestamp}.json"
    
    print(f"Processing Google Drive link: {drive_link}")
    print("=" * 60)
    
    # Process the Drive link
    result = process_drive_link(drive_link)
    
    print("\nProcessing Results:")
    print(f"  Success: {result.get('success')}")
    print(f"  Files Processed: {result.get('files_processed', 0)}")
    print(f"  Entries Created: {result.get('entries_created', 0)}")
    
    if result.get('errors'):
        print(f"\n  Errors: {len(result.get('errors', []))} files had issues")
    
    # Get all memory entries related to this source
    source_name = result.get('source', 'Drive')
    # Access memory directly (it's a list)
    all_memory = sales_memory_manager.memory
    
    # Filter entries from this source
    drive_entries = [
        entry for entry in all_memory 
        if source_name in entry.get('source', '')
    ]
    
    # Prepare export data
    export_data = {
        "drive_link": drive_link,
        "processed_at": datetime.now().isoformat(),
        "processing_result": result,
        "extracted_data": {
            "total_entries": len(drive_entries),
            "entries": drive_entries
        }
    }
    
    # Export to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Data exported to: {output_file}")
    print(f"   Total entries exported: {len(drive_entries)}")
    
    return output_file

if __name__ == "__main__":
    # Test with the provided Drive link
    drive_link = "https://drive.google.com/drive/folders/1RVE5zmBVKngSKo3OUxc9WECOsPKoqymm?usp=sharing"
    export_drive_data(drive_link)

