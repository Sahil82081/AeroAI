from typing import Tuple, Literal

class ConnectionRiskEvaluator:
    """
    Evaluates connection risk level based on available time gap (buffer),
    transfer logistics, and minimum required transit windows.
    """

    @classmethod
    def evaluate(
        cls,
        buffer_minutes: int,
        min_required_buffer: int,
        transfer_type: str
    ) -> Tuple[Literal["SAFE", "TIGHT", "IMPOSSIBLE"], str]:
        """
        Calculates risk level:
        - IMPOSSIBLE: buffer_minutes < min_required_buffer * 0.5 or buffer_minutes < 0 or inter-city mismatch
        - TIGHT: min_required_buffer * 0.5 <= buffer_minutes < min_required_buffer * 1.25
        - SAFE: buffer_minutes >= min_required_buffer * 1.25
        """
        if buffer_minutes < 0:
            return (
                "IMPOSSIBLE",
                f"Negative connection time ({buffer_minutes}m). Next departure occurs before arrival."
            )

        if transfer_type == "inter_city_transfer" and buffer_minutes < 180:
            return (
                "IMPOSSIBLE",
                f"Location mismatch across distinct cities with insufficient transit window ({buffer_minutes}m)."
            )

        if buffer_minutes < (min_required_buffer * 0.6):
            return (
                "IMPOSSIBLE",
                f"Severe time constraint ({buffer_minutes}m available vs {min_required_buffer}m minimum required for {transfer_type.replace('_', ' ')})."
            )

        if buffer_minutes < (min_required_buffer * 1.2):
            return (
                "TIGHT",
                f"Tight connection window ({buffer_minutes}m). High vulnerability to modest delays ({min_required_buffer}m recommended)."
            )

        return (
            "SAFE",
            f"Healthy connection buffer ({buffer_minutes}m available, comfortably exceeds {min_required_buffer}m required)."
        )
