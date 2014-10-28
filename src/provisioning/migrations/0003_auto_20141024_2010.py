# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('provisioning', '0002_auto_20141024_1515'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdevice',
            name='status',
            field=model_utils.fields.StatusField(default=b'staged', max_length=100, no_check_for_status=True, choices=[(0, 'dummy')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='usermobiledataplan',
            name='status',
            field=model_utils.fields.StatusField(default=b'staged', max_length=100, no_check_for_status=True, choices=[(0, 'dummy')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userplatform',
            name='status',
            field=model_utils.fields.StatusField(default=b'staged', max_length=100, no_check_for_status=True, choices=[(0, 'dummy')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='usersoftware',
            name='status',
            field=model_utils.fields.StatusField(default=b'staged', max_length=100, no_check_for_status=True, choices=[(0, 'dummy')]),
            preserve_default=True,
        ),
    ]
