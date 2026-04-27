import logging 
import aiofiles
from fastapi import UploadFile
from pymavlink.DFReader import DFReader_binary
import time
import os 
import tempfile
import json 


class Orchestrator():
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def write_new_file_to_disc(self, file: UploadFile, temp_file: str):
        try:
            import time
            start = time.perf_counter()
            async with aiofiles.open(temp_file,'ab') as f:
                    context = await file.read()
                    await f.write(context)
            return time.perf_counter() - start 
        except Exception:
            self.logger.error('failed write new file to disc',exc_info=True)
            raise

    def _process_file(self, fileno:int):
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl", mode="w", encoding="utf-8")
        mav = None
        try:
            start_time = time.perf_counter()
            duplicated_fd = os.dup(fileno)
            mav = DFReader_binary(duplicated_fd)
            count = 0
            while True :
                msg_raw = mav.recv_match(blocking=False,type=['GPS'])
                if msg_raw is None:
                    break
                original_msg :dict  = msg_raw.to_dict()
                if original_msg['I'] == 1 :
                    keys_msg_to_keep = {'TimeUS', 'Status', 'Lat','Lng','Alt','Spd'} 
                    new_dict = {key: original_msg.get(key,None) for key in keys_msg_to_keep}
                    tmp_file.write(json.dumps(new_dict) + "\n")
                count +=1
            duration = time.perf_counter() - start_time
            tmp_file.close()
            mav.close() 
            
            return {
                "file_path": tmp_file.name,
                "count": count, 
                "duration_sec": f"({int(duration//60)} min {duration%60:.2f} sec)"
            }
        
        except Exception as e: 
            if tmp_file:
                tmp_file.close()
            if os.path.exists(tmp_file.name):
                os.remove(tmp_file.name)
            if mav:
                mav.close()
            return {"error": str(e)}
    
    async def process(self,fileno:int):
        import asyncio
        return await asyncio.to_thread(self._process_file, fileno)