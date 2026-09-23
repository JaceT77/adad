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

    async def generate_dossier_content(self, task: DailyTask, role: str | None = None) -> str:
        if not role:
            try:
                role = task.user.role.value if (hasattr(task, "user") and task.user) else "Architect"
            except Exception:
                role = "Architect"

        prompt = generate_task_prompt(
            role=role,
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
        """O'zbekiston qurilish me'yorlariga asoslangan to'liq o'zbekcha va ruscha manbali ma'lumotnoma."""
        role_label = task.user.role.value if (hasattr(task, "user") and task.user) else "architect"
        role_name_uz = {
            "architect": "Arxitektor",
            "structural_engineer": "Konstruktor (Muhandis)",
            "cost_estimator": "Smetachi",
            "interior_designer": "Interyer va Fasad Dizayneri",
        }.get(role_label, role_label.title())

        title = task.project_title
        b_type = task.building_type

        tier_diff = (
            "• <b>Ilg'or Yevropa standarti:</b> Ventilyatsiyalanuvchi sopol (terrakota) fasad, quyosh harakatiga moslashuvchi avtomatlashtirilgan jaluzilar (Brise-Soleil), aqlli bino boshqaruv tizimi (BMS, KNX)."
            if task.request_global_tier
            else "• <b>Jahon standarti:</b> Buyurtmachi talabiga ko'ra qo'shimcha kiritilishi mumkin."
        )

        return f"""📌 <b>TEXNIK MA'LUMOTNOMA (DOSSIER)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 <b>Loyiha:</b> <code>{title}</code>
🏗️ <b>Bino turi:</b> <code>{b_type}</code>
👤 <b>Mutaxassis:</b> <b>{role_name_uz}</b>
📅 <b>Reja sanasi:</b> <code>{task.target_date}</code>

<b>📋 1. LOYIHA HAQIDA VA IQLIMIY KONTEKST</b>
• <b>Bino tipologiyasi:</b> {b_type.capitalize()}
• <b>Iqlimiy sharoit:</b> Toshkentning keskin kontinental iqlimi (yozda +42°C gacha issiq, qishda -18°C gacha sovuq). Tashqi devorlarni jiddiy issiqlik izolyatsiyasi va quyoshdan himoyalovchi oynalar talab etiladi.
<blockquote><b>Rasmiy manba / Официальный источник:</b>
QMQ 2.01.01-94 "Loyihalash uchun iqlimiy va fizik-geologik ma'lumotlar" / <i>КМК 2.01.01-94 "Климатические и физико-геологические данные для проектирования"</i>.</blockquote>

<b>⚖️ 2. TEGISHLI NORMATIV HUJJATLAR VA ANIQ MANBALAR</b>
• <b>SHNK 2.08.02-09</b> "Jamoat binolari va inshootlari" / <i>СНиП 2.08.02-09 "Общественные здания и сооружения"</i> (Xona o'lchamlari, zinalar eni ≥ 1.20m, evakuatsiya yo'laklari ≥ 1.50m).
• <b>SHNK 2.01.03-19</b> "Seysmik hududlarda qurilish" / <i>СНиП 2.01.03-19 "Строительство в сейсмических районах"</i> (Toshkent hududi: 8-9 ballik seysmik chidamlilik talablari, temir-beton monolit karkas va gazobetonni armaturalash).
• <b>SHNK 2.01.02-04</b> "Binolar va inshootlarning yong'in xavfsizligi" / <i>СНиП 2.01.02-04 "Противопожарные нормы строительства зданий и сооружений"</i> (I-II darajali yong'inga chidamlilik, yong'inga qarshi to'siqlar).
• <b>SHNK 2.01.04-18</b> "Qurilish issiqlik texnikasi" / <i>СНиП 2.01.04-18 "Строительная теплотехника"</i> (Toshkent uchun tashqi to'siq konstruksiyalarining issiqlik uzatishga qarshiligi: <code>R₀ ≥ 2.8 - 3.2 m²·°C/W</code>).
• <b>Toshkent Shahri Arxitektura Dizayn Kodi:</b> Fasadlarning yaxlit qiyofasi, konditsioner tashqi bloklarini dekorativ panjara (basket) bilan yashirish, imkoniyati cheklanganlar uchun pandus (1:12).
<blockquote><b>Qonunchilik bazasi / Законодательная база:</b>
O'zbekiston Respublikasi Qurilish vazirligi (mc.uz) va <a href="https://lex.uz">Lex.uz</a> milliy bazasi.</blockquote>

<b>🧱 3. TAVSIYA ETILADIGAN MATERIALLAR VA XARID BOZORLARI</b>
• <b>Devor materiali:</b> D500/D600 zichlikdagi avtoklav gazobeton bloklari (qalinligi <code>300 mm</code>).
  <i>Ishlab chiqaruvchilar:</i> "Arton" (Chirchiq zavodi, arton.uz), "East Gazobeton".
  <i>Xarid manzili:</i> O'rikzor va Bekto'pi qurilish bozorlari (o'rtacha narx: 1 m³ = ~650,000 - 750,000 so'm).
• <b>Issiqlik izolyatsiyasi va suvoq:</b> 80-100 mm bazalt minvatasi (zichligi 110-130 kg/m³), Knauf MP-75 gipsli mashina suvog'i.
  <i>Yetkazib beruvchi:</i> "Knauf Gips Buxoro" rasmiy dilerlik tarmog'i.
• <b>Oyna va fasad vitrajlari:</b> Termoko'priqli alyuminiy profillar (Thermo 70 seriya), ikki kamerali energiya tejovchi oynalar (Low-E + Argon).
  <i>Ishlab chiqaruvchi:</i> "AKFA" / "IMZO", "Alutex".
• <b>Sement va beton:</b> Monolit karkas uchun B25 (M350) markali beton, M500 sementi.
  <i>Manba:</i> "Bekobodsement" / "Olmaliq TMK".

<b>🌿 4. YASHIL VA TEJAMKOR TEXNOLOGIYALAR</b>
• <b>Kulrang suvni qayta ishlash (Trilliant biznes markazi modeli):</b> Rakovinalar va konditsioner kondensati suvlari qum va ultrabinafsha (UF) filtrdan o'tkazilib, faqat hojatxona bachoklariga va yer osti tomchilatib sug'orish tizimiga yo'naltiriladi (toza ichimlik suvi sarfini 35-40% tejaydi).
<blockquote><b>Normativ asos / Нормативная основа:</b>
SHNK 2.04.01-98 "Binolarning ichki suv ta'minoti va kanalizatsiyasi" / <i>СНиП 2.04.01-98 "Внутренний водопровод и канализация"</i>.</blockquote>
• <b>Quyosh fotoelektr tizimi (Solar PV):</b> Tom maydoniga <code>30 - 50 kVt</code> quvvatli quyosh panellari o'rnatish orqali bino kunduzgi ehtiyojining 50-60% elektr energiyasini qoplaydi.

<b>🌍 5. VARIANTLAR TAQQOSLASHI</b>
• <b>O'zbekiston standarti (Asosiy-Tejamkor):</b> Gazoblok + Akfa alyuminiy vitrajlar + Knauf mineral vata. Narxi tejamkor, barcha materiallar mahalliy bozorlarda mavjud.
{tier_diff}

<b>📐 6. AUTOCAD (DWG) CHIZMASI UCHUN TAYYOR ANDOZA KO'RSATKICHLARI</b>
• <b>Konstruktiv o'qlar to'ri:</b> <code>6.0m × 6.0m</code> yoki <code>6.0m × 7.2m</code> temir-beton monolit ustunlar qadami.
• <b>Qavat balandliklari:</b> 1-qavat toza balandligi <code>4.20m</code>, yuqori qavatlar <code>3.60m</code> (osma shiftgacha toza balandlik <code>3.00m</code>).
• <b>Devor kesimi qatlamlari (tashqaridan ichkariga):</b> Fasad paneli (10mm) + havo tirqishi (40mm) + bazalt vata (80mm) + gazoblok (300mm) + Knauf suvoq (20mm) = <b>Jami 450 mm</b>.
• <b>Kommunikatsiya shaxtalari:</b> Shamollatish (HVAC) shaxtasi <code>1200mm × 800mm</code>, Santexnika va kulrang suv shaxtasi <code>800mm × 600mm</code>.
"""

    async def process_task(self, session: AsyncSession, task: DailyTask) -> Dossier:
        logger.info(f"Processing overnight research for task {task.id}: {task.project_title}")
        full_content = await self.generate_dossier_content(task)
        role = "Architect"
        if task.user_id:
            user = await crud.get_user_by_id(session, task.user_id)
            if user and user.role:
                role = user.role.value

        full_content = await self.generate_dossier_content(task, role=role)

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
