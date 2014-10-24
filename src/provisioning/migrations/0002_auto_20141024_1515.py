# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('provisioning', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userdevice',
            unique_together=set([('user', 'device')]),
        ),
        migrations.AlterUniqueTogether(
            name='usermobiledataplan',
            unique_together=set([('user', 'mobile_data_plan')]),
        ),
        migrations.AlterUniqueTogether(
            name='userplatform',
            unique_together=set([('user', 'platform')]),
        ),
        migrations.AlterUniqueTogether(
            name='usersoftware',
            unique_together=set([('user', 'software')]),
        ),
    ]
