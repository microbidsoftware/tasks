from info_panel_manager import InfoPanelManager

def test_info_panel_logic():
    print("Testing Info Panel Logic...")
    
    # Mock tasks with hierarchy
    tasks = [
        {
            'id': 1,
            'title': 'Parent (High, #work)',
            'parent_id': None,
            'status': 'pending',
            'time_minutes': 10,
            'importance': 'Important',
            'tags': [{'name': 'work'}]
        },
        {
            'id': 2,
            'title': 'Child of 1 (Medium, #home)',
            'parent_id': 1,
            'status': 'pending',
            'time_minutes': 20,
            'importance': 'Medium',
            'tags': [{'name': 'home'}]
        },
        {
            'id': 3,
            'title': 'Completed Child of 1',
            'parent_id': 1,
            'status': 'completed',
            'time_minutes': 30,
            'importance': 'Normal',
            'tags': []
        },
        {
            'id': 4,
            'title': 'Independent (Normal)',
            'parent_id': None,
            'status': 'pending',
            'time_minutes': 5,
            'importance': None,
            'tags': []
        }
    ]
    
    stats = InfoPanelManager.calculate_stats(tasks)
    
    print(f"Stats: {stats}")
    
    # Assertions
    # Total time should be 10 (Task 1) + 20 (Task 2) + 5 (Task 4) = 35
    assert stats['total_time'] == 35
    
    # Importance summary
    # Important: Task 1 (10) + Task 2 (20 inherited) = 30
    assert stats['importance_summary']['Important'] == 30
    # Medium: Task 2 (20) = 20
    assert stats['importance_summary']['Medium'] == 20
    # Normal: Task 4 (5) = 5. Task 3 is completed, Task 1/2 have other importances.
    assert stats['importance_summary']['Normal'] == 5
    
    # Tag summary
    # #work: Task 1 (10) + Task 2 (20 inherited) = 30
    assert stats['tag_summary']['work'] == 30
    # #home: Task 2 (20) = 20
    assert stats['tag_summary']['home'] == 20
    
    print("\nInfo Panel Logic verification passed!")

if __name__ == "__main__":
    test_info_panel_logic()
    
