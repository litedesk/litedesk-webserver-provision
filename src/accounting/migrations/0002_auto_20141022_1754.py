# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
        ('contenttypes', '0001_initial'),
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(to='tenants.User'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='offer',
            name='item_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='offer',
            name='tenant',
            field=models.ForeignKey(to='tenants.Tenant'),
            preserve_default=True,
        ),
    ]
