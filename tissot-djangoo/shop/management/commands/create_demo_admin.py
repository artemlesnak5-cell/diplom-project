import secrets
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Создать локального администратора и записать пароль в DEMO_ACCESS.txt (только DEBUG).'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Команда доступна только для локальной демонстрации.')
        if User.objects.filter(username='demo_admin').exists():
            self.stdout.write('Администратор уже существует; пароль не изменён.')
            return
        password = secrets.token_urlsafe(18)
        User.objects.create_superuser(username='demo_admin', email='admin@example.com', password=password)
        (settings.BASE_DIR / 'DEMO_ACCESS.txt').write_text(
            'ДОСТУП ДЛЯ ЛОКАЛЬНОЙ ДЕМОНСТРАЦИИ\n\n'
            'Админка: http://127.0.0.1:8000/admin/\n'
            'Логин: demo_admin\nПароль: ' + password + '\n\n'
            'Не отправляйте этот файл вместе с дипломом и не используйте этот аккаунт на публичном сервере.\n'
            'Покупателя зарегистрируйте через сайт. Для показа используйте вымышленные данные.\n', encoding='utf-8')
        self.stdout.write(self.style.SUCCESS('Администратор создан. Доступ сохранён в DEMO_ACCESS.txt.'))
