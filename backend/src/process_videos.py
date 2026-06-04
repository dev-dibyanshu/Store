"""Process store videos and generate events."""

import json
import sys
from pathlib import Path
from datetime import datetime
from cv.video_processor import VideoProcessor


def define_store1_zones():
    """Define zones for Store 1 based on layout."""
    return [
        {
            'id': 'STORE1_Z01_LEFT_SHELF',
            'name': 'Left Product Shelf',
            'type': 'SHELF',
            'polygon': [(100, 200), (400, 200), (400, 600), (100, 600)],
            'is_revenue': True
        },
        {
            'id': 'STORE1_Z02_CENTER',
            'name': 'Center Display Area',
            'type': 'DISPLAY',
            'polygon': [(450, 150), (800, 150), (800, 650), (450, 650)],
            'is_revenue': True
        },
        {
            'id': 'STORE1_Z03_BILLING',
            'name': 'Billing Counter',
            'type': 'BILLING',
            'polygon': [(850, 200), (1150, 200), (1150, 500), (850, 500)],
            'is_revenue': True
        }
    ]


def define_store2_zones():
    """Define zones for Store 2 based on layout."""
    return [
        {
            'id': 'STORE2_Z01_ENTRY',
            'name': 'Entry Zone',
            'type': 'ENTRY',
            'polygon': [(50, 100), (300, 100), (300, 400), (50, 400)],
            'is_revenue': False
        },
        {
            'id': 'STORE2_Z02_MAIN_DISPLAY',
            'name': 'Main Display',
            'type': 'DISPLAY',
            'polygon': [(350, 150), (750, 150), (750, 550), (350, 550)],
            'is_revenue': True
        },
        {
            'id': 'STORE2_Z03_BILLING',
            'name': 'Billing Area',
            'type': 'BILLING',
            'polygon': [(800, 200), (1100, 200), (1100, 500), (800, 500)],
            'is_revenue': True
        }
    ]


def process_store1():
    """Process Store 1 videos."""
    print("\n" + "="*60)
    print("PROCESSING STORE 1")
    print("="*60)
    
    info_path = Path("../Info")
    store1_path = info_path / "Store 1"
    
    zones = define_store1_zones()
    
    video_configs = [
        {
            'path': str(store1_path / "CAM 3 - entry.mp4"),
            'camera_id': 'STORE1_CAM3_ENTRY',
            'zones': zones
        },
        {
            'path': str(store1_path / "CAM 1 - zone.mp4"),
            'camera_id': 'STORE1_CAM1_ZONE',
            'zones': zones
        },
        {
            'path': str(store1_path / "CAM 2 - zone.mp4"),
            'camera_id': 'STORE1_CAM2_ZONE',
            'zones': zones
        },
        {
            'path': str(store1_path / "CAM 5 - billing.mp4"),
            'camera_id': 'STORE1_CAM5_BILLING',
            'zones': zones
        }
    ]
    
    processor = VideoProcessor("store_1", sample_every_n_frames=10)
    
    # Process videos - process full videos for accurate counting
    from datetime import timedelta
    start_time = datetime.utcnow() - timedelta(hours=2)
    events = processor.process_store_videos(
        video_configs,
        start_time=start_time,
        max_frames_per_video=None  # Process full videos
    )
    
    return events


def process_store2():
    """Process Store 2 videos."""
    print("\n" + "="*60)
    print("PROCESSING STORE 2")
    print("="*60)
    
    info_path = Path("../Info")
    store2_path = info_path / "Store 2"
    
    zones = define_store2_zones()
    
    video_configs = [
        {
            'path': str(store2_path / "entry 1.mp4"),
            'camera_id': 'STORE2_CAM1_ENTRY',
            'zones': zones
        },
        {
            'path': str(store2_path / "entry 2.mp4"),
            'camera_id': 'STORE2_CAM2_ENTRY',
            'zones': zones
        },
        {
            'path': str(store2_path / "zone.mp4"),
            'camera_id': 'STORE2_CAM3_ZONE',
            'zones': zones
        },
        {
            'path': str(store2_path / "billing_area.mp4"),
            'camera_id': 'STORE2_CAM4_BILLING',
            'zones': zones
        }
    ]
    
    processor = VideoProcessor("store_2", sample_every_n_frames=10)
    
    # Process videos - process full videos for accurate counting
    from datetime import timedelta
    start_time = datetime.utcnow() - timedelta(hours=1, minutes=30)
    events = processor.process_store_videos(
        video_configs,
        start_time=start_time,
        max_frames_per_video=None  # Process full videos
    )
    
    return events


def main():
    """Main processing function."""
    print("Store Intelligence CV Pipeline")
    print("Processing videos from Store 1 and Store 2...")
    
    # Process both stores
    all_events = []
    
    try:
        store1_events = process_store1()
        all_events.extend(store1_events)
        print(f"\nStore 1: Generated {len(store1_events)} events")
    except Exception as e:
        print(f"Error processing Store 1: {e}")
    
    try:
        store2_events = process_store2()
        all_events.extend(store2_events)
        print(f"Store 2: Generated {len(store2_events)} events")
    except Exception as e:
        print(f"Error processing Store 2: {e}")
    
    # Save events
    output_file = Path("../Info/cv_generated_events.jsonl")
    with open(output_file, 'w') as f:
        for event in all_events:
            f.write(json.dumps(event) + '\n')
    
    print(f"\n{'='*60}")
    print(f"COMPLETE: {len(all_events)} total events generated")
    print(f"Output: {output_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
