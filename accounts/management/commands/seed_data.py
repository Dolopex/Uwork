"""
python manage.py seed_data
Crea datos de prueba realistas: usuarios, trabajos, postulaciones,
calificaciones, notificaciones y tickets de soporte.
"""
import datetime
import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import Application, Job
from notifications.models import Notification
from reviews.models import Review
from support.models import SupportTicket

User = get_user_model()


# ──────────────────────────── helpers ────────────────────────────
def future(days):
    return (timezone.now() + datetime.timedelta(days=days)).date()


def past(days):
    return (timezone.now() - datetime.timedelta(days=days)).date()


def ago(days, hours=0):
    return timezone.now() - datetime.timedelta(days=days, hours=hours)


# ──────────────────────────── datos ─────────────────────────────
EMPLOYERS = [
    dict(username='techcorp',   first_name='TechCorp',    last_name='SAS',
         email='techcorp@demo.com',   rol='empleador',
         telefono='3001234567', direccion='Bogotá, Colombia',
         cedula='900123456'),
    dict(username='creativestudio', first_name='Creative',   last_name='Studio',
         email='creative@demo.com',  rol='empleador',
         telefono='3019876543', direccion='Medellín, Colombia',
         cedula='900654321'),
    dict(username='redacpro',   first_name='Redac',       last_name='Pro',
         email='redacpro@demo.com',  rol='empleador',
         telefono='3025551234', direccion='Cali, Colombia',
         cedula='900111222'),
]

STUDENTS = [
    dict(username='ana_garcia',   first_name='Ana',    last_name='García',
         email='ana@demo.com',      rol='estudiante',
         telefono='3101112233', direccion='Bogotá, Colombia',
         universidad='Universidad Nacional', carrera='Ingeniería de Sistemas', semestre=7,
         habilidades='Python, Django, React, JavaScript',
         cedula='1012345678'),
    dict(username='carlos_lopez', first_name='Carlos', last_name='López',
         email='carlos@demo.com',   rol='estudiante',
         telefono='3112223344', direccion='Medellín, Colombia',
         universidad='EAFIT', carrera='Diseño Gráfico', semestre=5,
         habilidades='Illustrator, Photoshop, Figma, UI/UX',
         cedula='1023456789'),
    dict(username='maria_mtz',    first_name='María',  last_name='Martínez',
         email='maria@demo.com',    rol='estudiante',
         telefono='3123334455', direccion='Cali, Colombia',
         universidad='Universidad del Valle', carrera='Comunicación Social', semestre=8,
         habilidades='Redacción, SEO, WordPress, Copywriting',
         cedula='1034567890'),
    dict(username='juan_perez',   first_name='Juan',   last_name='Pérez',
         email='juan@demo.com',     rol='estudiante',
         telefono='3134445566', direccion='Barranquilla, Colombia',
         universidad='Universidad del Norte', carrera='Administración', semestre=4,
         habilidades='Excel, PowerPoint, Análisis de datos',
         cedula='1045678901'),
    dict(username='sofia_ramirez',first_name='Sofía',  last_name='Ramírez',
         email='sofia@demo.com',    rol='estudiante',
         telefono='3145556677', direccion='Bucaramanga, Colombia',
         universidad='UIS', carrera='Lenguas Modernas', semestre=6,
         habilidades='Inglés C1, Francés B2, Traducción técnica',
         cedula='1056789012'),
]

JOBS_DATA = [
    # ── DISPONIBLES ──
    dict(titulo='Desarrollo de landing page en React',
         descripcion='Necesitamos una landing page moderna y responsive para nuestro nuevo producto SaaS. Debe incluir animaciones suaves, sección de precios, testimonios y formulario de contacto.',
         requisitos='Experiencia con React 18+. Conocimiento de Tailwind CSS o Bootstrap. Portafolio previo requerido.',
         habilidades_requeridas='React, JavaScript, CSS, HTML',
         pago=320000, categoria='tecnologia', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='2 semanas', urgente=True,
         fecha_limite=future(10), estado='disponible', emp='techcorp'),

    dict(titulo='Diseño de identidad visual para startup',
         descripcion='Startup de fintech busca diseñador para crear su identidad visual completa: logotipo, paleta de colores, tipografías, y manual de marca en PDF.',
         requisitos='Experiencia en branding. Manejo de Adobe Illustrator. Entrega en formatos AI, SVG y PNG.',
         habilidades_requeridas='Illustrator, Branding, Diseño vectorial',
         pago=250000, categoria='diseno', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='1 semana', urgente=False,
         fecha_limite=future(14), estado='disponible', emp='creativestudio'),

    dict(titulo='Redacción de 10 artículos SEO',
         descripcion='Blog de viajes requiere 10 artículos optimizados para SEO, cada uno de mínimo 1200 palabras. Temas relacionados con destinos turísticos colombianos.',
         requisitos='Conocimiento de SEO on-page. Buena ortografía y redacción. Uso de herramientas como Surfer SEO o similar.',
         habilidades_requeridas='Redacción, SEO, WordPress',
         pago=180000, categoria='redaccion', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='10 días', urgente=False,
         fecha_limite=future(12), estado='disponible', emp='redacpro'),

    dict(titulo='Traducción de manual técnico (inglés → español)',
         descripcion='Manual de usuario de software de contabilidad (45 páginas) que debe ser traducido del inglés al español colombiano. Se requiere conocimiento de terminología financiera.',
         requisitos='Nivel C1 de inglés certificado o demostrable. Conocimiento de vocabulario financiero/contable.',
         habilidades_requeridas='Inglés C1, Traducción técnica, Terminología financiera',
         pago=210000, categoria='traduccion', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='5 días', urgente=True,
         fecha_limite=future(6), estado='disponible', emp='techcorp'),

    dict(titulo='Tutoría de cálculo diferencial',
         descripcion='Estudiante universitario requiere clases de refuerzo en cálculo diferencial. Se necesitan al menos 8 sesiones de 1.5 horas. Temas: límites, derivadas, regla de la cadena y optimización.',
         requisitos='Estar cursando o haber cursado Ingeniería o Matemáticas. Paciencia y habilidad pedagógica.',
         habilidades_requeridas='Cálculo diferencial, Pedagogía, Matemáticas',
         pago=160000, categoria='academico', modalidad='presencial',
         ubicacion='Bogotá, Colombia', duracion_estimada='3 semanas', urgente=False,
         fecha_limite=future(20), estado='disponible', emp='creativestudio'),

    dict(titulo='Automatización de reportes en Excel con macros',
         descripcion='Empresa contable necesita automatizar la generación de reportes mensuales usando macros VBA en Excel. Se tienen 3 plantillas que deben ser automatizadas.',
         requisitos='Experiencia con VBA para Excel. Entrega de archivos .xlsm documentados.',
         habilidades_requeridas='Excel, VBA, Macros',
         pago=190000, categoria='tecnologia', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='1 semana', urgente=False,
         fecha_limite=future(18), estado='disponible', emp='redacpro'),

    # ── EN PROCESO ──
    dict(titulo='App móvil de seguimiento de hábitos (Flutter)',
         descripcion='Desarrollo de app móvil multiplataforma en Flutter para seguimiento de hábitos diarios. Incluye notificaciones push, estadísticas semanales y sincronización en la nube.',
         requisitos='Experiencia con Flutter y Dart. Conocimiento de Firebase. Publicación en Play Store.',
         habilidades_requeridas='Flutter, Dart, Firebase',
         pago=480000, categoria='tecnologia', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='1 mes', urgente=False,
         fecha_limite=future(25), estado='en_proceso', emp='techcorp',
         asignado_to='ana_garcia'),

    dict(titulo='Rediseño de interfaz de panel administrativo',
         descripcion='Panel administrativo web heredado que necesita un rediseño completo de UX/UI. Actualmente usa Bootstrap 3, se requiere migrar a Figma primero y luego implementar.',
         requisitos='Dominio de Figma. Experiencia en diseño de dashboards. Conocimiento de Bootstrap 5.',
         habilidades_requeridas='Figma, UI/UX, Bootstrap, Diseño',
         pago=350000, categoria='diseno', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='3 semanas', urgente=True,
         fecha_limite=future(15), estado='en_proceso', emp='creativestudio',
         asignado_to='carlos_lopez'),

    dict(titulo='Gestión de redes sociales para restaurante',
         descripcion='Restaurante de comida italiana en Bogotá necesita community manager para manejar Instagram y Facebook: 2 publicaciones diarias, stories, respuesta a comentarios.',
         requisitos='Experiencia en manejo de redes. Conocimiento de herramientas de diseño básico (Canva). Disponibilidad de 2h diarias.',
         habilidades_requeridas='Community Manager, Canva, Redes sociales',
         pago=220000, categoria='redaccion', modalidad='remoto',
         ubicacion='Bogotá, Colombia', duracion_estimada='1 mes', urgente=False,
         fecha_limite=future(30), estado='en_proceso', emp='redacpro',
         asignado_to='maria_mtz'),

    dict(titulo='Análisis de datos de ventas con Python',
         descripcion='Empresa de retail necesita análisis exploratorio de su dataset de ventas (CSV, ~50k filas). Se requiere limpieza de datos, visualizaciones con matplotlib/seaborn y reporte en Jupyter.',
         requisitos='Dominio de pandas y matplotlib. Entrega de notebook documentado y PDF del reporte.',
         habilidades_requeridas='Python, Pandas, Matplotlib, Jupyter',
         pago=290000, categoria='tecnologia', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='1 semana', urgente=True,
         fecha_limite=future(7), estado='en_proceso', emp='techcorp',
         asignado_to='ana_garcia'),

    # ── FINALIZADOS ──
    dict(titulo='Diseño de presentación corporativa (PowerPoint)',
         descripcion='Presentación de 20 diapositivas para pitch ante inversionistas. Incluye infografías, visualización de datos y animaciones profesionales.',
         requisitos='Dominio de PowerPoint o Google Slides. Buen ojo estético. Entrega en PPTX y PDF.',
         habilidades_requeridas='PowerPoint, Diseño, Infografías',
         pago=150000, categoria='diseno', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='3 días', urgente=False,
         fecha_limite=past(5), estado='finalizado', emp='creativestudio',
         asignado_to='carlos_lopez'),

    dict(titulo='Transcripción y corrección de estilo de entrevistas',
         descripcion='15 entrevistas en audio (total ~6 horas) deben ser transcritas y corregidas de estilo para publicación en revista digital.',
         requisitos='Velocidad de escritura >60 ppm. Buen manejo del español. Confidencialidad.',
         habilidades_requeridas='Transcripción, Redacción, Corrección de estilo',
         pago=200000, categoria='redaccion', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='1 semana', urgente=False,
         fecha_limite=past(10), estado='finalizado', emp='redacpro',
         asignado_to='maria_mtz'),

    dict(titulo='Integración de pasarela de pagos (Wompi)',
         descripcion='E-commerce en Django necesita integrar Wompi como pasarela de pagos. Incluye flujo de checkout, webhooks para actualización de pedidos y página de confirmación.',
         requisitos='Experiencia con Django. Conocimiento de APIs REST. Lectura de documentación de Wompi.',
         habilidades_requeridas='Django, Python, REST API, Wompi',
         pago=380000, categoria='tecnologia', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='5 días', urgente=True,
         fecha_limite=past(15), estado='finalizado', emp='techcorp',
         asignado_to='ana_garcia'),

    dict(titulo='Traducción de subtítulos para curso online',
         descripcion='Curso de marketing digital en inglés (8 módulos, ~4 horas de video) necesita subtítulos traducidos al español en formato SRT.',
         requisitos='Nivel C1 de inglés. Conocimiento de terminología de marketing digital. Formato de entrega: SRT.',
         habilidades_requeridas='Inglés C1, Traducción, Formato SRT',
         pago=175000, categoria='traduccion', modalidad='remoto',
         ubicacion='Remoto', duracion_estimada='4 días', urgente=False,
         fecha_limite=past(8), estado='finalizado', emp='creativestudio',
         asignado_to='sofia_ramirez'),

    dict(titulo='Asesoría académica en estadística para tesis',
         descripcion='Estudiante de maestría necesita asesoría en análisis estadístico de su investigación: regresión múltiple, ANOVA y análisis de correlación en SPSS.',
         requisitos='Conocimiento avanzado de estadística. Manejo de SPSS o R. Disponibilidad de 3 sesiones presenciales.',
         habilidades_requeridas='Estadística, SPSS, Análisis de datos, Pedagogía',
         pago=280000, categoria='academico', modalidad='presencial',
         ubicacion='Bucaramanga, Colombia', duracion_estimada='2 semanas', urgente=False,
         fecha_limite=past(20), estado='finalizado', emp='redacpro',
         asignado_to='juan_perez'),
]

REVIEW_COMMENTS = [
    (5, 'Excelente trabajo, superó mis expectativas. Muy profesional y entregó antes del plazo.'),
    (5, 'Increíble calidad y atención al detalle. Definitivamente volvería a contratar.'),
    (4, 'Muy buen trabajo. Pequeños ajustes necesarios al final pero quedó perfecto.'),
    (4, 'Cumplió con todo lo acordado. Buena comunicación durante el proceso.'),
    (5, 'Trabajo impecable. La comunicación fue excelente durante todo el proyecto.'),
    (3, 'El resultado fue aceptable, aunque tardó un poco más de lo esperado.'),
    (5, 'Profesional, puntual y con mucho talento. Muy recomendado.'),
    (4, 'Buen trabajo, se comprometió con la calidad. Lo recomiendo.'),
]

SUPPORT_TICKETS = [
    dict(tipo='bug',     descripcion='Al intentar subir una imagen de perfil mayor a 2MB la app se congela y no muestra mensaje de error. Sucede en Chrome y Firefox.'),
    dict(tipo='usuario', descripcion='El empleador "techcorp" me prometió pago adicional fuera de la plataforma y luego no cumplió. Guardo los mensajes como evidencia.'),
    dict(tipo='pago',    descripcion='El trabajo fue marcado como finalizado hace 5 días pero mi saldo no refleja el pago. El estado aparece como completado en el sistema.'),
    dict(tipo='bug',     descripcion='En la vista móvil el botón de "Postularme" aparece cortado en dispositivos con pantalla pequeña (360px de ancho).'),
    dict(tipo='otro',    descripcion='Quisiera que se agregue la opción de filtrar trabajos por rango de pago en la vista de explorar.'),
]


class Command(BaseCommand):
    help = 'Crea datos de prueba en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true',
                            help='Elimina todos los datos existentes primero')

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write('Eliminando datos existentes...')
            Review.objects.all().delete()
            Application.objects.all().delete()
            Job.objects.all().delete()
            Notification.objects.all().delete()
            SupportTicket.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        self.stdout.write('Creando usuarios...')
        emp_objs = {}
        for data in EMPLOYERS:
            u, created = User.objects.get_or_create(username=data['username'], defaults={
                **{k: v for k, v in data.items() if k != 'username'},
            })
            if created:
                u.set_password('demo1234')
                u.save()
            emp_objs[data['username']] = u
            self.stdout.write(f'  Empleador: {u.get_full_name()} ({"creado" if created else "ya existía"})')

        stu_objs = {}
        for data in STUDENTS:
            u, created = User.objects.get_or_create(username=data['username'], defaults={
                **{k: v for k, v in data.items() if k not in ('username',)},
            })
            if created:
                u.set_password('demo1234')
                u.save()
            stu_objs[data['username']] = u
            self.stdout.write(f'  Estudiante: {u.get_full_name()} ({"creado" if created else "ya existía"})')

        self.stdout.write('Creando trabajos...')
        # Map each job index to months ago for created_at backdating
        # disponibles: spread across last 2 months (0-1 months ago)
        # en_proceso:  1-3 months ago
        # finalizados: 2-5 months ago
        created_ago_months = [0, 0, 1, 1, 0, 1,   # disponibles (indices 0-5)
                               2, 2, 3, 3,          # en_proceso  (indices 6-9)
                               4, 3, 5, 4, 5]       # finalizados (indices 10-14)

        job_objs = []
        for idx, d in enumerate(JOBS_DATA):
            emp = emp_objs[d['emp']]
            asignado = stu_objs.get(d.get('asignado_to'))
            job, created = Job.objects.get_or_create(
                titulo=d['titulo'],
                creador=emp,
                defaults=dict(
                    descripcion=d['descripcion'],
                    requisitos=d.get('requisitos', ''),
                    habilidades_requeridas=d.get('habilidades_requeridas', ''),
                    pago=Decimal(str(d['pago'])),
                    categoria=d['categoria'],
                    modalidad=d['modalidad'],
                    ubicacion=d.get('ubicacion', ''),
                    duracion_estimada=d.get('duracion_estimada', ''),
                    urgente=d.get('urgente', False),
                    fecha_limite=d['fecha_limite'],
                    estado=d['estado'],
                    asignado=asignado,
                ),
            )
            # Backdate created_at (bypass auto_now_add with update())
            months_back = created_ago_months[idx] if idx < len(created_ago_months) else 0
            backdated = timezone.now() - datetime.timedelta(days=months_back * 30 + random.randint(0, 12))
            Job.objects.filter(pk=job.pk).update(created_at=backdated)
            job.created_at = backdated
            job_objs.append(job)
            self.stdout.write(f'  Trabajo: {job.titulo[:50]} [{job.estado}] ({"creado" if created else "ya existía"})')

        self.stdout.write('Creando postulaciones...')
        all_students = list(stu_objs.values())
        for job in job_objs:
            asignado = job.asignado
            # Reference date slightly after job creation
            job_date = job.created_at

            # For non-available jobs, create the accepted application
            if asignado and job.estado in ('en_proceso', 'finalizado'):
                app, _ = Application.objects.get_or_create(
                    usuario=asignado, trabajo=job,
                    defaults=dict(
                        mensaje='Me interesa mucho este proyecto. Tengo experiencia relevante y puedo comenzar de inmediato.',
                        estado=Application.Estado.ACEPTADA,
                    )
                )
                Application.objects.filter(pk=app.pk).update(
                    created_at=job_date + datetime.timedelta(days=random.randint(1, 3))
                )
                # Add 1-2 rejected applicants
                others = [s for s in all_students if s != asignado]
                for s in random.sample(others, min(2, len(others))):
                    app2, _ = Application.objects.get_or_create(
                        usuario=s, trabajo=job,
                        defaults=dict(
                            mensaje='Estoy interesado en este trabajo y creo que puedo aportar mucho.',
                            estado=Application.Estado.RECHAZADA,
                        )
                    )
                    Application.objects.filter(pk=app2.pk).update(
                        created_at=job_date + datetime.timedelta(days=random.randint(1, 5))
                    )

            # For available jobs, create 1-3 pending applications
            elif job.estado == 'disponible':
                applicants = random.sample(all_students, min(random.randint(1, 3), len(all_students)))
                for s in applicants:
                    app3, _ = Application.objects.get_or_create(
                        usuario=s, trabajo=job,
                        defaults=dict(
                            mensaje='Me gustaría aplicar a esta oferta. Cuento con las habilidades requeridas.',
                            estado=Application.Estado.PENDIENTE,
                        )
                    )
                    Application.objects.filter(pk=app3.pk).update(
                        created_at=job_date + datetime.timedelta(days=random.randint(0, 4))
                    )

        self.stdout.write('Creando calificaciones...')
        finished_jobs = [j for j in job_objs if j.estado == 'finalizado' and j.asignado]
        comment_pool = REVIEW_COMMENTS.copy()
        random.shuffle(comment_pool)
        for i, job in enumerate(finished_jobs):
            puntuacion, comentario = comment_pool[i % len(comment_pool)]
            # Employer → Student
            Review.objects.get_or_create(
                autor=job.creador, receptor=job.asignado, trabajo=job,
                defaults=dict(puntuacion=puntuacion, comentario=comentario)
            )
            # Student → Employer
            puntuacion2, comentario2 = comment_pool[(i + 1) % len(comment_pool)]
            Review.objects.get_or_create(
                autor=job.asignado, receptor=job.creador, trabajo=job,
                defaults=dict(puntuacion=puntuacion2, comentario=comentario2)
            )

        # Update calificacion_promedio for all users
        from django.db.models import Avg
        for u in list(emp_objs.values()) + list(stu_objs.values()):
            avg = u.reviews_recibidas.aggregate(avg=Avg('puntuacion'))['avg']
            u.calificacion_promedio = Decimal(str(round(avg, 2))) if avg else Decimal('0')
            u.save(update_fields=['calificacion_promedio'])

        self.stdout.write('Creando notificaciones...')
        notifs = []
        for job in job_objs:
            if job.estado in ('en_proceso', 'finalizado') and job.asignado:
                # Accepted notification for student
                notifs.append(Notification(
                    usuario=job.asignado,
                    tipo=Notification.Tipo.ACEPTADO,
                    mensaje=f'¡Felicitaciones! Fuiste aceptado para "{job.titulo}".',
                    link=f'/jobs/job/{job.pk}/',
                    leida=job.estado == 'finalizado',
                ))
                # New application notification for employer
                notifs.append(Notification(
                    usuario=job.creador,
                    tipo=Notification.Tipo.POSTULACION,
                    mensaje=f'{job.asignado.get_full_name()} se postuló a "{job.titulo}".',
                    link=f'/jobs/job/{job.pk}/applicants/',
                    leida=True,
                ))
            if job.estado == 'finalizado' and job.asignado:
                notifs.append(Notification(
                    usuario=job.asignado,
                    tipo=Notification.Tipo.FINALIZADO,
                    mensaje=f'El trabajo "{job.titulo}" fue marcado como finalizado.',
                    link=f'/jobs/job/{job.pk}/',
                    leida=True,
                ))
                notifs.append(Notification(
                    usuario=job.asignado,
                    tipo=Notification.Tipo.RESENA,
                    mensaje=f'Recibiste una calificación por "{job.titulo}".',
                    link=f'/jobs/job/{job.pk}/',
                    leida=False,
                ))

        # Some unread notifications for available jobs
        for job in [j for j in job_objs if j.estado == 'disponible']:
            apps = Application.objects.filter(trabajo=job)
            for app in apps[:2]:
                notifs.append(Notification(
                    usuario=job.creador,
                    tipo=Notification.Tipo.POSTULACION,
                    mensaje=f'{app.usuario.get_full_name()} se postuló a "{job.titulo}".',
                    link=f'/jobs/job/{job.pk}/applicants/',
                    leida=False,
                ))

        Notification.objects.bulk_create(notifs, ignore_conflicts=False)
        self.stdout.write(f'  {len(notifs)} notificaciones creadas')

        self.stdout.write('Creando tickets de soporte...')
        all_users = list(stu_objs.values()) + list(emp_objs.values())
        for i, t in enumerate(SUPPORT_TICKETS):
            reporter = all_users[i % len(all_users)]
            reported = None
            if t['tipo'] == 'usuario':
                reported = all_users[(i + 1) % len(all_users)]
            SupportTicket.objects.get_or_create(
                reporter=reporter,
                descripcion=t['descripcion'],
                defaults=dict(
                    tipo=t['tipo'],
                    usuario_reportado=reported,
                    estado=random.choice(['abierto', 'en_revision', 'resuelto']),
                )
            )

        self.stdout.write(self.style.SUCCESS(
            '\n✅ Datos de prueba creados exitosamente.\n'
            '   Credenciales: usuario / demo1234\n'
            '   Empleadores: techcorp, creativestudio, redacpro\n'
            '   Estudiantes: ana_garcia, carlos_lopez, maria_mtz, juan_perez, sofia_ramirez'
        ))
