import magic

import fitz  # PyMuPDF, imported as fitz for backward compatibility reasons
from django.core.files.base import ContentFile
import cv2

def detect_content_type(f):
    sample = f.read(2048)
    f.seek(0)

    return magic.from_buffer(sample, mime=True)


def get_file_thumbnail(file, mime_type: str):
    if mime_type == "application/pdf":
        pdf_document = fitz.open(stream=file.read())

        first_page = pdf_document.load_page(0)
        thumbnail = first_page.get_pixmap()
        # TODO resize & lower quality
        return thumbnail.tobytes()
    
    base_type = mime_type.split("/")[0] 
    
    if base_type == "image":
        # TODO resize & co
        return file.read()
    
    if base_type == "video":
        # save file to storage as cv2 requires working with file uri's
        file.save(file.name, file, save=False)
        # extract frame
        videocap = cv2.VideoCapture(file.path)
        
        # get a frame after 3 seconds
        FRAME_AFTER_SECONDS = 3
        videocap.set(cv2.CAP_PROP_POS_MSEC,FRAME_AFTER_SECONDS*1000)
        
        success, frame = videocap.read()
        if not success:
            # TODO handle
            pass
        success, encoded_frame = cv2.imencode(".jpeg", frame)
        if not success:
            # TODO handle
            pass
        return encoded_frame.tobytes()

    # TODO thumbnails for other file types

    return None
