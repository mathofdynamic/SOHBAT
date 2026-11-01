import math

from sohbat.ui.pill import Spring


def test_spring_interruption_preserves_position_and_velocity():
    spring = Spring(44)
    spring.target = 400
    for _ in range(5):
        spring.step(.016)
    position, velocity = spring.value, spring.velocity
    spring.target = 44
    assert (spring.value, spring.velocity) == (position, velocity)
    spring.step(.016)
    assert spring.value > position
    for _ in range(60):
        spring.step(.016)
    assert math.isclose(spring.value, 44, abs_tol=.01)


def test_spring_is_independent_of_frame_partition():
    continuous = Spring(44)
    sampled = Spring(44)
    continuous.target = sampled.target = 400
    continuous.step(.32)
    for _ in range(20):
        sampled.step(.016)
    assert math.isclose(sampled.value, continuous.value, abs_tol=1e-9)
    assert math.isclose(sampled.velocity, continuous.velocity, abs_tol=1e-9)
