#!/usr/bin/python3

import docker
import os
import glob
import asyncio
from asyncio import Queue
from threading import Thread, Event
from pathlib import Path
from fastapi import FastAPI, WebSocket, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()
client = docker.from_env()
board = ""

@app.get("/containers")
async def get_list_of_container():
    # return list of available containers
    list_of_container = client.containers.list(all=True)
    list_of_desire_containers = []
    for container in list_of_container:
        if "v2fly" in container.name: # only containers which have v2fly in their name
            list_of_desire_containers.append(container.attrs)
            
    return list_of_desire_containers


@app.post("/restart/{container_id}")
async def restart_container_from_id(container_id : str, response: Response):
    # restart container with the given ID
    try:
        desire_container = client.containers.get(str(container_id))
        desire_container.restart(timeout=5)
        response.status_code = status.HTTP_200_OK
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))
        
@app.get("/files/list")
async def get_list_of_available_configs():
    # return list of client configs name
    list_of_files = []
    for file in glob.glob("client-configs/*.json"):
        list_of_files.append(os.path.basename(file))
        
    return list_of_files

@app.get("/files/{file_name}")
async def get_config_file(file_name : str):
    # get config file from folder
    path_of_file = "client-configs/" + file_name
    path = Path(path_of_file)
    if not path.exists():
        raise HTTPException(status_code=404, detail="file does not exists")
    
    return FileResponse(path=path_of_file, filename=file_name)

@app.get("/board")
async def get_board_content():
    # get content of the board
    return board

class Content(BaseModel):
    content: str

@app.post("/board")
async def set_board_content(content : Content):
    # set content on the board
    global board
    board = content.content

async def watch_container_log(queue, container, limit, event):
    # watch logs of the container and put the logs inside the queue
    container_log = container.logs(follow=True, stream=True, tail=limit)
    for line in container_log:
        await queue.put(line.decode())
        if event.is_set():
            break

def entrypoint(queue, container, limit, event):
    # run the function in async thread
    asyncio.run(watch_container_log(queue, container, limit, event))

@app.websocket("/watch-logs/{container_id}/ws")
async def watch_logs(websocket: WebSocket, container_id : str, limit : int = 10):
    # watch logs of container
    watch_log_t = None
    event = Event()
    communication_queue = Queue(maxsize=100)
    try:
        await websocket.accept()
        desire_container = client.containers.get(str(container_id))
        watch_log_t = Thread(target=entrypoint, args=(communication_queue, desire_container, limit, event))
        watch_log_t.start()
        while True:
            log = await communication_queue.get()
            await websocket.send_text(log)
    except Exception as e:
        print(e)

    await websocket.close()
    if watch_log_t:
        event.set()
        while (not communication_queue.empty()) and watch_log_t.is_alive():
            await communication_queue.get()