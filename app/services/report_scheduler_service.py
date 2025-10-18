"""Сервис для планировщика отчетов"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import os

from app.models.user import User
from app.models.social import UserProfile
from app.services.advanced_analytics_service import AdvancedAnalyticsService, AnalyticsFilter, ReportType, ExportFormat


class ReportSchedule:
    """Расписание отчета"""
    
    def __init__(self, 
                 user_id: str,
                 report_type: ReportType,
                 schedule_type: str,  # daily, weekly, monthly
                 time: str,  # HH:MM format
                 email: str,
                 filters: Dict[str, Any],
                 export_format: ExportFormat = ExportFormat.PDF):
        self.user_id = user_id
        self.report_type = report_type
        self.schedule_type = schedule_type
        self.time = time
        self.email = email
        self.filters = filters
        self.export_format = export_format
        self.last_run = None
        self.next_run = self._calculate_next_run()
        self.is_active = True
    
    def _calculate_next_run(self) -> datetime:
        """Рассчитать следующее время запуска"""
        now = datetime.now()
        hour, minute = map(int, self.time.split(':'))
        
        if self.schedule_type == "daily":
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif self.schedule_type == "weekly":
            # Запуск в понедельник
            days_ahead = 0 - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        elif self.schedule_type == "monthly":
            # Запуск в первый день месяца
            if now.day == 1 and now.hour < hour:
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            else:
                next_month = now.replace(day=1) + timedelta(days=32)
                next_month = next_month.replace(day=1)
                next_run = next_month.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return next_run
    
    def should_run(self) -> bool:
        """Проверить, нужно ли запускать отчет"""
        if not self.is_active:
            return False
        
        now = datetime.now()
        return now >= self.next_run
    
    def mark_run(self):
        """Отметить выполнение отчета"""
        self.last_run = datetime.now()
        self.next_run = self._calculate_next_run()


class ReportSchedulerService:
    """Сервис планировщика отчетов"""
    
    def __init__(self, db: Session):
        self.db = db
        self.schedules: List[ReportSchedule] = []
        self.analytics_service = AdvancedAnalyticsService(db)
        self.is_running = False
    
    def add_schedule(self, schedule: ReportSchedule):
        """Добавить расписание отчета"""
        self.schedules.append(schedule)
        self._save_schedules()
    
    def remove_schedule(self, user_id: str, report_type: ReportType):
        """Удалить расписание отчета"""
        self.schedules = [s for s in self.schedules 
                         if not (s.user_id == user_id and s.report_type == report_type)]
        self._save_schedules()
    
    def get_user_schedules(self, user_id: str) -> List[ReportSchedule]:
        """Получить расписания пользователя"""
        return [s for s in self.schedules if s.user_id == user_id]
    
    def update_schedule(self, user_id: str, report_type: ReportType, 
                       new_schedule: ReportSchedule):
        """Обновить расписание отчета"""
        for i, schedule in enumerate(self.schedules):
            if schedule.user_id == user_id and schedule.report_type == report_type:
                self.schedules[i] = new_schedule
                break
        self._save_schedules()
    
    def _save_schedules(self):
        """Сохранить расписания в файл"""
        schedules_data = []
        for schedule in self.schedules:
            schedules_data.append({
                "user_id": schedule.user_id,
                "report_type": schedule.report_type.value,
                "schedule_type": schedule.schedule_type,
                "time": schedule.time,
                "email": schedule.email,
                "filters": schedule.filters,
                "export_format": schedule.export_format.value,
                "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
                "next_run": schedule.next_run.isoformat(),
                "is_active": schedule.is_active
            })
        
        with open("report_schedules.json", "w") as f:
            json.dump(schedules_data, f, indent=2)
    
    def _load_schedules(self):
        """Загрузить расписания из файла"""
        if not os.path.exists("report_schedules.json"):
            return
        
        try:
            with open("report_schedules.json", "r") as f:
                schedules_data = json.load(f)
            
            for data in schedules_data:
                schedule = ReportSchedule(
                    user_id=data["user_id"],
                    report_type=ReportType(data["report_type"]),
                    schedule_type=data["schedule_type"],
                    time=data["time"],
                    email=data["email"],
                    filters=data["filters"],
                    export_format=ExportFormat(data["export_format"])
                )
                schedule.last_run = datetime.fromisoformat(data["last_run"]) if data["last_run"] else None
                schedule.next_run = datetime.fromisoformat(data["next_run"])
                schedule.is_active = data["is_active"]
                self.schedules.append(schedule)
        except Exception as e:
            print(f"Error loading schedules: {e}")
    
    async def start_scheduler(self):
        """Запустить планировщик"""
        if self.is_running:
            return
        
        self.is_running = True
        self._load_schedules()
        
        while self.is_running:
            try:
                await self._process_schedules()
                await asyncio.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                print(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    def stop_scheduler(self):
        """Остановить планировщик"""
        self.is_running = False
    
    async def _process_schedules(self):
        """Обработать расписания"""
        for schedule in self.schedules:
            if schedule.should_run():
                try:
                    await self._generate_and_send_report(schedule)
                    schedule.mark_run()
                except Exception as e:
                    print(f"Error generating report for {schedule.user_id}: {e}")
        
        self._save_schedules()
    
    async def _generate_and_send_report(self, schedule: ReportSchedule):
        """Сгенерировать и отправить отчет"""
        # Создаем фильтр
        filter_params = AnalyticsFilter(**schedule.filters)
        
        # Генерируем отчет
        report_data = self.analytics_service.export_data(
            schedule.report_type,
            filter_params,
            schedule.export_format
        )
        
        # Отправляем email
        await self._send_email_report(
            schedule.email,
            schedule.report_type,
            report_data,
            schedule.export_format
        )
    
    async def _send_email_report(self, email: str, report_type: ReportType, 
                                report_data: bytes, export_format: ExportFormat):
        """Отправить отчет по email"""
        # Настройки SMTP (заглушка)
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        if not smtp_username or not smtp_password:
            print("SMTP credentials not configured")
            return
        
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = f"Universal Parser Report - {report_type.value}"
        
        # Текст сообщения
        body = f"""
        Здравствуйте!
        
        Ваш запланированный отчет готов.
        
        Тип отчета: {report_type.value}
        Формат: {export_format.value}
        Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        С уважением,
        Universal Parser Team
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Прикрепляем файл
        filename = f"report_{report_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format.value}"
        
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(report_data)
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename= {filename}'
        )
        msg.attach(attachment)
        
        # Отправляем email
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_username, email, text)
            server.quit()
            print(f"Report sent to {email}")
        except Exception as e:
            print(f"Error sending email to {email}: {e}")
    
    def create_schedule(self, user_id: str, report_type: str, schedule_type: str,
                       time: str, email: str, filters: Dict[str, Any],
                       export_format: str = "pdf") -> bool:
        """Создать расписание отчета"""
        try:
            schedule = ReportSchedule(
                user_id=user_id,
                report_type=ReportType(report_type),
                schedule_type=schedule_type,
                time=time,
                email=email,
                filters=filters,
                export_format=ExportFormat(export_format)
            )
            
            self.add_schedule(schedule)
            return True
        except Exception as e:
            print(f"Error creating schedule: {e}")
            return False
    
    def get_schedule_status(self, user_id: str) -> Dict[str, Any]:
        """Получить статус расписаний пользователя"""
        user_schedules = self.get_user_schedules(user_id)
        
        status = {
            "total_schedules": len(user_schedules),
            "active_schedules": len([s for s in user_schedules if s.is_active]),
            "schedules": []
        }
        
        for schedule in user_schedules:
            status["schedules"].append({
                "report_type": schedule.report_type.value,
                "schedule_type": schedule.schedule_type,
                "time": schedule.time,
                "email": schedule.email,
                "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
                "next_run": schedule.next_run.isoformat(),
                "is_active": schedule.is_active
            })
        
        return status
    
    def toggle_schedule(self, user_id: str, report_type: str, is_active: bool) -> bool:
        """Включить/выключить расписание"""
        try:
            report_type_enum = ReportType(report_type)
            for schedule in self.schedules:
                if schedule.user_id == user_id and schedule.report_type == report_type_enum:
                    schedule.is_active = is_active
                    self._save_schedules()
                    return True
            return False
        except Exception as e:
            print(f"Error toggling schedule: {e}")
            return False
