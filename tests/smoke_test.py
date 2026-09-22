import asyncio
import sys
from datetime import date
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.orchestrator import orchestrator
from database import crud
from database.connection import async_session, init_db
from database.models import SpecialistRole, TaskStatus


async def run_smoke_test() -> None:
    print("=" * 60)
    print("RUNNING ADAD SMOKE TEST & SYSTEM VERIFICATION")
    print("=" * 60)

    # 1. Initialize Tables
    print("\n1. Initializing database schema...")
    await init_db()
    print("   [OK] Tables created successfully.")

    async with async_session() as session:
        # 2. Create / Get User & Admin verification
        print("\n2. Testing User creation, role assignment, and Admin status...")
        user = await crud.get_or_create_user(
            session=session,
            telegram_id=999999999,
            full_name="Test Architect User",
            username="test_architect",
            role=SpecialistRole.ARCHITECT,
        )
        print(f"   [OK] User 1 created: {user.full_name} (Role: {user.role.value}, IsAdmin: {user.is_admin})")

        # Create a second user (Specialist)
        user2 = await crud.get_or_create_user(
            session=session,
            telegram_id=888888888,
            full_name="Second Specialist User",
            username="second_specialist",
            role=SpecialistRole.COST_ESTIMATOR,
        )
        print(f"   [OK] User 2 created: {user2.full_name} (Role: {user2.role.value}, IsAdmin: {user2.is_admin})")

        # Test admin promotion
        print("\n2b. Testing Admin Promotion via set_user_admin...")
        promoted_user = await crud.set_user_admin(session, user2.id, is_admin=True)
        assert promoted_user.is_admin is True, "User 2 should now be an admin"
        print(f"   [OK] User 2 successfully promoted to Admin: {promoted_user.is_admin}")

        # 3. Create Daily Task (Evening flow)
        print("\n3. Testing Evening Task registration...")
        task = await crud.create_daily_task(
            session=session,
            user_id=user.id,
            project_title="3-Story Modern Office in Yunusabad",
            building_type="Commercial Office",
            raw_notes="Energy-saving design, local aerated blocks, greywater filtration for toilets.",
            request_global_tier=True,
            target_date=date.today(),
        )
        print(f"   [OK] Task created with ID: {task.id}, Status: {task.status.value}")

        # 4. Overnight Research Orchestration
        print("\n4. Testing AI Research Orchestrator...")
        dossier = await orchestrator.process_task(session=session, task=task)
        print(f"   [OK] Dossier generated with ID: {dossier.id}")
        print(f"   [OK] Task status updated to: {task.status.value}")

        # Assertions
        assert task.status == TaskStatus.READY, f"Expected READY status, got {task.status}"
        assert "SHNK" in dossier.full_content, "Dossier should reference SHNK norms"
        assert "Trilliant" in dossier.full_content or "filtration" in dossier.full_content, (
            "Dossier should contain water recycling specs"
        )
        assert (
            "Gazoblok" in dossier.full_content
            or "Knauf" in dossier.full_content
            or "materials" in dossier.full_content.lower()
        ), "Dossier should contain local materials"

        # 5. Morning Delivery Query
        print("\n5. Testing Morning Delivery queries...")
        ready_tasks = await crud.get_ready_dossiers_for_delivery(session, target_date=date.today())
        matching = [t for t in ready_tasks if t.id == task.id]
        assert len(matching) == 1, "Should find 1 ready task for delivery"
        print(f"   [OK] Found {len(ready_tasks)} ready task(s) for morning delivery.")

        # 6. Mark Delivered
        print("\n6. Testing Task Delivery confirmation...")
        await crud.mark_task_delivered(session, task.id)
        assert task.status == TaskStatus.DELIVERED
        print("   [OK] Task status successfully marked DELIVERED.")

    print("\n" + "=" * 60)
    print("ALL SMOKE TESTS PASSED SUCCESSFULLY! 🎉")
    print("=" * 60)
    print("\nSample Generated Dossier Preview:")
    print("-" * 40)
    print(dossier.full_content)
    print("-" * 40)


if __name__ == "__main__":
    try:
        asyncio.run(run_smoke_test())
    except Exception as e:
        print(f"\n[FAILED] Smoke test failed with error: {e}")
        sys.exit(1)
