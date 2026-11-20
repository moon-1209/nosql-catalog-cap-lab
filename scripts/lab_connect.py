"""Ket noi ScyllaDB lab - dung chung cho moi experiment script.

Truoc day LocalAddressTranslator + contact_points + wait_cluster_ready bi
trung lap o 5 file (e1a, e1b, cap_matrix, lwt, counter). Gom ve day.

Uu tien chay BEN TRONG lab-net voi IP that:
    SCYLLA_CONTACT_POINTS=10.88.88.11,10.88.88.12,10.88.88.13
Chi dung 127.0.0.1 + translator khi chay tu host ngoai (fallback).
"""
import os
import time

from cassandra.cluster import Cluster
from cassandra.policies import AddressTranslator

DC = os.environ.get("SCYLLA_DC", "datacenter1")
DEFAULT_RF = int(os.environ.get("SCYLLA_RF", "3"))


class LocalAddressTranslator(AddressTranslator):
    """Fallback chay tu host ngoai lab-net.

    LUU Y: map moi host ve 127.0.0.1 lam driver khong nhin thay topology
    that -> KHONG dung cho thi nghiem CAP khi co the (day la mot phan
    nguyen nhan run CAP_ALL 18/11 fail 100%).
    """
    def translate(self, addr):
        return "127.0.0.1"


def contact_points():
    """Tra ve (points, translator|None) theo env SCYLLA_CONTACT_POINTS."""
    env = os.environ.get("SCYLLA_CONTACT_POINTS")
    if env:
        return [p.strip() for p in env.split(",") if p.strip()], None
    print("WARN: LocalAddressTranslator 127.0.0.1 - topology that bi an. "
          "Nen chay trong lab-net voi SCYLLA_CONTACT_POINTS.")
    return ["127.0.0.1"], LocalAddressTranslator()


def connect():
    """Cluster + session theo cau hinh env."""
    points, translator = contact_points()
    cluster = (Cluster(points, address_translator=translator)
               if translator else Cluster(points))
    return cluster, cluster.connect()


def up_nodes(cluster):
    return [h.address for h in cluster.metadata.all_hosts() if h.is_up]


def wait_cluster_ready(cluster, min_up=3, timeout_s=60, label=""):
    """Poll den khi >= min_up node UP. Tra ve so node up (0 neu timeout)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        n = len(up_nodes(cluster))
        if n >= min_up:
            if label:
                print(f"[{label}] {n} node UP")
            return n
        time.sleep(1)
    return len(up_nodes(cluster))


def ensure_keyspace(session, keyspace="catalog", rf=DEFAULT_RF):
    session.execute(
        "CREATE KEYSPACE IF NOT EXISTS %s WITH replication = "
        "{'class': 'NetworkTopologyStrategy', '%s': %d}"
        % (keyspace, DC, rf))
    session.set_keyspace(keyspace)
