import asyncio
from app.database import engine
from sqlalchemy import text

async def check_db():
    async with engine.connect() as conn:
        # Check compliance bodies
        print("--- Compliance Bodies ---")
        bodies = await conn.execute(text("SELECT id, name FROM compliance_bodies"))
        for b in bodies:
            print(f"ID: {b.id}, Name: {b.name}")
            
        # Check regulation documents
        print("\n--- Regulation Documents ---")
        docs = await conn.execute(text("SELECT id, compliance_body_id, status, filename, total_pages FROM regulation_documents"))
        for d in docs:
            print(f"ID: {d.id}, BodyID: {d.compliance_body_id}, Status: {d.status}, File: {d.filename}, Pages: {d.total_pages}")
            
        # Check regulation texts
        print("\n--- Regulation Texts Count ---")
        counts = await conn.execute(text("SELECT regulation_id, count(*) as count FROM regulation_texts GROUP BY regulation_id"))
        for c in counts:
            print(f"DocID: {c.regulation_id}, Count: {c.count}")
            
        # Check a sample text if exists
        print("\n--- Sample Regulation Text ---")
        sample = await conn.execute(text("SELECT section_ref, text FROM regulation_texts LIMIT 1"))
        row = sample.fetchone()
        if row:
            print(f"Section: {row.section_ref}")
            print(f"Text: {row.text[:200]}...")
        else:
            print("No texts found.")

if __name__ == "__main__":
    asyncio.run(check_db())
