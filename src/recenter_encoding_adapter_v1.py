"""Complete the ALREADY registered ten-arm aligned encoding contract.

Three H-independent arms delegate unchanged to the original pure encoder;
seven H-dependent arms delegate unchanged to the document-aligned encoder.
No fitted values, dates, feature definitions or model settings are changed.
"""
from calendar_encoding_study import encoded_input as unchanged_input, feature_names
from calendar_semantics_study_v2 import encoded_input as aligned_input

INDEPENDENT = {'history', 'zero1', 'te_weekday'}


def encoded_input(observed, state, arm, origin):
    if arm in INDEPENDENT:
        return unchanged_input(observed, state, arm, origin)
    return aligned_input(observed, state, arm, origin)
