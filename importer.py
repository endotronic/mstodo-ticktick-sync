from datetime import datetime
from time import sleep
from os import environ
from sys import exit

from pymstodo.client import ToDoConnection
from ticktick.oauth2 import OAuth2  # OAuth2 Manager
from ticktick.api import TickTickClient  # Main Interface


def date_only(dt: datetime) -> datetime:
    return datetime.combine(dt.date(), datetime.min.time())


client_id = environ.get("MICROSOFT_TODO_CLIENT_ID")
client_secret = environ.get("MICROSOFT_TODO_CLIENT_SECRET")

redirect_resp = environ.get("MICROSOFT_TODO_RESPONSE_URL")
if not redirect_resp:
    auth_url = ToDoConnection.get_auth_url(client_id)
    print("Authorize at " + auth_url)
    sleep(300)
    exit(0)

token = ToDoConnection.get_token(client_id, client_secret, redirect_resp)
todo_client = ToDoConnection(
    client_id=client_id, client_secret=client_secret, token=token
)

lists = todo_client.get_lists()
task_list = lists[0]


auth_client = OAuth2(
    client_id=environ.get("TICKTICK_CLIENT_ID"),
    client_secret=environ.get("TICKTICK_CLIENT_ID"),
    redirect_uri=environ.get("TICKTICK_CLIENT_REDIRECT_URI"),
    cache_path="/cache/token-oauth",
)

client = TickTickClient(
    environ.get("TICKTICK_USERNAME"),
    environ.get("TICKTICK_PASSWORD"),
    auth_client,
)

print("Starting...")
while True:
    tasks = todo_client.get_tasks(task_list.list_id)
    for task in tasks:
        print("Importing {}...".format(task.title))
        tt_task = client.task.builder(
            task.title,
            startDate=date_only(task.created_date),
            dueDate=task.reminder_date,
            timeZone="GMT",
            desc="Imported",
        )

        # It seems like TickTick won't do reminders when there is a start date
        if task.reminder_date:
            del tt_task["startDate"]
            tt_task["reminders"] = ["TRIGGER:PT0S"]

        client.task.create(tt_task)

        print("Deleting {} from MS-TODO.".format(task.task_id))
        todo_client.delete_task(task.task_id, task_list.list_id)

    sleep(300)
