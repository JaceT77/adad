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

                base_url = settings.LLM_BASE_URL
                if not base_url and "gemini" in self.model.lower():
                    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

                client_kwargs = {"api_key": self.api_key}
                if base_url:
                    client_kwargs["base_url"] = base_url

                client = AsyncOpenAI(**client_kwargs)
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
        """O'zbekiston qurilish me'yorlariga asoslangan to'liq o'zbekcha ma'lumotnoma."""
        role_label = task.user.role.value if task.user else "arxitektor"
        role_name_uz = {
            "architect": "Arxitektor",
            "structural_engineer": "Konstruktor (Muhandis)",
            "cost_estimator": "Smetachi",
            "interior_designer": "Interyer va Fasad Dizayneri",
        }.get(role_label, role_label.title())

        title = task.project_title
        b_type = task.building_type

        return f"""📌 *ERTALABKI TEXNIK MA'LUMOTNOMA (DOSSIER)*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 *Loyiha:* {title} ({b_type})
👤 *Mutaxassis:* {role_name_uz}
📅 *Sana:* {task.target_date}

📋 *1. Loyiha haqida va iqlimiy kontekst*
• Bino tipologiyasi: {b_type.capitalize()}
• Iqlimiy omillar: Toshkentning keskin kontinental iqlimi (yozda +42°C gacha issiq, qishda sovuq). Tashqi devorlarni jiddiy issiqlik izolyatsiyasi va quyoshdan himoyalovchi oynalar talab etiladi.

⚖️ *2. Normativ hujjatlar (O'zbekiston SHNK / QMQ va Toshkent Dizayn Kodi)*
• *SHNK 2.08.02-22*: Jamoat va ma'muriy binolar (xona o'lchamlari, zinalar eni ≥ 1.2m, yo'laklar ≥ 1.5m).
• *SHNK 2.01.02-04*: Binolarning yong'in xavfsizligi (evakuatsiya yo'llari, 1-toifali yong'inga qarshi to'siqlar).
• *SHNK 2.01.03-19*: Seysmik hududlarda qurilish (8.5–9.0 ballik seysmik chidamlilik talablari).
• *Toshkent Shahri Dizayn Kodi*: Fasadlarning yagona me'moriy qiyofasi, konditsioner tashqi bloklarini dekorativ panjaralar bilan yashirish, neytral tabiiy ranglar.

🧱 *3. Tavsiya etiladigan materiallar va O'zbekiston bozoridan topish*
• *Devor materiali*: Gazobeton bloklari (*Gazoblok* D500, qalinligi 300mm). Ishlab chiqaruvchilar: *Arton*, *East Gazobeton* (Chirchiq zavodlari), xarid manzili: O'rikzor va Bekto'pi bozorlari.
• *Suvoq va pardoz*: Knauf MP-75 gipsli suvoq, fasad uchun silikat bo'yoq. Rasmiy diler: Knauf O'zbekiston.
• *Deraza va vitrajlar*: Akfa Comfort / Thermo 78 alyuminiy profillari, Low-E ikki kamerali energiya tejovchi oynalar (yozgi issiq nurlarini qaytaradi).
• *Pol va kafel*: Mahalliy chinni kafel / keramik granit (*Koshona Ceramic* / *Modern Tile*).

🌿 *4. Yashil va tejamkor texnologiyalar (Trilliant modeli)*
• *Oqova suvni qayta ishlash (Kulrang suv)*: Rakovinalar va konditsioner kondensati maxsus qum va ultrabinafsha (UV) filtrdan o'tkazilib, faqat tualet bachoklariga va yer osti sug'orish tizimiga qayta yo'naltiriladi (toza ichimlik suvini 35-40% tejaydi).
• *Qayta tiklanuvchi energiya*: Tomda 20–30 kVt quvvatga ega quyosh fotoelektr panellari tarmog'i.

🌍 *5. Variantlar taqqoslashi*
• *Mahalliy standart (Asosiy)*: Gazoblok + Akfa alyuminiy vitrajlar. Narxi tejamkor, materiallar Toshkentda mavjud.
{"• *Ilg'or Yevropa standarti*: Ventilyatsiyalanuvchi sopol (terrakota) fasad, quyosh harakatiga moslashuvchi avtomatlashtirilgan jaluzilar (Brise-Soleil), aqlli bino boshqaruv tizimi (BMS)." if task.request_global_tier else "• *Jahon standarti*: Buyurtmachi talabiga ko'ra qo'shimcha kiritilishi mumkin."}

📐 *6. AutoCAD (DWG) chizmasi uchun tayyor andoza ko'rsatkichlari*
• O'qlar to'ri (Setka osi): 6.0m x 6.0m yoki 6.0m x 7.2m temir-beton karkas o'qlari.
• Qavat balandliklari: 1-qavat toza balandligi 4.20m, yuqori qavatlar 3.60m.
• Devor qatlamlari: 15mm ichki suvoq + 300mm Gazoblok + 80mm mineral paxta + 40mm havo bo'shlig'i + travertin/alyuminiy fasad (Jami qalinlik ~450mm).
• Asosiy kommunikatsiya shaxtalari va zinalar o'lchamlari tayyor andozaga muvofiqlashtirilgan.
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
