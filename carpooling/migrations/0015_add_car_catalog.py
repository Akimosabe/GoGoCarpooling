from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpooling', '0014_fix_city_timezones_by_region'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarCatalog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('make', models.CharField(db_index=True, max_length=120, verbose_name='Марка')),
                ('model', models.CharField(db_index=True, max_length=120, verbose_name='Модель')),
            ],
            options={
                'verbose_name': 'Марка/модель',
                'verbose_name_plural': '7. Автомобили',
                'ordering': ['make', 'model'],
                'unique_together': {('make', 'model')},
            },
        ),
        migrations.AddIndex(
            model_name='carcatalog',
            index=models.Index(fields=['make', 'model'], name='carpooling_c_make_7c0b0d_idx'),
        ),
    ]
