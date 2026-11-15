"""Registry of the seven independently contributed task pipelines."""
from importlib import import_module

PIPELINES = {
    "spc": ("akhil", "heads_first_signal"),
    "fiber": ("akhil", "fiber_trace"),
    "brain": ("akhil", "brain_spike_location"),
    "cross_sections": ("akhil", "xsec_max_cut_interval_hard"),
    "finance": ("finance_reconciliation", None),
    "measurebench": ("measurebench_ext", None),
    "reconstruction": ("visual_reconstruction", "global_spatial_reconstruction"),
}

REFERENCES = {
    "spc": ["NIST/SEMATECH e-Handbook, section 6.3, Shewhart control charts: https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3.htm", "Western Electric Statistical Quality Control Handbook (1956), rules 1–4"],
    "fiber": ["ANSI/TIA-568.3-D, MTP/MPO polarity methods A, B and C", "Corning and CommScope MTP trunk polarity and structured-cabling guides"],
    "brain": ["AASM Manual for the Scoring of Sleep and Associated Events", "ACNS guidelines for longitudinal bipolar EEG montage and phase-reversal localization"],
    "cross_sections": ["FHWA Western Federal Lands cross-section sample sheets: https://highways.dot.gov/federal-lands/design/plan-prep/wfl/samples/cross-section.pdf", "Caltrans Plans Preparation Manual, roadway cross-section conventions"],
    "finance": ["Purchase orders, goods-receipt notes and supplier invoices: member_notes/finance_reconciliation/REFERENCES.md"],
    "measurebench": ["WIKA pressure-gauge catalogs; Mitutoyo vernier-caliper catalogs; ISO 4788 graduated-cylinder conventions", "member_notes/measurebench_ext/REFERENCES.md"],
    "reconstruction": ["Warren LeMay, Urban Lab Building photograph, Wikimedia Commons, CC BY-SA 4.0; see member_notes/visual_reconstruction/REFERENCES.md"],
}


def adapter_for(pipeline):
    member, default = PIPELINES[pipeline]
    return import_module(f"generators.{member}.adapter"), member, default
