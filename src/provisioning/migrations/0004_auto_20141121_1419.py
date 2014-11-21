# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('provisioning', '0003_tenantprovisionable'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprovisionable',
            name='offer',
        ),
        migrations.AddField(
            model_name='userprovisionable',
            name='item_type',
            field=models.ForeignKey(default=1, to='contenttypes.ContentType'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprovisionable',
            name='object_id',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
    ]
