import os
import uuid
from typing import List
from fastapi import UploadFile, HTTPException
from sqlalchemy import select

from core.db.tables import Image, Item
from core.models.images import ImageModel, ImageCreateModel
from database import db


async def save_image(file: UploadFile, item_id: int) -> ImageModel:
    # Create uploads directory if it doesn't exist
    upload_dir = "static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    
    # Save to database
    async with db.sessionmaker() as session:
        # Verify item exists
        item = await session.execute(select(Item).where(Item.id == item_id))
        if not item.scalars().first():
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Create image record
        image = Image(file_path=file_path, item_id=item_id)
        session.add(image)
        await session.commit()
        await session.refresh(image)
        
        return ImageModel(
            id=image.id,
            file_path=image.file_path,
            item_id=image.item_id,
            created_at=image.created_at.isoformat()
        )


async def get_item_images(item_id: int) -> List[ImageModel]:
    async with db.sessionmaker() as session:
        query = select(Image).where(Image.item_id == item_id)
        result = await session.execute(query)
        images = result.scalars().all()
        
        return [
            ImageModel(
                id=image.id,
                file_path=image.file_path,
                item_id=image.item_id,
                created_at=image.created_at.isoformat()
            )
            for image in images
        ]


async def delete_image(image_id: int):
    async with db.sessionmaker() as session:
        query = select(Image).where(Image.id == image_id)
        result = await session.execute(query)
        image = result.scalars().first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Delete file from filesystem
        try:
            if os.path.exists(image.file_path):
                os.remove(image.file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not delete file: {str(e)}")
        
        # Delete from database
        await session.delete(image)
        await session.commit() 