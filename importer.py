from datetime import datetime
from time import sleep
from threading import Thread
from os import environ

import http.server 
import socketserver 
from urllib.parse import urlparse

from pymstodo import ToDoConnection
from ticktick.oauth2 import OAuth2  # OAuth2 Manager
from ticktick.api import TickTickClient  # Main Interface

def date_only(dt: datetime) -> datetime:
    return datetime.combine(dt.date(), datetime.min.time())
 

todo_client_id = environ.get("MICROSOFT_TODO_CLIENT_ID")
todo_client_secret = environ.get("MICROSOFT_TODO_CLIENT_SECRET")

ticktick_auth_client = OAuth2(
    client_id=environ.get("TICKTICK_CLIENT_ID"),
    client_secret=environ.get("TICKTICK_CLIENT_SECRET"),
    redirect_uri=environ.get("TICKTICK_CLIENT_REDIRECT_URL"),
    cache_path="/cache/token-oauth",
    get_token_now=False,
)

token = None
todo_client = None
todo_response_url = environ.get("MICROSOFT_TODO_RESPONSE_URL")
if not todo_response_url:
    auth_url = ToDoConnection.get_auth_url(todo_client_id)
    print("Authorize MS ToDo at " + auth_url)
else:
    token = ToDoConnection.get_token(
        client_id=todo_client_id, 
        client_secret=todo_client_secret, 
        redirect_resp=todo_response_url,
    )
    todo_client = ToDoConnection(
        client_id=todo_client_id, 
        client_secret=todo_client_secret, 
        token=token,
    )

ticktick_client = None
ticktick_response_url = environ.get("TICKTICK_RESPONSE_URL")
if not ticktick_response_url:
    auth_url = ticktick_auth_client.get_auth_url()
    print("Authorize TickTick at " + auth_url)

httpd = None
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global todo_response_url
        global ticktick_response_url
        global todo_client
        global ticktick_client

        url_parts = urlparse(self.path)
        if url_parts.path == "/login/authorized":
            try:
                print("Authorizing with MS ToDo")
                todo_response_url = "https://localhost/" + self.path # fake it to make oauth2 happy
                token = ToDoConnection.get_token(
                    client_id=todo_client_id, 
                    client_secret=todo_client_secret, 
                    redirect_resp=todo_response_url,
                )
                todo_client = ToDoConnection(
                    client_id=todo_client_id, 
                    client_secret=todo_client_secret, 
                    token=token,
                )
            except Exception as e:
                print(e.message)
                todo_response_url = None
        elif url_parts.query.startswith("code"):
            try:
                print("Authorizing with TickTick")
                ticktick_response_url = "https://localhost/" + self.path # fake it to make oauth2 happy
                ticktick_auth_client.get_access_token(
                    use_browser=False, 
                    redirected_url=ticktick_response_url,
                )
                ticktick_client = TickTickClient(
                    environ.get("TICKTICK_USERNAME"),
                    environ.get("TICKTICK_PASSWORD"),
                    ticktick_auth_client,
                )
            except Exception as e:
                print(e.message)
                ticktick_response_url = None

        if not todo_response_url:
            self.send_response(302)
            auth_url = ToDoConnection.get_auth_url(todo_client_id)
            self.send_header('Location', auth_url)
            print("Redirecting browser to " + auth_url)
        elif not ticktick_response_url:
            self.send_response(302)
            auth_url = ticktick_auth_client.get_auth_url()
            self.send_header('Location', auth_url)
            print("Redirecting browser to " + auth_url)
        else:
            print("Fully authorized")
            self.send_response(200, "Done")
            
            # Shutdown server in another thread to avoid deadlock
            Thread(target=httpd.shutdown, daemon=True).start()
       
        self.end_headers()

if not todo_response_url or not ticktick_response_url:
    with socketserver.TCPServer(("", 8080), MyHttpRequestHandler) as httpd:
        print("Enabled HTTP server on port 8080 to aid authentication")
        httpd.serve_forever()

lists = todo_client.get_lists()
task_list = lists[0]

print("Starting...")
while True:
    tasks = todo_client.get_tasks(task_list.list_id)
    for task in tasks:
        print("Importing {}...".format(task.title))
        tt_task = ticktick_client.task.builder(
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

        ticktick_client.task.create(tt_task)

        print("Deleting {} from MS-TODO.".format(task.task_id))
        todo_client.delete_task(task.task_id, task_list.list_id)

    sleep(300)
