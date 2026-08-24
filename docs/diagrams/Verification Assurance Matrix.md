| **Dimension                    | Level 1     | Level 2           | Level 3**           |

| ---------------------------- | ----------- | ----------------- | ----------------- |

| Reviewer independence        | Required    | Required          | Required          |

| Repository spot-check        | Yes         | Yes               | Yes               |

| Test rerun                   | No          | Yes               | Yes               |

| Isolated environment         | No          | No                | Yes               |

| Captured verifier-run output | Optional    | Required          | Required          |

| Typical risk                 | Low         | Moderate          | High              |

| Example                      | Docs/config | Behavioral change | Identity/security |



**Threat Model: False Verification / False PASS**



What could cause an implementation to appear correct when it is not?

Examples:



* contaminated test environments,
* stale artifacts,
* incorrect configuration,
* incomplete test selection,
* implementation-generated evidence,
* reviewer authority overlap,
* tests that verify presence but not prohibited behavior



Then map each threat to the verification level designed to mitigate it.

