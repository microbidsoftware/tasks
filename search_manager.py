class SearchManager:
    """
    Manages search and filtering logic for tasks.
    Separated from the main business logic to keep the codebase clean.
    """

    @staticmethod
    def filter_tasks(all_tasks, search_query=None, tag_filter=None, importance_filter=None, period_filter=None):
        """
        Filters the list of tasks based on the provided search query and filters.
        """
        if not search_query and not tag_filter and not importance_filter and not period_filter:
            return all_tasks

        from datetime import datetime, timedelta

        # Period Filter logic refinement
        effective_period = None if tag_filter else period_filter
        if effective_period == 'all':
            effective_period = None # "All" means no period filter
        
        filtered_ids = set()
        search_query = search_query.lower() if search_query else None
        
        for task in all_tasks:
            match = True
            
            # --- Search Query (Title, Tags, or Importance) ---
            if search_query:
                title_match = search_query in task.get('title', '').lower()
                tags_match = any(search_query in t.get('name', '').lower() for t in task.get('tags', []))
                imp = task.get('importance') or 'Normal'
                if imp == '': imp = 'Normal'
                imp_match = search_query in imp.lower()
                
                if not (title_match or tags_match or imp_match):
                    match = False

            # --- Tag Filter ---
            if match and tag_filter:
                found_tag = any(t.get('name') == tag_filter for t in task.get('tags', []))
                if not found_tag:
                    match = False

            # --- Importance Filter ---
            if match and importance_filter:
                imp = task.get('importance') or 'Normal'
                if imp == '': imp = 'Normal'
                if imp != importance_filter:
                    match = False

            # --- Period Filter ---
            if match and effective_period:
                # Decide which date to check based on status
                target_date = task.get('due_at')
                if task.get('status') == 'completed':
                     # For completed tasks, we care about when they were completed
                     target_date = task.get('completed_at')
                     # print(f"DEBUG: Checking completed task {task.get('title')} with completed_at {target_date} against {effective_period}")

                if not target_date:
                    match = False
                else:
                    if isinstance(target_date, str):
                        try:
                            target_date = datetime.fromisoformat(target_date.replace(' ', 'T'))
                        except ValueError:
                            match = False
                    
                    if match:
                        now = datetime.now()
                        today_start = datetime(now.year, now.month, now.day)
                        tomorrow_start = today_start + timedelta(days=1)
                        day_after_tomorrow = today_start + timedelta(days=2)
                        
                        days_to_next_monday = 7 - now.weekday()
                        next_week_start = today_start + timedelta(days=days_to_next_monday)
                        next_week_end = next_week_start + timedelta(days=7)

                        seven_days_later = now + timedelta(days=7)

                        if effective_period == 'today':
                            if task.get('status') == 'completed':
                                # Completed Today = [Today Start, Tomorrow Start)
                                if not (today_start <= target_date < tomorrow_start): match = False
                            else:
                                # Due Today = Overdue + Today (< Tomorrow Start)
                                if not (target_date < tomorrow_start): match = False
                        elif effective_period == 'tomorrow':
                            if not (tomorrow_start <= target_date < day_after_tomorrow): match = False
                        elif effective_period == 'this_week':
                            if not (now <= target_date < seven_days_later): match = False
                        elif effective_period == 'next_week':
                            if not (next_week_start <= target_date < next_week_end): match = False

            if match:
                filtered_ids.add(task['id'])

        # Include descendants if tag_filter is present
        if tag_filter and filtered_ids:
            expanded_set = set(filtered_ids)
            children_map = {}
            for t in all_tasks:
                pid = t.get('parent_id')
                if pid:
                    if pid not in children_map: children_map[pid] = []
                    children_map[pid].append(t['id'])
            
            def add_descendants(tid):
                for cid in children_map.get(tid, []):
                    if cid not in expanded_set:
                        expanded_set.add(cid)
                        add_descendants(cid)
            
            for tid in list(filtered_ids):
                add_descendants(tid)
            filtered_ids = expanded_set

        # To maintain tree structure for matched tasks, we should include their ancestors.
        if filtered_ids:
            expanded_set = set(filtered_ids)
            tasks_map = {t['id']: t for t in all_tasks}
            
            for tid in list(filtered_ids):
                curr = tasks_map.get(tid)
                while curr and curr.get('parent_id'):
                    pid = curr['parent_id']
                    if pid not in expanded_set:
                        parent = tasks_map.get(pid)
                        if parent:
                            expanded_set.add(pid)
                            curr = parent
                        else: break
                    else: break
            
            # Preserve original sort order from all_tasks
            return [t for t in all_tasks if t['id'] in expanded_set]

        return []
