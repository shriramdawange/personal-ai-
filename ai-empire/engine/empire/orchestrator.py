import time
from pathlib import Path
from .agents import ceo_plan, execute_specialist, quality_review, revise_output
from .config import settings
from .db import connect, event, get_task, init_db, list_tasks, update_task

class Orchestrator:
    def __init__(self):
        init_db()
        settings.workspace.mkdir(parents=True, exist_ok=True)

    def run_task(self, task_id: int):
        task=get_task(task_id)
        if not task: raise ValueError(f'Task {task_id} not found')
        if task['status'] == 'succeeded': return task
        update_task(task_id,status='running',error=None)
        try:
            event(task_id,'CEO','plan_started',task['title'])
            plan=ceo_plan(task['title'],task['description'])
            event(task_id,'CEO','plan_ready',plan)
            output=execute_specialist(task['title'],task['description'],plan)
            event(task_id,'Delivery specialist','draft_ready',output)
            review=quality_review(task['title'],task['description'],plan,output)
            event(task_id,'QA','review_complete',review)
            if 'QA_STATUS: REVISE' in review.upper():
                for attempt in range(settings.max_revisions):
                    output=revise_output(task['title'],task['description'],plan,output,review)
                    event(task_id,'Delivery specialist','revision_ready',f'Revision {attempt+1}:\n{output}')
                    review=quality_review(task['title'],task['description'],plan,output)
                    event(task_id,'QA','revision_review',review)
                    if 'QA_STATUS: PASS' in review.upper(): break
            stamp=time.strftime('%Y%m%d-%H%M%S')
            safe=''.join(c.lower() if c.isalnum() else '-' for c in task['title'])[:48].strip('-') or 'task'
            output_path=settings.workspace / f'task-{task_id}-{safe}-{stamp}.md'
            output_path.write_text(f'# {task[\'title\']}\n\n## CEO plan\n\n{plan}\n\n## Deliverable\n\n{output}\n\n## QA review\n\n{review}\n',encoding='utf-8')
            status='succeeded' if 'QA_STATUS: PASS' in review.upper() else 'needs_review'
            update_task(task_id,status=status,result_path=str(output_path))
            event(task_id,'Orchestrator','task_finished',f'status={status}; artifact={output_path}')
            return get_task(task_id)
        except Exception as exc:
            update_task(task_id,status='failed',error=str(exc))
            event(task_id,'Orchestrator','task_failed',str(exc))
            raise

    def run_next(self):
        queued=[t for t in list_tasks(100) if t['status']=='queued']
        if not queued: return None
        return self.run_task(queued[-1]['id'])

    def serve(self, once=False):
        print('AI Empire worker started. Stop with Ctrl+C. Local model:', settings.ollama_model)
        while True:
            try:
                task=self.run_next()
                if task: print(f"Task #{task['id']}: {task['status']} {task.get('result_path') or task.get('error') or ''}")
                elif once: return
            except Exception as exc:
                print('Worker error:',exc)
            if once: return
            time.sleep(settings.poll_seconds)
