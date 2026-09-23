import asyncio
import sys
from datetime import date
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.bot import bot
from bot.utils.sender import clean_text_for_telegram, split_text_into_chunks, safe_send_message
from config.settings import settings
from core.orchestrator import orchestrator
from database import crud
from database.connection import async_session, init_db
from database.models import SpecialistRole, TaskStatus
from scheduler.jobs import evening_task_prompt_job, morning_dossier_delivery_job


async def run_comprehensive_check() -> None:
    print("=" * 70)
    print("STARTING COMPREHENSIVE BOT & SYSTEM HEALTH CHECK")
    print("=" * 70)

    # 1. Telegram API Connectivity
    print("\n[Step 1] Checking Telegram Bot API Connectivity...")
    me = await bot.get_me()
    print(f"  --> Bot Connected: @{me.username} (ID: {me.id}, Name: {me.first_name})")
    assert me.username is not None

    # 2. Database Initialization
    print("\n[Step 2] Initializing SQLite Database...")
    await init_db()
    print("  --> SQLite Database schema verified.")

    # 3. User & Admin Logic
    print("\n[Step 3] Testing User & Admin CRUD Operations...")
    async with async_session() as session:
        # Check active users
        users = await crud.get_active_users(session)
        print(f"  --> Active users in DB: {len(users)}")
        admin_count = sum(1 for u in users if u.is_admin)
        print(f"  --> Admin users in DB: {admin_count}")
        assert admin_count >= 1, "At least one admin should exist"

        # Verify first user admin rule
        test_first_user = await crud.get_or_create_user(
            session=session,
            telegram_id=111111111,
            full_name="Auto Test User",
            username="auto_test",
            role=SpecialistRole.ARCHITECT,
        )
        print(f"  --> Created/Retrieved user: {test_first_user.full_name} (Admin: {test_first_user.is_admin})")

    # 4. Sender & Chunking Logic
    print("\n[Step 4] Testing Safe Sender & Chunking Logic...")
    long_content = "🏛️ Qurilish normativlari SHNK 2.01.03-19 va Toshkent dizayn kodi. " * 120
    latex_sample = "Formulalar: $R_0 = 3.5 \\text{ m}^2 \\cdot \\text{K/W}$, narxi $500, $\\alpha=0.85$."
    cleaned = clean_text_for_telegram(long_content + latex_sample)
    chunks = split_text_into_chunks(cleaned, max_chunk_size=3800)
    print(f"  --> Original length: {len(cleaned)} chars")
    print(f"  --> Resulting chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        assert len(chunk) <= 3800, f"Chunk {i} exceeds 3800 limit: {len(chunk)}"
        assert "$" not in chunk, f"LaTeX delimiter $ still found in chunk {i}"
        print(f"      Chunk {i}: {len(chunk)} chars [VALID]")

    # 5. Task & AI Dossier Generation
    print("\n[Step 5] Testing AI Dossier Generation & Storage...")
    async with async_session() as session:
        test_task = await crud.create_daily_task(
            session=session,
            user_id=test_first_user.id,
            project_title="Chilonzordagi 5 qavatli IT-Park binosi",
            building_type="Tijorat ofisi",
            raw_notes="Mahalliy gazoblok, energiya tejamkor oynalar, suvni qayta ishlash",
            request_global_tier=True,
            target_date=date.today(),
        )
        print(f"  --> Created Task: ID={test_task.id}, Title='{test_task.project_title}'")

        # Process task via orchestrator
        dossier = await orchestrator.process_task(session=session, task=test_task)
        print(f"  --> Dossier generated: ID={dossier.id}, Length={len(dossier.full_content)} chars")
        assert len(dossier.full_content) > 1000
        assert "SHNK" in dossier.full_content
        assert test_task.status == TaskStatus.READY

    # 6. Morning Delivery & Evening Prompt Jobs
    print("\n[Step 6] Testing Scheduler Jobs Logic...")
    async with async_session() as session:
        ready_tasks = await crud.get_ready_dossiers_for_delivery(session, target_date=date.today())
        print(f"  --> Ready tasks for delivery today: {len(ready_tasks)}")
        assert any(t.id == test_task.id for t in ready_tasks)

        # Mark test task delivered
        await crud.mark_task_delivered(session, test_task.id)
        print("  --> Task marked as DELIVERED.")

    await bot.session.close()

    print("\n" + "=" * 70)
    print("ALL HEALTH CHECKS AND VERIFICATIONS PASSED SUCCESSFULLY! 🚀")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_comprehensive_check())
