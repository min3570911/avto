# 📁 blog/management/commands/create_sample_articles.py
# 🛠️ Management команда для создания тестовых статей

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from blog.models import Category, Article


class Command(BaseCommand):
    """🎯 Команда для создания тестовых статей в блоге"""
    help = 'Создает тестовые статьи для блога'

    def handle(self, *args, **options):
        """🚀 Основная логика команды"""

        # 👤 Получаем или создаем автора
        author, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'email': 'admin@example.com'
            }
        )
        if created:
            author.set_password('admin')
            author.save()
            self.stdout.write(self.style.SUCCESS('✅ Создан пользователь admin'))

        # 📂 Создаем категории
        categories_data = [
            {
                'name': 'Советы по выбору',
                'slug': 'sovety-po-vyboru',
                'description': 'Полезные советы по выбору автоковриков'
            },
            {
                'name': 'Установка и монтаж',
                'slug': 'ustanovka-i-montazh',
                'description': 'Инструкции по установке ковриков'
            },
            {
                'name': 'Уход и эксплуатация',
                'slug': 'uhod-i-ekspluataciya',
                'description': 'Как ухаживать за автоковриками'
            },
            {
                'name': 'Обзоры моделей',
                'slug': 'obzory-modeley',
                'description': 'Обзоры различных моделей ковриков'
            }
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Создана категория: {category.name}'))

        # 📰 Создаем тестовые статьи
        articles_data = [
            {
                'category_slug': 'sovety-po-vyboru',
                'title': 'Как выбрать коврики для BMW: полное руководство',
                'excerpt': '<p>Выбор автомобильных ковриков для BMW требует особого внимания к деталям. В этой статье мы расскажем о всех нюансах выбора.</p>',
                'content': '''
                    <h2>Почему важно правильно выбрать коврики для BMW</h2>
                    <p>BMW - это премиальный автомобиль, который требует соответствующих аксессуаров. Правильно подобранные коврики не только защищают салон, но и подчеркивают статус автомобиля.</p>

                    <h3>Основные критерии выбора</h3>
                    <ul>
                        <li>Точное соответствие модели автомобиля</li>
                        <li>Качество материалов</li>
                        <li>Тип крепления</li>
                        <li>Дизайн и цветовое решение</li>
                    </ul>

                    <h3>Материалы ковриков</h3>
                    <p>Для BMW мы рекомендуем следующие материалы:</p>
                    <ol>
                        <li><strong>EVA (ЭВА)</strong> - современный материал, сочетающий прочность и эластичность</li>
                        <li><strong>Резина высокого качества</strong> - классический вариант с отличными защитными свойствами</li>
                        <li><strong>Текстильные коврики</strong> - для летнего периода и аккуратных водителей</li>
                    </ol>
                '''
            },
            {
                'category_slug': 'ustanovka-i-montazh',
                'title': 'Пошаговая установка ковриков в салон автомобиля',
                'excerpt': '<p>Правильная установка автоковриков - залог их долгой службы и вашей безопасности. Следуйте нашей инструкции.</p>',
                'content': '''
                    <h2>Подготовка к установке</h2>
                    <p>Перед установкой новых ковриков необходимо тщательно подготовить салон автомобиля.</p>

                    <h3>Шаг 1: Удаление старых ковриков</h3>
                    <p>Аккуратно извлеките старые коврики, начиная с водительского места.</p>

                    <h3>Шаг 2: Очистка салона</h3>
                    <p>Тщательно пропылесосьте пол салона, удалите всю грязь и мусор.</p>

                    <h3>Шаг 3: Установка новых ковриков</h3>
                    <p>Начните с водительского коврика, убедитесь что он надежно зафиксирован креплениями.</p>
                '''
            },
            {
                'category_slug': 'uhod-i-ekspluataciya',
                'title': 'Как правильно ухаживать за EVA ковриками',
                'excerpt': '<p>EVA коврики неприхотливы в уходе, но правильная эксплуатация значительно продлит срок их службы.</p>',
                'content': '''
                    <h2>Регулярный уход за EVA ковриками</h2>
                    <p>EVA коврики - это современное решение для защиты салона, которое требует минимального ухода.</p>

                    <h3>Ежедневный уход</h3>
                    <ul>
                        <li>Вытряхивайте коврики от песка и мелкого мусора</li>
                        <li>Протирайте влажной тряпкой при необходимости</li>
                    </ul>

                    <h3>Еженедельная чистка</h3>
                    <p>Раз в неделю рекомендуется проводить более тщательную очистку:</p>
                    <ol>
                        <li>Извлеките коврики из салона</li>
                        <li>Промойте теплой водой с мягким моющим средством</li>
                        <li>Тщательно просушите перед установкой обратно</li>
                    </ol>
                '''
            },
            {
                'category_slug': 'obzory-modeley',
                'title': 'Обзор ковриков ELEMENT для Toyota Camry',
                'excerpt': '<p>Детальный обзор популярной модели ковриков ELEMENT для Toyota Camry всех поколений.</p>',
                'content': '''
                    <h2>Коврики ELEMENT для Toyota Camry</h2>
                    <p>ELEMENT - это проверенный производитель автомобильных ковриков с многолетним опытом.</p>

                    <h3>Преимущества модели</h3>
                    <ul>
                        <li>Точное повторение рельефа пола</li>
                        <li>Высокие бортики до 5 см</li>
                        <li>Надежные крепления</li>
                        <li>Экологичные материалы</li>
                    </ul>

                    <h3>Технические характеристики</h3>
                    <table>
                        <tr>
                            <th>Параметр</th>
                            <th>Значение</th>
                        </tr>
                        <tr>
                            <td>Материал</td>
                            <td>Термопластичный эластомер</td>
                        </tr>
                        <tr>
                            <td>Высота борта</td>
                            <td>5 см</td>
                        </tr>
                        <tr>
                            <td>Вес комплекта</td>
                            <td>4.5 кг</td>
                        </tr>
                    </table>
                '''
            }
        ]

        for article_data in articles_data:
            category = Category.objects.get(slug=article_data['category_slug'])

            # Генерируем slug из заголовка
            from django.utils.text import slugify
            base_slug = slugify(article_data['title'])
            slug = f"{base_slug}.html"

            article, created = Article.objects.get_or_create(
                slug=slug,
                defaults={
                    'title': article_data['title'],
                    'author': author,
                    'category': category,
                    'excerpt': article_data['excerpt'],
                    'content': article_data['content'],
                    'is_published': True,
                    'published_at': timezone.now(),
                    'featured_image': 'blog/articles/default.jpg'  # Заглушка
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Создана статья: {article.title}'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Все тестовые данные успешно созданы!'))
        self.stdout.write(
            self.style.WARNING('⚠️  Не забудьте загрузить реальные изображения для статей через админку.'))