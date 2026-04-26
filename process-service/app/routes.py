from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
import aiofiles
import logging 
import mmap 

logger = logging.getLogger(__name__)

router = APIRouter()

def get_manager(request:Request):
        return request.app.state.manager

@router.post('/process', status_code=200)
async def process_bin_files(file : UploadFile = File(...)):
        try:
                temp_file = f'temp_{file.filename}'
                async with aiofiles.open(temp_file,'ab') as f:
                        context = await file.read()
                        await f.write(context)
                        print(context[:256])
                        
                return {'status':';ggg'} 
        except Exception:
                raise HTTPException(status_code=401)

@router.get('/result{task_id}', status_code=200)
async def get_task_id(task_id:int):
        pass