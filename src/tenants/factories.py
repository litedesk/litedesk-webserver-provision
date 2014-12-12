#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014, Deutsche Telekom AG - Laboratories (T-Labs)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unicodedata
import random

from django.contrib.auth import get_user_model
import factory

import models


BOYS_NAMES = [
    'Alexander', 'Andreas', 'Benjamin', 'Bernd', 'Christian', 'Daniel', 'David',
    'Dennis', 'Dieter', 'Dirk', 'Dominik', 'Eric', 'Felix', 'Florian',
    'Frank', 'Jan', 'Jens', 'Jonas', u'Jörg', u'Jürgen', 'Kevin',
    'Klaus', 'Leon', 'Lukas', 'Marcel', 'Marko', 'Mario', 'Markus',
    'Martin', 'Mathias', 'Max', 'Maximilian', 'Michael', 'Niklas', 'Patrick',
    'Paul', 'Peter', 'Philipp', 'Ralf', u'René', 'Robert', 'Sebastian',
    'Stephan', 'Steffen', 'Sven', 'Thomas', 'Thorsten', 'Tim', 'Tobias',
    'Tom', 'Ulrich', 'Uwe', 'Wolfgang'
    ]


GIRLS_NAMES = [
    'Andrea', 'Angelika', 'Anja', 'Anke', 'Anna', 'Anne', 'Annett', 'Antje',
    'Barbara', 'Birgit', 'Brigitte', 'Christin', 'Christina', 'Claudia', 'Daniela',
    'Diana', 'Doreen', 'Franziska', 'Gabriele', 'Heike', 'Ines', 'Jana',
    'Janina', 'Jennifer', 'Jessica', 'Julia', 'Juliane', 'Karin', 'Karolin',
    'Katharina', 'Katrin', 'Katja', 'Kerstin', 'Kristin', 'Laura', 'Lea',
    'Lena', 'Lisa', 'Mandy', 'Manuela', 'Maria', 'Marie', 'Marina',
    'Martina', 'Melanie', 'Monika', 'Nadine', 'Nicole', 'Petra', 'Sabine',
    'Sabrina', 'Sandra', 'Sara', 'Silke', 'Simone', 'Sophia', 'Stephanie',
    'Susanne', 'Tanja', 'Ulrike', 'Ursula', 'Vanessa', 'Yvonne',
]


SURNAMES = [
    u'Müller', 'Schmidt', 'Schneider', 'Fischer', 'Meyer', 'Weber', 'Schulz',
    'Wagner', 'Becker', 'Hoffmann', 'Smith', 'Johnson', 'Williams', 'Jones', 'Brown',
    'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin',
    'Thompson', 'Garcia', 'Martinez', 'Robinson', 'Clark', 'Rodriguez', 'Lewis', 'Lee',
    'Walker', 'Hall', 'Allen', 'Young', 'Hernandez', 'King', 'Wright', 'Lopez',
    'Hill', 'Scott', 'Green', 'Adams', 'Baker', 'Gonzalez', 'Nelson', 'Carter',
    'Mitchell', 'Perez', 'Roberts', 'Turner', 'Phillips', 'Campbell', 'Parker', 'Evans',
    'Edwards', 'Collins', 'Stewart', 'Sanchez', 'Morris', 'Rogers', 'Reed', 'Cook',
    'Morgan', 'Bell', 'Murphy', 'Bailey', 'Rivera', 'Cooper', 'Richardson', 'Cox',
    'Howard', 'Ward', 'Torres', 'Peterson', 'Gray', 'Ramirez', 'James', 'Watson',
    'Brooks', 'Kelly', 'Sanders', 'Price', 'Bennett', 'Wood', 'Barnes', 'Ross',
    'Henderson', 'Coleman', 'Jenkins', 'Perry', 'Powell', 'Long', 'Patterson', 'Hughes',
    'Flores', 'Washington', 'Butler', 'Simmons', 'Foster', 'Gonzales', 'Bryant', 'Alexander',
    'ussell', 'Griffin', 'Diaz', 'Hayes', 'Davis', 'Miller', 'Wilson'
]


def make_first_name(obj):
    return random.choice(random.choice([BOYS_NAMES, GIRLS_NAMES]))


def make_last_name(obj):
    return random.choice(SURNAMES)


def make_username(obj):
    def decode(name):
        return unicodedata.normalize('NFKD', unicode(name)).encode('ascii', 'ignore')

    return u'.'.join([decode(n).lower() for n in [
        obj.first_name, obj.last_name
        ]])


class AccountFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_user_model()

    username = factory.Sequence(lambda s: 'acme_account%05d' % s)
    first_name = factory.LazyAttribute(make_first_name)
    last_name = factory.LazyAttribute(make_last_name)


class TenantFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Tenant

    name = factory.Sequence(lambda s: 'company.%05d' % s)
    primary_contact = factory.SubFactory(AccountFactory)


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.User

    email = factory.LazyAttribute(lambda obj: '%s@mail.example.org' % (obj.username))
    username = factory.LazyAttribute(make_username)
    first_name = factory.LazyAttribute(make_first_name)
    last_name = factory.LazyAttribute(make_last_name)
