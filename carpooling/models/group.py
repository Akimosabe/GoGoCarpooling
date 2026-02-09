from django.contrib.auth.models import Group as BaseGroup


class Group(BaseGroup):
    """Прокси-модель для групп, чтобы отображалась в нашем приложении"""
    
    class Meta:
        proxy = True
        verbose_name = "Группа"
        verbose_name_plural = "8. Группы"
        app_label = 'carpooling'
