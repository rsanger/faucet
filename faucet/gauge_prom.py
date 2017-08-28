"""Prometheus for Gauge."""

# Copyright (C) 2015 Research and Education Advanced Network New Zealand Ltd.
# Copyright (C) 2015--2017 The Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from prometheus_client import start_http_server
from prometheus_client import Gauge as PromGauge # avoid collision
try:
    from gauge_pollers import GaugePortStatsPoller
except ImportError:
    from faucet.gauge_pollers import GaugePortStatsPoller


class GaugePrometheusClient(object):
    """Wrapper for Prometheus client that is shared between all pollers."""

    running = False
    metrics = {}

    def __init__(self):
        for stat_name in (
                'bytes_in', 'bytes_out',
                'dropped_in', 'dropped_out', 'errors_in',
                'packets_in', 'packets_out'):
            export_name = '_'.join(('of', stat_name))
            self.metrics[stat_name] = PromGauge(
                export_name, '', ['dp_id', 'port_name'])

    def start(self, addr, port):
        """Start Prometheus client if not already running."""
        if not self.running:
            start_http_server(int(port), addr)
            self.running = True


class GaugePortStatsPrometheusPoller(GaugePortStatsPoller):
    """Exports port stats to Prometheus."""

    def __init__(self, conf, logger, prom_client):
        super(GaugePortStatsPrometheusPoller, self).__init__(
            conf, logger, prom_client)
        if not self.prom_client.running:
            self.prom_client.start(
                self.conf.prometheus_addr, self.conf.prometheus_port)

    def update(self, rcv_time, dp_id, msg):
        super(GaugePortStatsPrometheusPoller, self).update(rcv_time, dp_id, msg)
        for stat in msg.body:
            port_name = self._stat_port_name(msg, stat, dp_id)
            for stat_name, stat_val in self._format_port_stats('_', stat):
                if stat_name in self.prom_client.metrics:
                    self.prom_client.metrics[stat_name].labels(
                        dp_id=hex(dp_id), port_name=port_name).set(stat_val)
