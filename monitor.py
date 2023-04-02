#!/usr/bin/python3

import docker
import glob
from pathlib import Path
from fastapi import FastAPI, WebSocket, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()
client = docker.from_env()
board = ""

@app.get("/containers")
async def get_list_of_container():
    list_of_container = client.containers.list(all=True)
    list_of_desire_containers = []
    for container in list_of_container:
        if "v2fly" in container.name:
            list_of_desire_containers.append(container.attrs)
            
    return list_of_desire_containers


@app.post("/restart/{container_id}")
async def restart_container_from_id(container_id : str, response: Response):
    try:
        desire_container = client.containers.get(str(container_id))
        desire_container.restart(timeout=5)
        response.status_code = status.HTTP_200_OK
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))
        
@app.get("/files/list")
async def get_list_of_available_configs():
    list_of_files = []
    for file in glob.glob("client-configs/*.json"):
        list_of_files.append(file)
        
    return list_of_files

@app.get("/files/{file_name}")
async def get_config_file(file_name : str):
    path_of_file = "client-configs/" + file_name
    path = Path(path_of_file)
    if not path.exists():
        raise HTTPException(status_code=404, detail="file does not exists")
    
    return FileResponse(path=path_of_file, filename=file_name)

@app.get("/board")
async def get_board_content():
    return board

class Content(BaseModel):
    content: str

@app.post("/board")
async def set_board_content(content : Content):
    global board
    board = content.content
    
@app.websocket("/watch-logs/{container_id}/ws")
async def watch_logs(websocket: WebSocket, container_id : str, limit : int = 10):
    await websocket.accept()
    try: 
        desire_container = client.containers.get(str(container_id))
        container_log = desire_container.logs(follow=True, stream=True, tail=limit)
        for line in container_log:
            await websocket.send_text(line)
    except Exception as e:
        await websocket.send_text({
            "error": str(e)
        })
        await websocket.close()