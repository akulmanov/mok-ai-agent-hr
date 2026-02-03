"""
Script to clear all vacancies, candidates, and CVs from the database.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_db, Base, engine
from app.models import Position, Candidate, Screening, Clarification
from sqlalchemy.orm import Session

def clear_all_data():
    """Clear all data from the database."""
    db = next(get_db())
    
    try:
        # Delete in correct order (respecting foreign keys)
        print("Удаление результатов отборов...")
        db.query(Screening).delete()
        
        print("Удаление уточнений...")
        db.query(Clarification).delete()
        
        print("Удаление кандидатов...")
        db.query(Candidate).delete()
        
        print("Удаление вакансий...")
        db.query(Position).delete()
        
        db.commit()
        print("✅ Все данные успешно удалены!")
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при удалении данных: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("⚠️  ВНИМАНИЕ: Это удалит ВСЕ данные из базы данных!")
    confirm = input("Продолжить? (yes/no): ")
    if confirm.lower() == 'yes':
        clear_all_data()
    else:
        print("Отменено.")
