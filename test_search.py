from search_manager import SearchManager

def test_search_logic():
    print("Testing Search and Filtering Logic...")
    
    # Mock tasks with hierarchy
    tasks = [
        {
            'id': 1,
            'title': 'Project Alpha',
            'parent_id': None,
            'importance': 'Important',
            'tags': [{'name': 'work'}]
        },
        {
            'id': 2,
            'title': 'Subtask Beta',
            'parent_id': 1,
            'importance': 'Medium',
            'tags': [{'name': 'home'}]
        },
        {
            'id': 3,
            'title': 'Urgent Fix',
            'parent_id': None,
            'importance': 'Important',
            'tags': [{'name': 'urgent'}]
        },
        {
            'id': 4,
            'title': 'Misc Task',
            'parent_id': None,
            'importance': 'Normal',
            'tags': []
        }
    ]
    
    # 1. Test search by title
    print("\n1. Searching for 'Beta'...")
    results = SearchManager.filter_tasks(tasks, search_query='Beta')
    ids = {t['id'] for t in results}
    # Should include 2 (match) AND 1 (parent of 2)
    assert 2 in ids
    assert 1 in ids
    print(f"Results for 'Beta': {ids}")

    # 2. Test filter by tag
    print("\n2. Filtering by tag 'urgent'...")
    results = SearchManager.filter_tasks(tasks, tag_filter='urgent')
    ids = {t['id'] for t in results}
    assert 3 in ids
    assert len(ids) == 1
    print(f"Results for tag 'urgent': {ids}")

    # 3. Test filter by importance
    print("\n3. Filtering by importance 'Important'...")
    results = SearchManager.filter_tasks(tasks, importance_filter='Important')
    ids = {t['id'] for t in results}
    assert 1 in ids
    assert 3 in ids
    # Task 2 should NOT be in results if it doesn't match and isn't an ancestor of a match
    assert 2 not in ids
    print(f"Results for importance 'Important': {ids}")

    # 4. Combine filter and search
    print("\n4. Searching for 'Project' with tag 'work'...")
    results = SearchManager.filter_tasks(tasks, search_query='Project', tag_filter='work')
    ids = {t['id'] for t in results}
    assert 1 in ids
    assert len(ids) == 1
    print(f"Combined results: {ids}")

    print("\nSearch Logic verification passed!")

if __name__ == "__main__":
    test_search_logic()
