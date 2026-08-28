# FIG-P670-01 overlap adjudication after image opening

HANDOFF_ID=C-FIG-P670-01-R114-SA3-FRESH-ISOLATED-V1

UID=FIG-P670-01

VISIBLE_OBJECT_DENOMINATOR=63

ALL_UNORDERED_PAIRS=1953

BBOX_PAIR_CANDIDATE_COUNT=45

BBOX_PAIR_CANDIDATES_REVIEWED_AFTER_OPEN=45

NON_CANDIDATE_DISJOINT_PAIRS=1908

LEGAL_NODE_CONNECTOR_PAIRS=1

LEGAL_SHARED_BAR_BOUNDARY_PAIRS=4

BACKGROUND_CONTAINMENT_PAIRS=6

SEPARATE_PEER_NODE_PAIRS=13

EXPECTED_NODE_LABEL_PAIRS=20

EXPECTED_BOX_TEXT_PAIRS=1

NATIVE_VISIBLE_INK_CANDIDATE_PIXEL_COUNT=0

MASK_CONTAMINATION_PIXEL_COUNT=0

OVERLAP_PIXEL_COUNT=0

UNRESOLVED_PAIR_COUNT=0

PIXEL_ADJUDICATION_STATUS=CLEAR

MIN_TEXT_CLEARANCE_PX=1

R168_NUMERIC_CLEARANCE_THRESHOLD_STATUS=ADVISORY_ONLY

The 1 px minimum occurs between probability-number ink and the colored probability-bar frame in the native 300dpi raster. Nearest-neighbor 8x inspection shows the two foregrounds remain disjoint and the fraction stays readable. Every bbox containment involving a node or filled bar is an authored background containment; it is not shared visible foreground ink. Detailed per-pair observations are in `manual_pair_candidate_review.csv`.
