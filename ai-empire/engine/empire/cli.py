import argparse
import json
from .db import add_task, events, init_db, list_leads, list_tasks
from .orchestrator import Orchestrator
from .research import hunt_clients
from .config import settings

def main():
    parser=argparse.ArgumentParser(prog='empire',description='AI Empire local autonomous business worker')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('init',help='Create local database and workspace')
    add=sub.add_parser('add-task',help='Queue a task for the AI team')
    add.add_argument('title'); add.add_argument('--description',default='')
    sub.add_parser('tasks',help='List tasks')
    run=sub.add_parser('run-task',help='Run one task through CEO, specialist, and QA')
    run.add_argument('task_id',type=int)
    worker=sub.add_parser('worker',help='Poll the queue and run tasks')
    worker.add_argument('--once',action='store_true',help='Process at most one queued task and exit')
    hunt=sub.add_parser('hunt-clients',help='Search public web results and draft lead notes')
    hunt.add_argument('--query',required=True,help='Specific service + client type + region query')
    hunt.add_argument('--limit',type=int,default=8)
    sub.add_parser('leads',help='List discovered leads and outreach drafts')
    ev=sub.add_parser('events',help='Show audit events for a task')
    ev.add_argument('task_id',type=int)
    args=parser.parse_args()
    init_db()
    if args.command=='init':
        settings.workspace.mkdir(parents=True,exist_ok=True); print('Database and workspace ready:',settings.db_path,settings.workspace)
    elif args.command=='add-task':
        task_id=add_task(args.title,args.description); print(f'Queued task #{task_id}: {args.title}')
    elif args.command=='tasks': print(json.dumps(list_tasks(),indent=2,ensure_ascii=False))
    elif args.command=='run-task': print(json.dumps(Orchestrator().run_task(args.task_id),indent=2,ensure_ascii=False))
    elif args.command=='worker': Orchestrator().serve(once=args.once)
    elif args.command=='hunt-clients':
        found=hunt_clients(args.query,max(1,min(args.limit,25))); print(json.dumps(found,indent=2,ensure_ascii=False))
    elif args.command=='leads': print(json.dumps(list_leads(),indent=2,ensure_ascii=False))
    elif args.command=='events': print(json.dumps(events(args.task_id),indent=2,ensure_ascii=False))

if __name__=='__main__': main()
