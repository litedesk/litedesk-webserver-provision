# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import jsonfield.fields
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
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('amount', models.DecimalField(max_digits=10, decimal_places=2)),
                ('currency', models.CharField(max_length=50, choices=[(b'EUR', b'Euro'), (b'USD', b'US Dollar')])),
                ('category', models.CharField(max_length=50, choices=[(b'platform', b'platform'), (b'software', b'software'), (b'devices', b'devices'), (b'other', b'other')])),
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
                ('start', models.DateTimeField(null=True, verbose_name='start', blank=True)),
                ('end', models.DateTimeField(null=True, verbose_name='end', blank=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('extra', jsonfield.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
