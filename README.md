# mstodo-ticktick-sync
Service to sync tasks from MS ToDo to TickTick, enabling Samsung Galaxy Watch to make tasks in TickTick

1. Set up an app in MS ToDo (see pymstodo readme)
2. Set up an app in TickTick (see ticktick-py readme)
3. Deploy with docker
```
  todo-importer:
    image: todo-importer
    container_name: todo-importer
    build:
      context: ./repos/mstodo-ticktick-sync
      args:
        module_name: importer
        UID: 1000
        GID: 1000
    environment:
      MICROSOFT_TODO_CLIENT_ID: "MICROSOFT_TODO_CLIENT_ID"
      MICROSOFT_TODO_CLIENT_SECRET: "MICROSOFT_TODO_CLIENT_SECRET"
      MICROSOFT_TODO_RESPONSE_URL: ""
      TICKTICK_CLIENT_ID: "TICKTICK_CLIENT_ID"
      TICKTICK_CLIENT_SECRET: "TICKTICK_CLIENT_SECRET"
      TICKTICK_CLIENT_REDIRECT_URL: "http://localhost"
      TICKTICK_USERNAME: "TICKTICK_USERNAME"
      TICKTICK_PASSWORD: "TICKTICK_PASSWORD"
      TICKTICK_RESPONSE_URL: ""
    volumes:
      - ./configs/todo-importer:/cache
    restart: unless-stopped
 ```
 4. Get docker logs. This contains a URL to authenticate both ToDo and TickTick. Follow each, then paste the URL the browser lands in your docker compose file for MICROSOFT_TODO_RESPONSE_URL and TICKTICK_RESPONSE_URL. I recommend doing TickTick first; Microsoft's auth times out very quickly.
 5. Recreate the docker container with these values populated (MICROSOFT_TODO_RESPONSE_URL and TICKTICK_RESPONSE_URL).
 6. Confirm logs now say "Starting..."
 
