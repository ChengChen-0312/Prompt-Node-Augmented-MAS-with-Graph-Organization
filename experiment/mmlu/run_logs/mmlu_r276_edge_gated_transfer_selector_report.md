# R276 Edge-Gated Transfer Selector Replay

**Claim boundary**: Offline selector replay over existing full24 API views; supports redesign only until prospectively validated.

- Correct: `13` / `24`
- Fix/Harm: `1/0`
- ARG/plain/node/proposed: `12` / `15` / `13` / `13`
- Beats ARG/plain/node/proposed: `True` / `False` / `False` / `False`
- Decision rules: `{'keep_arg_no_safe_switch': 18, 'keep_arg_unresolved_view_conflict': 5, 'switch_unanimous_api_views': 1}`
- Lifecycle actions: `{'compress': 23, 'forward': 1, 'merge': 1, 'prune': 5, 'upgrade': 1}`

Interpretation: the selector treats PromptEdge text as a gated edge, not an always-on instruction. This is a redesign signal and must be validated prospectively before a paper claim.
