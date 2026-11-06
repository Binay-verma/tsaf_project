"""Registered analysis for results/ziel_replacing_v2.

Reuses the registered v1 analysis code unchanged with the v2 directory and
contrasts. Writes only to results/ziel_replacing_v2/analysis.
"""
import ziel_replacing_analysis_v1 as a
import ziel_replacing_v2 as v2

a.OUT = v2.OUT
a.CONTRASTS = [('replace_typed', 'replace_pooled'), ('replace_pooled', 'pooled_day5'), ('replace_typed', 'day5'),
               ('replace_pooled', 'calendar'), ('replace_typed', 'calendar')]

if __name__ == '__main__':
    a.main()
