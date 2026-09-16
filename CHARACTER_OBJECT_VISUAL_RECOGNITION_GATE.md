# Character & Object Visual Recognition Gate

## Implemented
- Persistent project-bound visual targets for characters, objects, and set elements.
- Stable Character ID / Object ID association.
- Normalized target regions survive resolution changes.
- Independent target-region comparison prevents an unchanged actor region from being hidden by drift elsewhere in frame.
- Target evidence is integrated into Visual Continuity Certification and candidate drift reporting.

## Truth matrix
- Target registration/persistence: REAL / TESTED.
- Character-ID association: REAL / TESTED.
- Object/set-element association: REAL / TESTED.
- Region-specific visual consistency: REAL / TESTED at image-analysis boundary.
- Biometric/person identification: NOT IMPLEMENTED and NOT CLAIMED.
- Automatic semantic object detection/tracking: NOT IMPLEMENTED.
- Face/wardrobe/hair semantic sameness: PARTIAL / REVIEW_REQUIRED unless specialized evidence is later added.
- Actual Windows/AMD generated-footage certification: NOT TESTED.

Film Lab treats labels such as Sarah as project-bound identities supplied by the Creator. A PASS means the registered visual region remained sufficiently consistent under the measured image evidence; it does not independently identify a real person.
