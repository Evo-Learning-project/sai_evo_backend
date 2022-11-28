import magic

import fitz  # PyMuPDF, imported as fitz for backward compatibility reasons
from django.core.files.base import ContentFile


def detect_content_type(f):
    sample = f.read(2048)
    f.seek(0)

    return magic.from_buffer(sample, mime=True)


def get_file_thumbnail(file, mime_type: str):
    if mime_type == "application/pdf":
        pdf_document = fitz.open(stream=file.read())

        first_page = pdf_document.load_page(0)
        thumbnail = first_page.get_pixmap()
        print("\n\n\thumb", thumbnail, dir(thumbnail))
        print("BYTES", ContentFile(thumbnail.tobytes()))
        return thumbnail.tobytes()

    return None
