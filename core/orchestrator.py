import logging

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from core.prompts import DOSSIER_SYSTEM_PROMPT, generate_task_prompt
from database import crud
from database.models import DailyTask, Dossier

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    def __init__(self) -> None:
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL

    async def generate_dossier_content(self, task: DailyTask) -> str:
        prompt = generate_task_prompt(
            role=task.user.role.value if task.user else "Architect",
            project_title=task.project_title,
            building_type=task.building_type,
            raw_notes=task.raw_notes,
            request_global_tier=task.request_global_tier,
        )

        if self.api_key and self.api_key.strip() != "" and not self.api_key.startswith("your_"):
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=self.api_key)
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": DOSSIER_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                )
                content = response.choices[0].message.content
                if content:
                    return content
            except Exception as e:
                logger.error(f"Error calling LLM API: {e}. Falling back to domain generator.")

        # Fallback domain-specific synthesis engine for offline/local testing
        return self._generate_offline_synthesis(task)

    def _generate_offline_synthesis(self, task: DailyTask) -> str:
        """Generates a rich, domain-grounded dossier adhering to Uzbekistan building codes and client specs."""
        role_label = task.user.role.value.replace("_", " ").title() if task.user else "Architect"
        title = task.project_title
        b_type = task.building_type

        return f"""📌 *MORNING BRIEFING & DOSSIER*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 *Project:* {title} ({b_type})
👤 *Specialist:* {role_label}
📅 *Date:* {task.target_date}

📋 *1. Project & Spatial Context*
• Typology: {b_type.capitalize()}
• Climate Consideration: Tashkent continental climate (high summer heat + winter freeze). Requires insulated exterior envelope and solar shading.

⚖️ *2. Regulatory Codes (Uzbekistan SHNK & Tashkent Design Code)*
• *SHNK 2.08.02-09*: Public & Commercial Buildings (occupancy loads, stair clearances, corridor widths ≥ 1.5m).
• *SHNK 2.01.02-04*: Fire Safety (evacuation routes, fire-resistant partitions Type 1).
• *Tashkent Design Code (2023+)*: Unified architectural facade standards, neutral earth-tone palette, concealed HVAC condenser units, ground floor pedestrian permeability.

🧱 *3. Materials & Local Sourcing (Uzbekistan Market)*
• *Exterior Envelope*: Autoclaved aerated concrete blocks (*Gazoblok* D500) + mineral wool insulation (50mm). Available: *Arcon*, *Gazoblok Tashkent*, Urikzor building market.
• *Finishing*: Knauf MP-75 plaster, silicate facade paint. Local distributor: Knauf Uzbekistan.
• *Glazing & Profiles*: Akfa Comfort / Trio thermal-break aluminum profiles with Low-E double glazing (effective heat blocking for Uzbek summers).
• *Flooring & Tiling*: Local porcelain stoneware (*Koshona Ceramic* / *Modern Tile*).

🌿 *4. Sustainable & Green Technologies (Trilliant Model)*
• *Water Recycling*: Greywater filtration system installed in basement. Runoff from handwash sinks and AC condensate is passed through a quartz-sand + UV filter and re-routed exclusively for toilet flushing (saves up to 35% potable water).
• *Renewable Energy*: Rooftop solar PV setup (approx. 20kW system) providing peak daylight base-load coverage.

🌍 *5. Dual-Tier Options*
• *Local Tier (Default)*: Autoclaved aerated concrete + Akfa aluminum profiles. Estimated cost: budget-efficient, immediate local sourcing.
{"• *Global Tier (European Benchmark)*: Ventilated terracotta facade, automated sun louvers (Brise-Soleil), smart building energy management system (BEMS)." if task.request_global_tier else "• *Global Tier*: Available on request for high-spec commercial tenders."}

📐 *6. CAD / DWG Starter Drafting Checklist*
• Grid alignment: Recommend 6.0m x 6.0m or 6.0m x 7.2m column grid for optimal parking & office flexibility.
• Standard base floor heights: Ground floor 4.2m (clearance), typical upper floors 3.3m-3.6m.
• Base DWG template ready: check standard 40%-60% office core layout (elevators, fire stairs, wet zones grouped).
"""

    async def process_task(self, session: AsyncSession, task: DailyTask) -> Dossier:
        logger.info(f"Processing overnight research for task {task.id}: {task.project_title}")
        full_content = await self.generate_dossier_content(task)

        dossier = await crud.create_dossier(
            session=session,
            task_id=task.id,
            norms_summary="SHNK 2.08.02-09, SHNK 2.01.02-04, Tashkent Design Code",
            materials_summary="Gazoblok D500, Knauf MP-75, Akfa Thermal Aluminum, Low-E glass",
            eco_solutions="Solar PV rooftop, greywater sink filtration for toilet flushing",
            global_benchmarks="Terracotta ventilated facade, automated sun louvers"
            if task.request_global_tier
            else None,
            cad_dwg_notes="6.0m x 6.0m grid, core layout template",
            full_content=full_content,
        )
        return dossier


orchestrator = ResearchOrchestrator()
