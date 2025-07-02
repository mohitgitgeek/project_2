from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import uvicorn
import io
import base64
from api.utils import process_task

app = FastAPI()

@app.post("/")
async def handle_request(file: UploadFile):
    try:
        task_text = await file.read()
        task_text = task_text.decode()

        result = await process_task(task_text)

        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000)
