import networkx as nx
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.models import Journey, Booking, JourneyNode, JourneyEdge
from app.schemas.graph_schemas import (
    JourneyGraphResponse, JourneyNodeDetail, JourneyEdgeDetail, JourneyRiskSummary
)
from app.modules.journeys.location_matcher import LocationMatcher
from app.modules.journeys.risk_evaluator import ConnectionRiskEvaluator
from app.core.logger import logger

class JourneyGraphEngine:
    """
    Transforms individual bookings in a journey into a connected NetworkX DAG.
    Calculates chronological sequence, automatic transfers/dependencies,
    time buffers, location matching, and connection risk classifications.
    """

    def __init__(self, journey_id: int):
        self.journey_id = journey_id
        self.graph = nx.DiGraph()

    def build_from_bookings(self, bookings: List[Booking]) -> JourneyGraphResponse:
        """
        Builds graph from bookings, identifies chronological connections and dependencies.
        """
        self.graph.clear()

        # Sort bookings chronologically by start_time
        sorted_bookings = sorted(bookings, key=lambda b: b.start_time)

        nodes_detail: List[JourneyNodeDetail] = []
        edges_detail: List[JourneyEdgeDetail] = []

        # 1. Add all booking nodes to NetworkX graph
        for b in sorted_bookings:
            node_id = f"booking_{b.id}"
            node_type = b.booking_type.value.lower()
            
            node_data = {
                "id": node_id,
                "key": b.reference_number,
                "name": b.title,
                "type": node_type,
                "booking_id": b.id,
                "provider": b.provider_name,
                "start_time": b.start_time,
                "end_time": b.end_time,
                "origin": b.origin,
                "destination": b.destination,
                "status": b.status.value,
                "properties": b.raw_metadata or {}
            }
            self.graph.add_node(node_id, **node_data)
            nodes_detail.append(JourneyNodeDetail(**node_data))

        # 2. Automatically detect sequential connections and dependencies
        safe_count = 0
        tight_count = 0
        impossible_count = 0
        critical_deps = []

        for i in range(len(sorted_bookings) - 1):
            curr_b = sorted_bookings[i]
            next_b = sorted_bookings[i + 1]

            curr_node_id = f"booking_{curr_b.id}"
            next_node_id = f"booking_{next_b.id}"

            # Calculate available buffer (time gap) in minutes
            # For HOTEL stays where the next activity/leg occurs after check-in, measure from check-in time
            ref_end_time = (
                curr_b.start_time
                if (curr_b.booking_type.value == "HOTEL" and next_b.start_time >= curr_b.start_time)
                else curr_b.end_time
            )
            time_delta = next_b.start_time - ref_end_time
            buffer_minutes = int(time_delta.total_seconds() / 60)

            # Evaluate transfer logistics between arrival location and next departure location
            arr_loc = curr_b.destination or curr_b.origin or ""
            dep_loc = next_b.origin or next_b.destination or ""
            arr_type = curr_b.booking_type.value
            dep_type = next_b.booking_type.value

            transfer_type, min_buffer = LocationMatcher.evaluate_transfer_proximity(
                arr_loc, dep_loc, arr_type, dep_type
            )

            # Evaluate risk level
            risk_level, risk_reason = ConnectionRiskEvaluator.evaluate(
                buffer_minutes, min_buffer, transfer_type
            )

            if risk_level == "SAFE":
                safe_count += 1
            elif risk_level == "TIGHT":
                tight_count += 1
                critical_deps.append(f"{curr_b.reference_number} -> {next_b.reference_number} ({buffer_minutes}m buffer)")
            elif risk_level == "IMPOSSIBLE":
                impossible_count += 1
                critical_deps.append(f"CRITICAL: {curr_b.reference_number} -> {next_b.reference_number} ({buffer_minutes}m buffer)")

            edge_id = f"edge_{curr_b.id}_{next_b.id}"
            edge_type = "dependency" if risk_level in ["TIGHT", "IMPOSSIBLE"] else "connection"

            edge_data = {
                "id": edge_id,
                "source": curr_node_id,
                "target": next_node_id,
                "edge_type": edge_type,
                "from_booking_id": curr_b.id,
                "to_booking_id": next_b.id,
                "buffer_minutes": buffer_minutes,
                "transfer_type": transfer_type,
                "risk_level": risk_level,
                "risk_reason": risk_reason,
                "recommended_min_buffer": min_buffer,
                "properties": {
                    "from_ref": curr_b.reference_number,
                    "to_ref": next_b.reference_number
                }
            }

            self.graph.add_edge(curr_node_id, next_node_id, **edge_data)
            edges_detail.append(JourneyEdgeDetail(**edge_data))

        # 3. Graph topological analysis
        is_dag = nx.is_directed_acyclic_graph(self.graph)
        topological_sequence = list(nx.topological_sort(self.graph)) if is_dag else list(self.graph.nodes())

        highest_risk = "NONE"
        if impossible_count > 0:
            highest_risk = "IMPOSSIBLE"
        elif tight_count > 0:
            highest_risk = "TIGHT"
        elif safe_count > 0:
            highest_risk = "SAFE"

        risk_summary = JourneyRiskSummary(
            total_connections=len(edges_detail),
            safe_connections=safe_count,
            tight_connections=tight_count,
            impossible_connections=impossible_count,
            highest_risk=highest_risk,
            critical_dependencies=critical_deps
        )

        return JourneyGraphResponse(
            journey_id=self.journey_id,
            journey_title="",
            total_nodes=len(nodes_detail),
            total_edges=len(edges_detail),
            nodes=nodes_detail,
            edges=edges_detail,
            risk_summary=risk_summary,
            is_dag=is_dag,
            topological_sequence=topological_sequence
        )

    def sync_to_database(self, db: Session, journey: Journey) -> JourneyGraphResponse:
        """
        Builds the graph from the journey's current bookings and persists
        updated JourneyNode and JourneyEdge records into the database.
        """
        graph_resp = self.build_from_bookings(journey.bookings)
        graph_resp.journey_title = journey.title

        # Clear previous nodes and edges for this journey
        db.query(JourneyEdge).filter(JourneyEdge.journey_id == journey.id).delete()
        db.query(JourneyNode).filter(JourneyNode.journey_id == journey.id).delete()
        db.commit()

        # Insert new JourneyNode rows
        db_nodes_map = {}
        for n in graph_resp.nodes:
            db_node = JourneyNode(
                journey_id=journey.id,
                node_key=n.key,
                name=n.name,
                location_type=n.type.upper(),
                arrival_time=n.end_time,
                departure_time=n.start_time,
                properties=n.properties
            )
            db.add(db_node)
            db.flush()
            db_nodes_map[n.id] = db_node.id

        # Insert new JourneyEdge rows
        for e in graph_resp.edges:
            src_db_id = db_nodes_map.get(e.source)
            tgt_db_id = db_nodes_map.get(e.target)
            if src_db_id and tgt_db_id:
                db_edge = JourneyEdge(
                    journey_id=journey.id,
                    source_node_id=src_db_id,
                    target_node_id=tgt_db_id,
                    booking_id=e.from_booking_id,
                    transport_mode=e.transfer_type.upper(),
                    scheduled_departure=datetime.utcnow(),
                    scheduled_arrival=datetime.utcnow(),
                    duration_minutes=e.recommended_min_buffer,
                    buffer_minutes=e.buffer_minutes,
                    properties={
                        "risk_level": e.risk_level,
                        "risk_reason": e.risk_reason,
                        "transfer_type": e.transfer_type
                    }
                )
                db.add(db_edge)

        db.commit()
        logger.info(f"Synchronized Journey #{journey.id} graph ({len(graph_resp.nodes)} nodes, {len(graph_resp.edges)} edges) to database.")
        return graph_resp
