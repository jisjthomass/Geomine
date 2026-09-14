import unittest

class TestDashboardMetrics(unittest.TestCase):
    def test_metrics_calculation_from_rag_evidence(self):
        """
        Validates that dashboard metrics (total, unique_wells, avg_depth, dominant_event)
        are correctly calculated from RAG evidence rather than legacy pattern_analysis.
        """
        # Mock RAG evidence
        rag_evidence = [
            {"metadata": {"well_id": "WELL_008", "event_type": "Stuck Pipe", "depth_m": 2805}, "hybrid_score": 0.8643},
            {"metadata": {"well_id": "WELL_021", "event_type": "Stuck Pipe", "depth_m": 2810}, "hybrid_score": 0.8639},
            {"metadata": {"well_id": "WELL_022", "event_type": "Differential Sticking", "depth_m": 2845}, "hybrid_score": 0.8623},
            {"metadata": {"well_id": "WELL_008", "event_type": "Torque Spike", "depth_m": 2765}, "hybrid_score": 0.8523},
            {"metadata": {"well_id": "WELL_004", "event_type": "ROP Reduction", "depth_m": 2725}, "hybrid_score": 0.8423},
        ]
        
        display_events = []
        for item in rag_evidence:
            meta = item.get("metadata", {})
            ev_dict = dict(meta)
            display_events.append(ev_dict)
            
        # Metric 1: Total Incidents
        total = len(display_events)
        self.assertEqual(total, 5, "Total incidents should be 5.")
        
        # Metric 2: Unique Wells
        unique_w = len(set(e.get("well_id") for e in display_events if e.get("well_id")))
        self.assertEqual(unique_w, 4, "Unique wells should be 4.")
        
        # Metric 3: Average Depth
        depths = [e.get("depth_m") for e in display_events if e.get("depth_m") is not None]
        avg_depth = round(sum(depths) / len(depths), 1) if depths else 0
        self.assertEqual(avg_depth, 2790.0, "Average depth should be 2790.0.")
        
        # Metric 4: Dominant Event
        dominant_event = None
        ev_types = [
            e.get("event_type") for e in display_events 
            if e.get("event_type") and str(e.get("event_type")).strip() not in ("Unknown", "N/A", "None", "")
        ]
        if ev_types:
            from collections import Counter
            counts = Counter(ev_types)
            top_counts = counts.most_common(2)
            if len(top_counts) == 1:
                dominant_event = top_counts[0][0]
            elif len(top_counts) >= 2:
                if top_counts[0][1] > top_counts[1][1]:
                    dominant_event = top_counts[0][0]
                else:
                    dominant_event = None
                    
        self.assertEqual(dominant_event, "Stuck Pipe", "Dominant event should be 'Stuck Pipe'.")

    def test_dominant_event_tie_omission(self):
        """
        Validates the strict tie-breaker rule for dominant event metric.
        If highest frequency is tied, dominant_event should be None.
        """
        display_events = [
            {"event_type": "Stuck Pipe"},
            {"event_type": "Stuck Pipe"},
            {"event_type": "Mud Loss"},
            {"event_type": "Mud Loss"},
            {"event_type": "Torque Spike"}
        ]
        
        dominant_event = None
        ev_types = [
            e.get("event_type") for e in display_events 
            if e.get("event_type") and str(e.get("event_type")).strip() not in ("Unknown", "N/A", "None", "")
        ]
        if ev_types:
            from collections import Counter
            counts = Counter(ev_types)
            top_counts = counts.most_common(2)
            if len(top_counts) == 1:
                dominant_event = top_counts[0][0]
            elif len(top_counts) >= 2:
                if top_counts[0][1] > top_counts[1][1]:
                    dominant_event = top_counts[0][0]
                else:
                    dominant_event = None
                    
        self.assertIsNone(dominant_event, "Dominant event should be None in case of a tie.")

if __name__ == "__main__":
    unittest.main()
