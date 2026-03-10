import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import uuid
import tempfile
import re
import sys

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://-.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str
    language: str
    input_data: str = ""

@app.post("/run")
async def run_code(request: CodeRequest):
    return {"output": "Please use the interactive terminal!", "status": "success"}

@app.websocket("/ws/run")
async def run_code_ws(websocket: WebSocket):
    await websocket.accept()
    
    try:
        data = await websocket.receive_json()
        lang = data.get("language", "").lower()
        code = data.get("code", "")
        unique_id = str(uuid.uuid4())[:8]

        with tempfile.TemporaryDirectory() as tmpdirname:
            compile_cmd = None
            run_cmd = None

            # ==================== LANGUAGE COMMANDS ====================
            if lang == "python":
                run_cmd = [sys.executable, "-u", "-c", code]
            
            elif lang in ["cpp", "c++"]:
                cpp_file = os.path.join(tmpdirname, f"{unique_id}.cpp")
                out_file = os.path.join(tmpdirname, f"{unique_id}.exe" if os.name == 'nt' else f"{unique_id}.out")
                with open(cpp_file, "w") as f: f.write(code)
                compile_cmd = ["g++", cpp_file, "-o", out_file]
                run_cmd = [out_file]
            
            elif lang == "c":
                c_file = os.path.join(tmpdirname, f"{unique_id}.c")
                out_file = os.path.join(tmpdirname, f"{unique_id}.exe" if os.name == 'nt' else f"{unique_id}.out")
                with open(c_file, "w") as f: f.write(code)
                compile_cmd = ["gcc", c_file, "-o", out_file]
                run_cmd = [out_file]
            
            elif lang == "java":
                match = re.search(r'(?:public\s+)?class\s+([A-Za-z0-9_]+)', code)
                class_name = match.group(1) if match else "Main"
                java_file = os.path.join(tmpdirname, f"{class_name}.java")
                with open(java_file, "w") as f: f.write(code)
                compile_cmd = ["javac", java_file]
                run_cmd = ["java", "-cp", tmpdirname, class_name]
            else:
                await websocket.send_text("Language not supported for interactive execution.\r\n")
                await websocket.close()
                return

            # ==================== COMPILE (IF NEEDED) ====================
            if compile_cmd:
                await websocket.send_text("Compiling...\r\n")
                compile_proc = await asyncio.create_subprocess_exec(
                    *compile_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                _, stderr = await compile_proc.communicate()
                if compile_proc.returncode != 0:
                    await websocket.send_text(f"Compilation Error:\r\n{stderr.decode()}\r\n")
                    await websocket.close()
                    return

            # ==================== RUN ====================
            await websocket.send_text("Running...\r\n-----------------------\r\n")
            process = await asyncio.create_subprocess_exec(
                *run_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            async def read_stdout():
                while True:
                    chunk = await process.stdout.read(1)
                    if not chunk:
                        break
                    text = chunk.decode(errors='replace').replace('\n', '\r\n')
                    await websocket.send_text(text)

            async def write_stdin():
                try:
                    while True:
                        user_input = await websocket.receive_text()
                        if process.stdin:
                            process.stdin.write(user_input.encode())
                            await process.stdin.drain()
                except WebSocketDisconnect:
                    pass

            stdout_task = asyncio.create_task(read_stdout())
            stdin_task = asyncio.create_task(write_stdin())

            await process.wait()
            await stdout_task
            
            await websocket.send_text(f"\r\n\r\n=== Code Execution Finished (Exit code {process.returncode}) ===\r\n")
            
    except Exception as e:
        await websocket.send_text(f"\r\nSystem Error: {str(e)}\r\n")
    finally:
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



