# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('provisioning', '0005_userprovisionable_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprovisionable',
            name='status',
            field=model_utils.fields.StatusField(default=b'staged', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(0, 'dummy')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprovisionable',
            name='status_changed',
            field=model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status'),
            preserve_default=True,
        ),
    ]
