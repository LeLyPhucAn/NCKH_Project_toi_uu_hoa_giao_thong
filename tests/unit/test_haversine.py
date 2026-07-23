import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from shared.utils.haversine import haversine_distance


def test_haversine_same_point():
    # Khoảng cách giữa 2 điểm trùng nhau phải bằng 0.0 km
    dist = haversine_distance(10.77214, 106.69833, 10.77214, 106.69833)
    assert abs(dist - 0.0) < 1e-5


def test_haversine_known_distance():
    # Khoảng cách giữa Ga Bến Thành và Bến Bạch Đằng (~1.1 km)
    dist = haversine_distance(10.77064, 106.69683, 10.77548, 106.70725)
    assert 0.8 < dist < 1.5
