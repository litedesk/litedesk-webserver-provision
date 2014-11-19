# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Charge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('status', model_utils.fields.StatusField(default=b'scheduled', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'scheduled', b'scheduled'), (b'waived', b'waived'), (b'pending', b'pending'), (b'paid', b'paid')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('code', models.CharField(unique=True, max_length=30)),
                ('amount', models.DecimalField(max_digits=10, decimal_places=2)),
                ('currency', models.CharField(max_length=50, choices=[(b'EUR', b'Euro'), (b'USD', b'US Dollar')])),
                ('amount_paid', models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True)),
                ('due_on', models.DateTimeField()),
                ('paid_on', models.DateTimeField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('active', models.BooleanField(default=True)),
                ('extra', jsonfield.fields.JSONField(default=dict)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
