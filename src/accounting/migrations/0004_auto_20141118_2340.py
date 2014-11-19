# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0003_auto_20141118_1150'),
    ]

    operations = [
        migrations.AddField(
            model_name='charge',
            name='amount',
            field=models.DecimalField(default=0, max_digits=10, decimal_places=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='charge',
            name='amount_paid',
            field=models.DecimalField(default=0, max_digits=10, decimal_places=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='charge',
            name='currency',
            field=models.CharField(default=1, max_length=50, choices=[(b'EUR', b'Euro'), (b'USD', b'US Dollar')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='charge',
            name='due_on',
            field=models.DateTimeField(default=datetime.datetime(2014, 11, 18, 23, 40, 28, 285144)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='charge',
            name='paid_on',
            field=models.DateTimeField(null=True),
            preserve_default=True,
        ),
    ]
