# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('provisioning', '0006_auto_20141121_1704'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userprovisionable',
            unique_together=set([('user', 'service', 'item_type', 'object_id')]),
        ),
    ]
