"""Built-in policies.

  - floor: trivial combat policy (basic_attack, no cheat/survive).
  - default_macro: conservative between-combat policy (highest zone,
    no overstay, heal when wounded, accept recruits).

Phase 2 will add golden/<job>.yaml rule tables that slot in alongside
these as more sophisticated CombatPolicy implementations.
"""
