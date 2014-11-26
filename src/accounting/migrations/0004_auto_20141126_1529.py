# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
        ('accounting', '0003_auto_20141125_1543'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='charge',
            name='amount_paid',
        ),
        migrations.RemoveField(
            model_name='charge',
            name='code',
        ),
        migrations.RemoveField(
            model_name='charge',
            name='due_on',
        ),
        migrations.RemoveField(
            model_name='charge',
            name='paid_on',
        ),
        migrations.RemoveField(
            model_name='charge',
            name='status',
        ),
        migrations.RemoveField(
            model_name='charge',
            name='status_changed',
        ),
        migrations.RemoveField(
            model_name='charge',
            name='tenant',
        ),
        migrations.RemoveField(
            model_name='contract',
            name='active',
        ),
        migrations.RemoveField(
            model_name='contract',
            name='created',
        ),
        migrations.RemoveField(
            model_name='contract',
            name='modified',
        ),
        migrations.AddField(
            model_name='charge',
            name='user',
            field=models.ForeignKey(default=1, to='tenants.User'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contract',
            name='end',
            field=models.DateTimeField(null=True, verbose_name='end', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contract',
            name='quantity',
            field=models.PositiveIntegerField(default=1),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contract',
            name='start',
            field=models.DateTimeField(null=True, verbose_name='start', blank=True),
            preserve_default=True,
        ),
    ]
