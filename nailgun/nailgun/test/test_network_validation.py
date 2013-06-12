# -*- coding: utf-8 -*-

import json

from nailgun.api.models import Network, NetworkGroup
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.settings import settings


class TestHandlers(BaseHandlers):

    def test_network_checking(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"pending_addition": True},
            ]
        )
        cluster = self.env.clusters[0]

        nets = self.env.generate_ui_networks(
            cluster.id
        )
        resp = self.app.put(
            reverse('NetworkConfigurationHandler',
                    kwargs={'cluster_id': cluster.id}),
            json.dumps(nets),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 202)
        task = json.loads(resp.body)
        self.assertEquals(task['status'], 'ready')
        self.assertEquals(task['progress'], 100)
        self.assertEquals(task['name'], 'check_networks')
        ngs_created = self.db.query(NetworkGroup).filter(
            NetworkGroup.name.in_([n['name'] for n in nets['networks']])
        ).all()
        self.assertEquals(len(ngs_created), len(nets['networks']))

    def test_network_checking_fails_if_admin_intersection(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"pending_addition": True},
            ]
        )
        cluster = self.env.clusters[0]
        nets = self.env.generate_ui_networks(cluster.id)
        nets['networks'][-1]["cidr"] = settings.NET_EXCLUDE[0]
        resp = self.app.put(
            reverse('NetworkConfigurationHandler',
                    kwargs={'cluster_id': cluster.id}),
            json.dumps(nets),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 400)
        task = json.loads(resp.body)
        self.assertEquals(task['status'], 'error')
        self.assertEquals(task['progress'], 100)
        self.assertEquals(task['name'], 'check_networks')
        self.assertEquals(
            task['message'],
            "Intersection with admin "
            "network(s) '{0}' found".format(
                settings.NET_EXCLUDE
            )
        )

    def test_network_checking_fails_if_amount_flatdhcp(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"pending_addition": True},
            ]
        )
        cluster = self.env.clusters[0]

        nets = self.env.generate_ui_networks(
            cluster.id
        )
        nets['networks'][-1]["amount"] = 2
        nets['networks'][-1]["cidr"] = "10.0.0.0/23"
        resp = self.app.put(
            reverse('NetworkConfigurationHandler',
                    kwargs={'cluster_id': cluster.id}),
            json.dumps(nets),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 400)
        task = json.loads(resp.body)
        self.assertEquals(task['status'], 'error')
        self.assertEquals(task['progress'], 100)
        self.assertEquals(task['name'], 'check_networks')
        self.assertEquals(
            task['message'],
            "Network amount for '{0}' is more than 1 "
            "while using FlatDHCP manager.".format(
                nets['networks'][-1]["name"]))
