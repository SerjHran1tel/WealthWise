from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.app.database import SessionLocal
from backend.app.agents.weekly_report_agent import weekly_report_agent
from backend.app.agents.predictive_analytics import predictive_analytics_agent
from backend.app.core.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()


def generate_weekly_reports_for_all_users():
    """
    Генерирует еженедельные отчёты для всех пользователей.
    Вызывается автоматически каждый понедельник в 9:00.
    """
    logger.info("🔔 Starting weekly report generation for all users...")

    db = SessionLocal()
    try:
        # В production здесь был бы запрос всех активных пользователей
        # Для MVP используем тестового пользователя
        TEST_USER_ID = settings.DEFAULT_USER_ID

        # Генерируем отчёт
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        report = loop.run_until_complete(
            weekly_report_agent.generate_weekly_report(db, TEST_USER_ID)
        )

        loop.close()

        logger.info(f"✅ Weekly report generated for user {TEST_USER_ID}")
        logger.info(f"   - {report['stats']['expenses']:.0f}₽ expenses")
        logger.info(f"   - {len(report['actions'])} actions proposed")
        logger.info(f"   - {len(report['recommendations'])} recommendations")

        # В production здесь была бы отправка:
        # - Email уведомления
        # - Push notification
        # - Telegram бот

    except Exception as e:
        logger.error(f"❌ Error generating weekly reports: {e}", exc_info=True)
    finally:
        db.close()


def run_daily_analytics():
    """
    Запускает аналитику каждый день в полночь.
    Обновляет инсайты, прогнозы, аномалии.
    """
    logger.info("📊 Running daily analytics...")

    db = SessionLocal()
    try:
        TEST_USER_ID = settings.DEFAULT_USER_ID

        # Запускаем predictive analytics
        insights_count = predictive_analytics_agent.run_comprehensive_analysis(db, TEST_USER_ID)

        logger.info(f"✅ Daily analytics completed: {insights_count} insights generated")

    except Exception as e:
        logger.error(f"❌ Error running daily analytics: {e}", exc_info=True)
    finally:
        db.close()


def start_scheduler():
    """
    Запускает scheduler с заданиями.
    """
    logger.info("⏰ Starting APScheduler...")

    # 1. Еженедельные отчёты: каждый понедельник в 9:00
    scheduler.add_job(
        func=generate_weekly_reports_for_all_users,
        trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
        id='weekly_reports',
        name='Generate Weekly Reports',
        replace_existing=True
    )
    logger.info("   ✅ Scheduled: Weekly Reports (Monday 9:00 AM)")

    # 2. Ежедневная аналитика: каждый день в 00:00
    scheduler.add_job(
        func=run_daily_analytics,
        trigger=CronTrigger(hour=0, minute=0),
        id='daily_analytics',
        name='Daily Analytics Update',
        replace_existing=True
    )
    logger.info("   ✅ Scheduled: Daily Analytics (Every day 00:00)")

    # Запускаем scheduler
    scheduler.start()
    logger.info("✅ APScheduler started successfully")

    # Показываем список задач
    jobs = scheduler.get_jobs()
    logger.info(f"📋 Active jobs: {len(jobs)}")
    for job in jobs:
        logger.info(f"   - {job.name} (next run: {job.next_run_time})")


def stop_scheduler():
    """
    Останавливает scheduler.
    """
    logger.info("⏸️  Stopping APScheduler...")
    scheduler.shutdown()
    logger.info("✅ APScheduler stopped")


def trigger_weekly_report_now():
    """
    Ручной запуск генерации еженедельного отчёта (для тестирования).
    """
    logger.info("🔔 Manual trigger: Generating weekly report NOW...")
    generate_weekly_reports_for_all_users()


def get_scheduler_status():
    """
    Возвращает статус scheduler и список задач.
    """
    jobs = scheduler.get_jobs()

    return {
        "running": scheduler.running,
        "jobs_count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]
    }