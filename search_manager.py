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
                due_at = task.get('due_at')
                if not due_at:
                    match = False
                else:
                    if isinstance(due_at, str):
                        try:
                            due_at = datetime.fromisoformat(due_at.replace(' ', 'T'))
                        except ValueError:
                            match = False
                    
                    if match:
                        now = datetime.now()
                        today_start = datetime(now.year, now.month, now.day)
                        tomorrow_start = today_start + timedelta(days=1)
                        day_after_tomorrow = today_start + timedelta(days=2)
                        
                        # Next Week means "not the current week but the next one"
                        # Next Monday is the start of the next week
                        # Python weekday: Mon=0, ..., Sun=6
                        days_to_next_monday = 7 - now.weekday()
                        next_week_start = today_start + timedelta(days=days_to_next_monday)
                        next_week_end = next_week_start + timedelta(days=7)

                        # "This week" means next 7 days
                        seven_days_later = now + timedelta(days=7)

                        if effective_period == 'today':
                            if not (due_at < tomorrow_start): match = False
                        elif effective_period == 'tomorrow':
                            if not (tomorrow_start <= due_at < day_after_tomorrow): match = False
                        elif effective_period == 'this_week':
                            if not (now <= due_at < seven_days_later): match = False
                        elif effective_period == 'next_week':
                            if not (next_week_start <= due_at < next_week_end): match = False

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
            
            return [tasks_map[tid] for tid in expanded_set]

        return []
