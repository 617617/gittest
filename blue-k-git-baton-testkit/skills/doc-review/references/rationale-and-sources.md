# Doc Review Rationale And Sources

Load this file only when the user asks why the review policy exists, or when
editing the `doc-review` skill itself.

## Rationale

This skill is designed to stop pre-execution review from becoming a substitute
for execution. Long plan review loops tend to produce diminishing returns:
early rounds find structural problems, later rounds mostly find polish,
preferences, and speculative questions.

The runtime skill therefore keeps three constraints:

- Binary readiness: a small set of checks determines whether execution can start.
- Narrow severity: only `BLOCKING`, `IMPROVEMENT`, and `FOLLOW-UP` exist.
- Bounded rounds: R1 structural, R2 evidence, R3 regression.

## Anti-Patterns

BDUF / Big Design Up Front:

- Symptom: the plan tries to resolve every row, file, edge case, or contract
  before any commit exists.
- Countermeasure: approve the smallest walking skeleton and defer the rest.

Design by Committee:

- Symptom: many reviewers add must-fix items but no owner decides what blocks.
- Countermeasure: assign one owner for BLOCKING vs non-blocking decisions.

Iteration Fatigue:

- Symptom: repeated review rounds keep producing new categories of findings.
- Countermeasure: split, terminate, and force execution of the smallest packet.

## External Sources

- Google Engineering Practices, small CLs:
  https://google.github.io/eng-practices/review/developer/small-cls.html
- Google Engineering Practices, what to look for in review:
  https://google.github.io/eng-practices/review/reviewer/looking-for.html
- Google Engineering Practices, review speed:
  https://google.github.io/eng-practices/review/reviewer/speed.html
- GitLab Code Review Guidelines:
  https://docs.gitlab.com/development/code_review/
- Thoughtworks, Lightweight Architecture Decision Records:
  https://www.thoughtworks.com/en-us/radar/techniques/lightweight-architecture-decision-records
- Shape Up, fixed time and variable scope:
  https://basecamp.com/shapeup
- Walking Skeleton / Tracer Bullet:
  https://www.henricodolfing.com/2018/04/start-your-project-with-walking-skeleton.html
  https://blog.thepete.net/blog/2019/10/04/hello-production/
- Agile Modeling, BMUF anti-pattern:
  https://agilemodeling.com/essays/bmuf.htm
- DevIQ, Big Design Up Front:
  https://deviq.com/antipatterns/big-design-up-front/
