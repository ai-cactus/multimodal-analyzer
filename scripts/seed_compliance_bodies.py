"""
Seed script to populate compliance bodies (CARF, MHRS, DBH)
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import async_session_maker
from app.models import ComplianceBody
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def seed_compliance_bodies():
    """Seed initial compliance bodies"""
    
    compliance_bodies = [
        {
            "name": "CARF",
            "full_name": "Commission on Accreditation of Rehabilitation Facilities",
            "description": "CARF Behavioral Health Standards for accreditation"
        },
        {
            "name": "MHRS",
            "full_name": "Mental Health Rehabilitation Services (DC)",
            "description": "DC Mental Health Rehabilitation Services regulations"
        },
        {
            "name": "DBH",
            "full_name": "Department of Behavioral Health",
            "description": "Department of Behavioral Health licensing and operational rules"
        }
    ]
    
    async with async_session_maker() as session:
        try:
            # Check if already seeded
            from sqlalchemy import select
            result = await session.execute(select(ComplianceBody))
            existing = result.scalars().all()
            
            if existing:
                logger.info(f"Database already seeded with {len(existing)} compliance bodies")
                return
            
            # Create compliance bodies
            for body_data in compliance_bodies:
                body = ComplianceBody(**body_data)
                session.add(body)
                logger.info(f"Creating compliance body: {body_data['name']}")
            
            await session.commit()
            logger.info("Successfully seeded all compliance bodies")
            
        except Exception as e:
            logger.error(f"Error seeding compliance bodies: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    logger.info("Starting database seed...")
    asyncio.run(seed_compliance_bodies())
    logger.info("Database seed complete")
