from django.core.management.base import BaseCommand
from django.db import transaction
from shop.models import Category, Product

class Command(BaseCommand):
    help = 'Добавить шесть демонстрационных часов; существующие товары не изменяются.'

    @transaction.atomic
    def handle(self, *args, **options):
        prx, _ = Category.objects.get_or_create(slug='prx', defaults={'name': 'PRX'})
        bellissima, _ = Category.objects.get_or_create(slug='bellissima', defaults={'name': 'Bellissima'})
        rows = [
            ('prx-green', prx, 'T137.410.11.091.00', 'Зелёный циферблат', 40, 'prx-green.jpg'),
            ('prx-blue', prx, 'T137.410.11.041.00', 'Синий циферблат', 40, 'prx-reference.jpg'),
            ('prx-silver', prx, 'T137.410.11.031.00', 'Серебристый циферблат', 40, 'prx-silver.jpg'),
            ('prx-black', prx, 'T137.410.11.051.00', 'Чёрный циферблат', 40, 'prx-black.jpg'),
            ('t126-pearl', bellissima, 'T126.010.11.133.00', 'Голубой перламутровый циферблат', 26, 't126-pearl.jpg'),
            ('t126-bicolor', bellissima, 'T126.010.22.013.01', 'Белый циферблат · двухцветный браслет', 26, 't126-bicolor.jpg'),
        ]
        count = 0
        for slug, category, reference, color, diameter, image in rows:
            _, created = Product.objects.get_or_create(reference=reference, defaults={
                'slug': slug, 'category': category, 'name': 'Tissot ' + category.name,
                'color': color, 'diameter': diameter, 'price': '20000.00', 'stock': 5,
                'image': 'watches/' + image,
                'description': 'Кварцевые часы Tissot со стальным браслетом и сапфировым стеклом. Выберите свою модель и оформите заказ.',
            })
            count += created
        self.stdout.write(self.style.SUCCESS(f'Добавлено товаров: {count}. Остатки демонстрационные.'))
