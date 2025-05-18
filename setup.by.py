# products/management/commands/initialize_color_images.py

from django.core.management.base import BaseCommand
from products.models import Color


class Command(BaseCommand):
    help = 'Добавляет соответствующие файлы изображений для существующих цветов'

    def handle(self, *args, **kwargs):
        # Соответствия цветов и изображений для окантовки
        border_image_map = {
            'Черный': 'border211.png',
            'Серый': 'border212.png',
            'Коричневый': 'border213.png',
            'Бежевый': 'border214.png',
            'Синий': 'border215.png',
            'Темно-синий': 'border216.png',
            'Красный': 'border217.png',
            'Бордовый': 'border218.png',
            'Желтый': 'border219.png',
            'Зеленый': 'border220.png',
            'Темно-зеленый': 'border221.png',
            'Фиолетовый': 'border222.png',
            'Оранжевый': 'border223.png',
        }

        # Соответствия цветов и изображений для ковриков
        carpet_image_map = {
            'Черный': 'sota1.png',
            'Серый': 'sota2.png',
            'Коричневый': 'sota3.png',
            'Бежевый': 'sota4.png',
            'Синий': 'sota5.png',
            'Темно-синий': 'sota6.png',
            'Красный': 'sota7.png',
            'Бордовый': 'sota8.png',
            'Желтый': 'sota9.png',
            'Зеленый': 'sota10.png',
            'Темно-зеленый': 'sota11.png',
            'Фиолетовый': 'sota12.png',
            'Оранжевый': 'sota13.png',
        }

        # Получаем все существующие цвета
        colors = Color.objects.all()

        # Создаём счетчики
        carpet_count = 0
        border_count = 0

        # Устанавливаем типы и изображения для всех цветов
        for color in colors:
            # Определяем тип цвета по имени или оставляем как есть
            # Устанавливаем файл изображения
            if color.name in carpet_image_map:
                # Создаем/обновляем цвет для ковриков
                color.color_type = 'carpet'
                color.image_file = carpet_image_map[color.name]
                color.save()
                carpet_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Обновлен цвет коврика: {color.name} -> {color.image_file}')
                )

                # Дополнительно создаем цвет для окантовки с тем же именем, если его нет
                border_exists = Color.objects.filter(name=color.name, color_type='border').exists()
                if not border_exists and color.name in border_image_map:
                    Color.objects.create(
                        name=color.name,
                        hex_code=color.hex_code,
                        display_order=color.display_order,
                        color_type='border',
                        image_file=border_image_map[color.name],
                        is_available=True
                    )
                    border_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Создан новый цвет окантовки: {color.name} -> {border_image_map[color.name]}')
                    )

        # Итоговый отчет
        self.stdout.write(
            self.style.SUCCESS(f'Обновлено {carpet_count} цветов ковриков и {border_count} цветов окантовки')
        )