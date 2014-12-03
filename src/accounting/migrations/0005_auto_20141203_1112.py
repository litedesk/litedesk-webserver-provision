# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0004_auto_20141127_1710'),
    ]

    operations = [
        migrations.AlterField(
            model_name='charge',
            name='amount',
            field=models.DecimalField(editable=False, max_digits=10, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='charge',
            name='contract',
            field=models.ForeignKey(editable=False, to='accounting.Contract'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='charge',
            name='currency',
            field=models.CharField(max_length=50, editable=False, choices=[(b'EUR', b'Euro'), (b'USD', b'US Dollar')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='charge',
            name='user',
            field=models.ForeignKey(editable=False, to='tenants.User'),
            preserve_default=True,
        ),
    ]
