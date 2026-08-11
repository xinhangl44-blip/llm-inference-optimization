import redis
from fastapi import FastAPI
import uuid
from pydantic import BaseModel
app = FastAPI()
r = redis.Redis(host="redis-0.redis-headless.default.svc.cluster.local", port=6379, password="lixinhang11", decode_responses=True)

class User(BaseModel):
    prompt: str

@app.get("/")
async def read_root():
    return {"message": "Welcome to FastAPI"}

@app.post("/items/")
async def create_item(request: User):
    request_id = str(uuid.uuid4())
    r.xadd("vllm_task_stream", {"id": request_id, "prompt": request.prompt})
    return {"item_id": request_id, "prompt": request.prompt}
