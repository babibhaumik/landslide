"""
Static terrain / geological landslide-susceptibility weights.

Rainfall alone does not cause landslides - slope, soil type, geology and
existing terrain instability matter just as much. These weights are based
on well-established, publicly documented facts about which Indian regions
sit on steep, geologically unstable terrain (the Himalayan arc, the
Western Ghats escarpment, and parts of the North-East hill states), as
reported by the Geological Survey of India's landslide susceptibility
zonation work. They are NOT derived from a dataset and should be treated
as a reasonable starting weighting, not a precise scientific score.

Scale: 0.0 (flat / stable terrain, negligible landslide history)
       to  1.0 (steep, geologically unstable terrain, frequent landslide history)

Feel free to refine these numbers if you have access to a proper GSI
Landslide Susceptibility Zonation dataset - the model is built so you can
swap this dictionary out without touching anything else.
"""

TERRAIN_SUSCEPTIBILITY = {
    # Himalayan states - steep slopes, active seismicity, frequent landslides
    "Uttarakhand": 0.95,
    "Himachal Pradesh": 0.95,
    "Jammu and Kashmir": 0.90,
    "Ladakh": 0.60,
    "Sikkim": 0.90,

    # North-East hill states - steep terrain, high rainfall, soft geology
    "Arunachal Pradesh": 0.90,
    "Meghalaya": 0.85,
    "Mizoram": 0.85,
    "Manipur": 0.80,
    "Nagaland": 0.80,
    "Tripura": 0.55,
    "Assam": 0.45,  # mostly flood plain, but hill districts are vulnerable

    # Western Ghats - steep escarpment, very high monsoon rainfall
    "Kerala": 0.90,
    "Goa": 0.75,
    "Karnataka": 0.55,   # high only in Western Ghats districts
    "Maharashtra": 0.55,  # high only in Western Ghats / Konkan districts
    "Tamil Nadu": 0.45,   # high only in Nilgiris / Western Ghats districts

    # Eastern Ghats / other hill pockets - moderate
    "Odisha": 0.35,
    "Andhra Pradesh": 0.35,
    "West Bengal": 0.40,  # Darjeeling hills are high, rest of state is flat

    # Mostly flat / plains / arid - low baseline risk
    "Punjab": 0.10,
    "Haryana": 0.10,
    "Uttar Pradesh": 0.15,
    "Bihar": 0.15,
    "Rajasthan": 0.10,
    "Gujarat": 0.15,
    "Madhya Pradesh": 0.20,
    "Chhattisgarh": 0.25,
    "Jharkhand": 0.25,
    "Telangana": 0.20,
    "Delhi": 0.05,
}

DEFAULT_SUSCEPTIBILITY = 0.25  # used for any state not explicitly listed


def get_terrain_score(state_name: str) -> float:
    """Look up terrain susceptibility for a state name, case-insensitively."""
    if not state_name:
        return DEFAULT_SUSCEPTIBILITY
    for key, value in TERRAIN_SUSCEPTIBILITY.items():
        if key.lower() == state_name.strip().lower():
            return value
    return DEFAULT_SUSCEPTIBILITY
