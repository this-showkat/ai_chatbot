# Generated by Django 5.2.3 on 2025-06-20 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0002_alter_user_user_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(choices=[('assistant', 'Assistant '), ('user', 'User')], default='user', max_length=30),
        ),
    ]
