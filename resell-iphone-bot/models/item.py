from pydantic import BaseModel, validator
import os


class Item(BaseModel):
    name: str
    image: str
    price: float
    currency: str
    category: str
    contact: str
    description: str

    @validator('image')
    def validate_image_path(cls, v):
        if not v:
            return v
            
        # Если путь уже является URL, оставляем как есть
        if v.startswith(('http://', 'https://')):
            return v
            
        # Проверяем, существует ли файл
        if not os.path.exists(v):
            raise ValueError(f"Image file not found: {v}")
            
        # Проверяем размер файла
        if os.path.getsize(v) > 10 * 1024 * 1024:  # 10MB
            raise ValueError(f"Image file too large: {v}")
            
        return v
