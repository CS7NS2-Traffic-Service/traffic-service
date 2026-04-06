from services.osrm import _extract_steps_with_edges


def _make_leg(nodes, steps):
    return {
        'annotation': {'nodes': nodes},
        'steps': steps,
    }


def _make_step(name, num_coords, distance=100):
    return {
        'name': name,
        'distance': distance,
        'geometry': {'coordinates': [[0, 0]] * num_coords},
    }


class TestExtractStepsWithEdges:
    def test_single_step_produces_correct_edges(self):
        leg = _make_leg(
            nodes=[100, 200, 300],
            steps=[_make_step('Lime Street', 3)],
        )
        result = _extract_steps_with_edges(leg)
        assert len(result) == 1
        assert result[0]['name'] == 'Lime Street'
        assert result[0]['edge_ids'] == ['100-200', '200-300']

    def test_edge_ids_are_direction_independent(self):
        leg = _make_leg(
            nodes=[500, 200, 800],
            steps=[_make_step('Main Road', 3)],
        )
        result = _extract_steps_with_edges(leg)
        assert result[0]['edge_ids'] == ['200-500', '200-800']

    def test_multiple_steps_produce_separate_edge_lists(self):
        leg = _make_leg(
            nodes=[10, 20, 30, 40, 50],
            steps=[
                _make_step('First Street', 3),
                _make_step('Second Street', 3),
            ],
        )
        result = _extract_steps_with_edges(leg)
        assert len(result) == 2
        assert result[0]['name'] == 'First Street'
        assert result[0]['edge_ids'] == ['10-20', '20-30']
        assert result[1]['name'] == 'Second Street'
        assert result[1]['edge_ids'] == ['30-40', '40-50']

    def test_zero_distance_step_is_skipped(self):
        leg = _make_leg(
            nodes=[10, 20, 30],
            steps=[
                _make_step('Real Road', 2),
                _make_step('', 2, distance=0),
            ],
        )
        result = _extract_steps_with_edges(leg)
        assert len(result) == 1
        assert result[0]['name'] == 'Real Road'

    def test_empty_nodes_returns_empty(self):
        leg = _make_leg(nodes=[], steps=[_make_step('Road', 3)])
        result = _extract_steps_with_edges(leg)
        assert result == []

    def test_single_node_returns_empty(self):
        leg = _make_leg(nodes=[100], steps=[_make_step('Road', 1)])
        result = _extract_steps_with_edges(leg)
        assert result == []


class TestEdgeOverlapMatching:
    def test_overlapping_routes_share_edges(self):
        route_a_nodes = [10, 20, 30, 40, 50]
        route_b_nodes = [30, 40, 50, 60, 70]

        leg_a = _make_leg(route_a_nodes, [_make_step('Lime Street', 5)])
        leg_b = _make_leg(route_b_nodes, [_make_step('Lime Street', 5)])

        edges_a = _extract_steps_with_edges(leg_a)[0]['edge_ids']
        edges_b = _extract_steps_with_edges(leg_b)[0]['edge_ids']

        overlap = set(edges_a) & set(edges_b)
        assert len(overlap) > 0, 'Routes on same road should share edges'
        assert '30-40' in overlap
        assert '40-50' in overlap

    def test_disjoint_routes_share_no_edges(self):
        leg_a = _make_leg([10, 20, 30], [_make_step('Street A', 3)])
        leg_b = _make_leg([40, 50, 60], [_make_step('Street B', 3)])

        edges_a = _extract_steps_with_edges(leg_a)[0]['edge_ids']
        edges_b = _extract_steps_with_edges(leg_b)[0]['edge_ids']

        overlap = set(edges_a) & set(edges_b)
        assert len(overlap) == 0

    def test_partial_overlap_at_boundary(self):
        leg_a = _make_leg([10, 20, 30], [_make_step('Road', 3)])
        leg_b = _make_leg([30, 40, 50], [_make_step('Road', 3)])

        edges_a = _extract_steps_with_edges(leg_a)[0]['edge_ids']
        edges_b = _extract_steps_with_edges(leg_b)[0]['edge_ids']

        overlap = set(edges_a) & set(edges_b)
        assert len(overlap) == 0, 'Adjacent segments sharing only a node should not overlap'
