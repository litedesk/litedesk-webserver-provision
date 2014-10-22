# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import model_utils.fields
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Offer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(max_length=500)),
                ('currency', models.CharField(max_length=50, choices=[(b'EUR', b'Euro'), (b'USD', b'US Dollar')])),
                ('price', models.DecimalField(max_digits=10, decimal_places=2)),
                ('setup_price', models.DecimalField(null=True, max_digits=10, decimal_places=2)),
                ('object_id', models.PositiveIntegerField()),
                ('status', model_utils.fields.StatusField(default=b'inactive', max_length=100, no_check_for_status=True, choices=[(b'inactive', b'inactive'), (b'available', b'available'), (b'retired', b'retired'), (b'suspended', b'suspended')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('account', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderLine',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', model_utils.fields.StatusField(default=b'ordered', max_length=100, no_check_for_status=True, choices=[(b'ordered', b'ordered'), (b'completed', b'completed'), (b'failed', b'failed'), (b'accepted', b'accepted'), (b'rejected', b'rejected'), (b'expired', b'expired')])),
                ('extra', picklefield.fields.PickledObjectField(editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('offer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='accounting.Offer')),
            ],
            options={
                'abstract': False,
            },
            bases=('accounting.offer',),
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('offer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='accounting.Offer')),
                ('period', models.CharField(max_length=30, choices=[(b'day', b'day'), (b'week', b'week'), (b'month', b'month'), (b'year', b'year')])),
            ],
            options={
                'abstract': False,
            },
            bases=('accounting.offer',),
        ),
        migrations.AddField(
            model_name='orderline',
            name='item',
            field=models.ForeignKey(to='accounting.Offer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderline',
            name='order',
            field=models.ForeignKey(to='accounting.Order'),
            preserve_default=True,
        ),
    ]
