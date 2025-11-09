from pydantic import BaseModel

class UploadRequest(BaseModel):
    file_url: str
    submission_id: str
    assignment_id: str 
