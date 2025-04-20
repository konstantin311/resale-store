from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text

from database import db
from config import DatabaseMarker

router = APIRouter(tags=["Health"])


@router.get("/health-check")
async def health_check():
    """
    Проверка работоспособности API и подключения к базе данных
    """
    try:
        async with db.sessionmaker() as session:
            # Пробуем выполнить простой запрос к базе данных
            result = await session.execute(text("SELECT 1"))
            db_status = "connected" if result.scalar() == 1 else "error"
            
            return {
                "status": "ok",
                "database": db_status
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection error: {str(e)}"
        ) 