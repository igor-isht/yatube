# Generated by Django 2.2.16 on 2022-03-12 15:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20220311_2027'),
    ]

    operations = [
        migrations.RenameField(
            model_name='follow',
            old_name='follower',
            new_name='user',
        ),
    ]