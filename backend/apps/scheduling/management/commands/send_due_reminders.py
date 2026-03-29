from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from scheduling.models import AppointmentReminder


class Command(BaseCommand):
    help = "Envia recordatorios vencidos y los marca como SENT o FAILED."

    def handle(self, *args, **options):
        now = timezone.now()

        due_reminders = AppointmentReminder.objects.select_related(
            "appointment__patient",
            "appointment__doctor",
        ).filter(
            status=AppointmentReminder.Status.PENDING,
            scheduled_for__lte=now,
        ).order_by("scheduled_for")

        total = due_reminders.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No hay recordatorios pendientes por enviar."))
            return

        sent_count = 0
        failed_count = 0

        for reminder in due_reminders:
            try:
                if reminder.channel == AppointmentReminder.Channel.EMAIL:
                    patient = reminder.appointment.patient
                    to_email = getattr(patient, "email", "")

                    if not to_email:
                        raise ValueError("El paciente no tiene email registrado.")

                    subject = "Recordatorio de cita medica"
                    message = (
                        f"Hola {patient.username},\n\n"
                        f"Este es un recordatorio de tu cita programada para "
                        f"{reminder.appointment.scheduled_at}.\n\n"
                        f"Motivo: {reminder.appointment.reason or 'Sin motivo especificado'}\n\n"
                        f"Clinica Inteligente API"
                    )

                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[to_email],
                        fail_silently=False,
                    )
                else:
                    raise NotImplementedError(
                        f"Canal {reminder.channel} aun no implementado para envio real."
                    )

                reminder.status = AppointmentReminder.Status.SENT
                reminder.sent_at = now
                reminder.error_message = ""
                reminder.save(update_fields=["status", "sent_at", "error_message", "updated_at"])
                sent_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Reminder {reminder.id} enviado para appointment {reminder.appointment_id} via {reminder.channel}"
                    )
                )

            except Exception as exc:
                reminder.status = AppointmentReminder.Status.FAILED
                reminder.error_message = str(exc)[:255]
                reminder.save(update_fields=["status", "error_message", "updated_at"])
                failed_count += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"Reminder {reminder.id} fallo: {reminder.error_message}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Proceso finalizado. Enviados: {sent_count}, Fallidos: {failed_count}, Total: {total}"
            )
        )
