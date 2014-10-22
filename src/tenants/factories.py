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


import random

from django.contrib.auth import get_user_model
import factory

import models


BOYS_NAMES = [
    'Alexander', 'Andreas', 'Benjamin', 'Bernd', 'Christian', 'Daniel', 'David',
    'Dennis', 'Dieter', 'Dirk', 'Dominik', 'Eric', 'Felix', 'Florian',
    'Frank', 'Jan', 'Jens', 'Jonas', 'Jörg', 'Jürgen', 'Kevin',
    'Klaus', 'Leon', 'Lukas', 'Marcel', 'Marko', 'Mario', 'Markus',
    'Martin', 'Mathias', 'Max', 'Maximilian', 'Michael', 'Niklas', 'Patrick',
    'Paul', 'Peter', 'Philipp', 'Ralf', 'René', 'Robert', 'Sebastian',
    'Stephan', 'Steffen', 'Sven', 'Thomas', 'Thorsten', 'Tim', 'Tobias',
    'Tom', 'Ulrich', 'Uwe', 'Wolfgang'
    ]


GIRLS_NAMES = [
    'Andrea', 'Angelika', 'Anja', 'Anke', 'Anna, Anne', 'Annett', 'Antje',
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
    'Müller', 'Schmidt', 'Schneider', 'Fischer', 'Meyer', 'Weber', 'Schulz',
    'Wagner', 'Becker', 'Hoffmann'
]


def make_first_name(obj):
    return random.choice(random.choice([BOYS_NAMES, GIRLS_NAMES]))


def make_last_name(obj):
    return random.choice(SURNAMES)


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

    def _get_username(self):
        return '%s.%s' % (self.first_name.lower(), self.last_name.lower())

    tenant = factory.SubFactory(TenantFactory)
    email = factory.LazyAttribute(lambda obj: '%s@%s.de' % (obj.username, obj.tenant.name))
    first_name = factory.LazyAttribute(make_first_name)
    last_name = factory.LazyAttribute(make_last_name)
    username = factory.LazyAttribute(_get_username)
