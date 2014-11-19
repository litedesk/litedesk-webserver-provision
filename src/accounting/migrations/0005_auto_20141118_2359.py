# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0004_auto_20141118_2340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='charge',
            name='amount_paid',
            field=models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True),
            preserve_default=True,
        ),
    ]
