class InfoPanelManager:
    """
    Manages logic for calculating statistics to be displayed in the Information Panel.
    Separated from the main business logic to keep the codebase clean.
    """

    @staticmethod
    def calculate_stats(all_tasks):
        """
        Calculates total time, time by importance, and time by tag for a list of tasks.
        Includes subtask time in parent categories (inheritance).
        """
        stats = {
            'total_time': 0,
            'importance_summary': {},  # { 'High': 30, 'Medium': 20 ... }
            'tag_summary': {}          # { 'work': 50, 'home': 10 ... }
        }

        # Build a map for quick ancestor lookup if not already provided
        tasks_map = {task['id']: task for task in all_tasks}

        # Importance levels we expect
        default_importances = ['Important', 'Medium', 'Normal']
        for imp in default_importances:
            stats['importance_summary'][imp] = 0

        for task in all_tasks:
            # Global total: Only sum work that is NOT completed
            if task.get('status') == 'completed':
                continue

            own_time = task.get('time_minutes', 0) or 0
            stats['total_time'] += own_time

            # Calculate "Active Categories" for this task (Direct + Ancestors)
            active_importances = set()
            active_tags = set()

            curr = task
            while curr:
                # Importance
                imp = curr.get('importance')
                if imp and imp != '':
                    active_importances.add(imp)
                
                # Tags
                tags = curr.get('tags', [])
                for tag_obj in tags:
                    tag_name = tag_obj.get('name')
                    if tag_name:
                        active_tags.add(tag_name)
                
                # Move to parent
                parent_id = curr.get('parent_id')
                curr = tasks_map.get(parent_id) if parent_id else None

            # If no importance found in heritage, it's effectively 'Normal'
            if not active_importances:
                active_importances.add('Normal')

            # Add own_time to all active buckets
            for imp in active_importances:
                stats['importance_summary'][imp] = stats['importance_summary'].get(imp, 0) + own_time
            
            for tag in active_tags:
                stats['tag_summary'][tag] = stats['tag_summary'].get(tag, 0) + own_time

        # Sort tag summary by time descending
        stats['tag_summary'] = dict(sorted(stats['tag_summary'].items(), key=lambda item: item[1], reverse=True))

        return stats
