# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='offer',
            field=models.ForeignKey(to='catalog.Offer'),
            preserve_default=True,
        ),
    ]
