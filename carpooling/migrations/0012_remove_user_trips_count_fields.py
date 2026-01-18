from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('carpooling', '0011_alter_user_avatar'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='trips_as_driver',
        ),
        migrations.RemoveField(
            model_name='user',
            name='trips_as_passenger',
        ),
    ]
