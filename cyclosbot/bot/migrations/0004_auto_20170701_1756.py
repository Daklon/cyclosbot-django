# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-01 16:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_remove_telegramuser_django_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='telegramuser',
            old_name='conversation_status',
            new_name='conversation_flow',
        ),
    ]
