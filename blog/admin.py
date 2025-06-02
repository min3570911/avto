# 📁 blog/admin.py - Админка для раздела "Статьи"
# 🛠️ Настройка Django Admin с CKEditor 5
# ✅ СОВРЕМЕННО: Переход на django-ckeditor-5

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Article


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """📂 Админка для категорий статей"""
    list_display = ['name', 'slug', 'sort_order', 'get_articles_count', 'created_at']
    list_editable = ['sort_order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_filter = ['created_at']

    fieldsets = (
        ('🏷️ Основная информация', {
            'fields': ('name', 'slug', 'sort_order')
        }),
        ('📝 Описание и изображение', {
            'fields': ('description', 'image'),
            'classes': ('wide',),
        }),
    )

    def get_articles_count(self, obj):
        """📊 Количество статей в категории"""
        count = obj.get_articles_count()
        return format_html(
            '<span style="color: {};">{} статей</span>',
            'green' if count > 0 else 'gray',
            count
        )

    get_articles_count.short_description = 'Статей'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """📰 Админка для статей с CKEditor 5"""

    # 📋 Отображение в списке
    list_display = [
        'title',
        'category',
        'author',
        'is_published',
        'views',
        'published_at',
        'get_image_preview'
    ]
    list_filter = ['is_published', 'category', 'author', 'published_at']
    search_fields = ['title', 'excerpt', 'content']
    list_editable = ['is_published']
    date_hierarchy = 'published_at'

    # 🔧 Автозаполнение slug из title
    prepopulated_fields = {'slug': ('title',)}

    # 📝 Поля для редактирования
    fieldsets = (
        ('📋 Основная информация', {
            'fields': ('title', 'slug', 'category', 'author')
        }),
        ('🖼️ Изображение', {
            'fields': ('featured_image',),
            'classes': ('wide',),
        }),
        ('✍️ Краткое описание', {
            'fields': ('excerpt',),
            'classes': ('wide',),
            'description': '📝 Краткое описание статьи для карточки (использует CKEditor 5 с базовой конфигурацией)'
        }),
        ('📄 Полный текст статьи', {
            'fields': ('content',),
            'classes': ('wide', 'extra-wide-content'),
            'description': '📰 Полное содержание статьи (использует CKEditor 5 с расширенной конфигурацией для блога)'
        }),
        ('⚙️ Настройки публикации', {
            'fields': ('is_published', 'published_at'),
            'classes': ('collapse',),
        }),
        ('📊 Статистика', {
            'fields': ('views',),
            'classes': ('collapse',),
        }),
    )

    # 🔒 Только для чтения
    readonly_fields = ['views']

    def get_image_preview(self, obj):
        """🖼️ Превью изображения в списке"""
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px; object-fit: cover;" />',
                obj.featured_image.url
            )
        return '-'

    get_image_preview.short_description = 'Превью'

    def save_model(self, request, obj, form, change):
        """💾 Автоматическое назначение текущего пользователя автором"""
        if not change:  # Только при создании новой статьи
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """📝 Настройка формы"""
        form = super().get_form(request, obj, **kwargs)
        # Если создаем новую статью, устанавливаем текущего пользователя
        if not obj:
            form.base_fields['author'].initial = request.user
        return form

    class Media:
        """🎨 Дополнительные стили для админки"""
        css = {
            'all': ('blog/admin/article_admin.css',)
        }


# 🎯 Настройка заголовков админки для блога
admin.site.index_title = 'Управление сайтом автоковриков'

# 🔧 ИЗМЕНЕНИЯ:
# ✅ СОХРАНЕНО: Вся функциональность админки без изменений
# ✅ УЛУЧШЕНО: CKEditor 5 автоматически подключится через CKEditor5Field в моделях
# ✅ СОВРЕМЕННО: Новый интерфейс редактора с лучшей безопасностью и функционалом
#
# 📝 ПРИМЕЧАНИЕ:
# CKEditor 5 автоматически заменит стандартные textarea поля благодаря CKEditor5Field
# в моделях. Никаких дополнительных настроек в админке не требуется!