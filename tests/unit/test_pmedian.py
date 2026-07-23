import sys
import os
import pandas as pd
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from shared.algorithms.greedy_pmedian import run_greedy_pmedian


def test_greedy_pmedian_selection():
    hubs = pd.DataFrame([
        {"hub_id": 1, "name": "Hub A", "lat": 10.770, "lon": 106.690},
        {"hub_id": 2, "name": "Hub B", "lat": 10.780, "lon": 106.700},
        {"hub_id": 3, "name": "Hub C", "lat": 10.790, "lon": 106.710}
    ])
    orders = pd.DataFrame([
        {"order_id": 101, "lat": 10.771, "lon": 106.691},
        {"order_id": 102, "lat": 10.781, "lon": 106.701}
    ])

    selected = run_greedy_pmedian(hubs, orders, num_hubs=2)
    assert len(selected) == 2
    assert 1 in selected["hub_id"].values or 2 in selected["hub_id"].values
