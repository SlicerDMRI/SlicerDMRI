"""Cluster-to-tract mapping data extracted from the ORG atlas annotation.

Source: FiberClusterAnnotation_Updated20230110.xlsx from
https://github.com/SlicerDMRI/TractCloud

Each key is a tract name and each value is a list of cluster indices (0-based)
that belong to that tract. Clusters 0-799 are plausible; indices 800-1599 in
the model output are their outlier counterparts and are mapped to 'Other'.
"""

# Ordered tract names matching TractCloud convention
TRACT_NAMES = [
    "AF", "CB", "EC", "EmC", "ILF", "IOFF", "MdLF",
    "SLF-I", "SLF-II", "SLF-III", "UF",
    "CST", "CR-F", "CR-P", "SF", "SO", "SP",
    "TF", "TO", "TT", "TP", "PLIC",
    "CC1", "CC2", "CC3", "CC4", "CC5", "CC6", "CC7",
    "CPC", "ICP", "Intra-CBLM-I-P", "Intra-CBLM-PaT", "MCP",
    "Sup-F", "Sup-FP", "Sup-O", "Sup-OT", "Sup-P", "Sup-PO", "Sup-PT", "Sup-T",
    "Other",
]

# Category grouping for two-level SubjectHierarchy
TRACT_CATEGORIES = {
    "Association": ["AF", "CB", "EC", "EmC", "ILF", "IOFF", "MdLF",
                    "SLF-I", "SLF-II", "SLF-III", "UF"],
    "Projection": ["CST", "CR-F", "CR-P", "SF", "SO", "SP",
                   "TF", "TO", "TT", "TP", "PLIC"],
    "Commissural": ["CC1", "CC2", "CC3", "CC4", "CC5", "CC6", "CC7"],
    "Cerebellar": ["CPC", "ICP", "Intra-CBLM-I-P", "Intra-CBLM-PaT", "MCP"],
    "Superficial": ["Sup-F", "Sup-FP", "Sup-O", "Sup-OT", "Sup-P",
                    "Sup-PO", "Sup-PT", "Sup-T"],
    "Other": ["Other"],
}

# Full anatomical names for each tract abbreviation
TRACT_FULL_NAMES = {
    "AF": "arcuate fasciculus",
    "CB": "cingulum bundle",
    "EC": "external capsule",
    "EmC": "extreme capsule",
    "ILF": "inferior longitudinal fasciculus",
    "IOFF": "inferior occipito-frontal fasciculus",
    "MdLF": "middle longitudinal fasciculus",
    "SLF-I": "superior longitudinal fasciculus I",
    "SLF-II": "superior longitudinal fasciculus II",
    "SLF-III": "superior longitudinal fasciculus III",
    "UF": "uncinate fasciculus",
    "CST": "corticospinal tract",
    "CR-F": "corona radiata frontal",
    "CR-P": "corona radiata parietal",
    "SF": "striato-frontal",
    "SO": "striato-occipital",
    "SP": "striato-parietal",
    "TF": "thalamo-frontal",
    "TO": "thalamo-occipital",
    "TT": "thalamo-temporal",
    "TP": "thalamo-parietal",
    "PLIC": "posterior limb of internal capsule",
    "CC1": "corpus callosum 1",
    "CC2": "corpus callosum 2",
    "CC3": "corpus callosum 3",
    "CC4": "corpus callosum 4",
    "CC5": "corpus callosum 5",
    "CC6": "corpus callosum 6",
    "CC7": "corpus callosum 7",
    "CPC": "cortico-ponto-cerebellar",
    "ICP": "inferior cerebellar peduncle",
    "Intra-CBLM-I-P": "intracerebellar input and Purkinje tract",
    "Intra-CBLM-PaT": "intracerebellar parallel tract",
    "MCP": "middle cerebellar peduncle",
    "Sup-F": "superficial frontal",
    "Sup-FP": "superficial frontal-parietal",
    "Sup-O": "superficial occipital",
    "Sup-OT": "superficial occipital-temporal",
    "Sup-P": "superficial parietal",
    "Sup-PO": "superficial parietal-occipital",
    "Sup-PT": "superficial parietal-temporal",
    "Sup-T": "superficial temporal",
    "Other": "other",
}

# Mapping from tract name to list of cluster indices (0-based).
TRACT_CLUSTER_MAPPING = {
    "AF": [168, 169, 170, 175, 180, 185, 205, 291, 347, 434, 725],
    "CB": [140, 278, 281, 283, 304, 312, 320, 354, 362, 366, 386, 396, 398, 405, 409, 412, 464, 473, 548, 630, 681, 769],
    "EC": [706, 720, 779, 784],
    "EmC": [727, 775, 777],
    "ILF": [111, 127, 135, 137, 138, 150, 157, 164, 166, 542, 684, 685, 700, 718, 722],
    "IOFF": [680, 682, 712, 715, 723, 748, 751, 768],
    "MdLF": [36, 47, 432, 461, 471, 489, 491, 558, 566, 690, 714, 735, 759, 780, 789],
    "SLF-I": [241, 249, 253, 270, 280, 289, 306, 313, 315, 323, 328, 341, 381, 394, 433, 463, 480, 481],
    "SLF-II": [173, 177, 186, 187, 209, 215, 218, 235, 265, 282, 333, 395],
    "SLF-III": [208, 211, 219, 228, 244],
    "UF": [650, 689, 697, 701, 730, 760, 791],
    "CST": [172, 193, 237, 673, 696, 708, 710, 729, 745, 772, 792],
    "CR-F": [171, 674, 704, 719, 747, 753, 758, 763],
    "CR-P": [136, 147],
    "SF": [222, 236, 300, 327, 401, 580, 581, 585, 586, 612, 617, 622, 625, 632, 665],
    "SO": [563],
    "SP": [288, 346],
    "TF": [183, 189, 195, 210, 223, 229, 255, 272, 357, 378, 593, 600, 608, 621, 624, 635, 639, 686, 687, 734, 764],
    "TO": [71, 99, 533],
    "TT": [143, 269, 707, 731, 746, 754, 783, 793, 795],
    "TP": [37, 49, 59, 192, 310, 326, 445, 474, 498, 607],
    "PLIC": [317, 416],
    "CC1": [614, 633, 653],
    "CC2": [251, 363, 371, 403, 576, 577, 582, 587, 591, 597, 620, 623, 627, 645, 663, 670],
    "CC3": [252, 262, 263, 305, 311, 330, 338, 375],
    "CC4": [250, 257, 268, 271, 314, 350],
    "CC5": [322, 410, 440, 465, 484],
    "CC6": [8, 33, 40, 46, 52, 56, 163, 437, 448, 456, 475, 485, 488, 658],
    "CC7": [3, 57, 62, 68, 69, 86, 91],
    "CPC": [145, 159, 557, 677, 770],
    "ICP": [125, 129, 514],
    "Intra-CBLM-I-P": [108, 495, 497, 500, 503, 513, 526, 536, 539, 569, 571, 574],
    "Intra-CBLM-PaT": [494, 499, 501, 502, 504, 507, 509, 511, 512, 515, 518, 520, 527, 528, 535, 537, 538, 540, 547, 550, 551, 561, 562, 564, 570],
    "MCP": [109, 110, 114, 519, 522, 525, 543, 545, 549],
    "Sup-F": [204, 221, 231, 245, 258, 260, 261, 266, 274, 275, 277, 286, 290, 292, 293, 295, 297, 298, 299, 302, 303, 318, 321, 332, 337, 339, 343, 345, 349, 351, 358, 359, 360, 364, 367, 372, 373, 374, 376, 379, 384, 387, 388, 389, 393, 399, 400, 404, 406, 407, 408, 411, 444, 472, 584, 588, 590, 592, 595, 602, 603, 606, 611, 615, 618, 628, 629, 634, 636, 638, 641, 644, 646, 651, 652, 655, 656, 660, 661, 666, 761],
    "Sup-FP": [200, 216, 238, 319, 390, 397, 414, 476, 477, 478],
    "Sup-O": [77, 78, 82, 89, 93, 95, 100],
    "Sup-OT": [85, 94, 96, 105, 552, 553, 568],
    "Sup-P": [14, 16, 17, 22, 24, 29, 34, 38, 41, 45, 54, 58, 60, 273, 307, 336, 361, 368, 391, 413, 418, 419, 420, 421, 426, 429, 430, 435, 438, 443, 446, 447, 449, 455, 457, 459, 462, 466, 482, 483],
    "Sup-PO": [6, 35, 53, 61, 63, 64, 66, 70, 74, 83, 92],
    "Sup-PT": [0, 1, 2, 5, 7, 9, 11, 18, 21, 25, 28, 30, 42, 50, 51, 72, 75, 81, 106, 431, 439, 454, 713, 790],
    "Sup-T": [118, 154, 555, 556, 688, 691, 717, 724, 728, 737, 739, 743, 776, 794],
    "Other": [4, 10, 12, 13, 15, 19, 20, 23, 26, 27, 31, 32, 39, 43, 44, 48, 55, 65, 67, 73, 76, 79, 80, 84, 87, 88, 90, 97, 98, 101, 102, 103, 104, 107, 112, 113, 115, 116, 117, 119, 120, 121, 122, 123, 124, 126, 128, 130, 131, 132, 133, 134, 139, 141, 142, 144, 146, 148, 149, 151, 152, 153, 155, 156, 158, 160, 161, 162, 165, 167, 174, 176, 178, 179, 181, 182, 184, 188, 190, 191, 194, 196, 197, 198, 199, 201, 202, 203, 206, 207, 212, 213, 214, 217, 220, 224, 225, 226, 227, 230, 232, 233, 234, 239, 240, 242, 243, 246, 247, 248, 254, 256, 259, 264, 267, 276, 279, 284, 285, 287, 294, 296, 301, 308, 309, 316, 324, 325, 329, 331, 334, 335, 340, 342, 344, 348, 352, 353, 355, 356, 365, 369, 370, 377, 380, 382, 383, 385, 392, 402, 415, 417, 422, 423, 424, 425, 427, 428, 436, 441, 442, 450, 451, 452, 453, 458, 460, 467, 468, 469, 470, 479, 486, 487, 490, 492, 493, 496, 505, 506, 508, 510, 516, 517, 521, 523, 524, 529, 530, 531, 532, 534, 541, 544, 546, 554, 559, 560, 565, 567, 572, 573, 575, 578, 579, 583, 589, 594, 596, 598, 599, 601, 604, 605, 609, 610, 613, 616, 619, 626, 631, 637, 640, 642, 643, 647, 648, 649, 654, 657, 659, 662, 664, 667, 668, 669, 671, 672, 675, 676, 678, 679, 683, 692, 693, 694, 695, 698, 699, 702, 703, 705, 709, 711, 716, 721, 726, 732, 733, 736, 738, 740, 741, 742, 744, 749, 750, 752, 755, 756, 757, 762, 765, 766, 767, 771, 773, 774, 778, 781, 782, 785, 786, 787, 788, 796, 797, 798, 799],
}


def _buildLookupTable():
    """Build a 1600-element lookup table: cluster index -> tract label index."""
    import numpy as np
    other_idx = len(TRACT_NAMES) - 1
    lut = np.full(1600, other_idx, dtype=np.int32)
    for tract_idx, tract_name in enumerate(TRACT_NAMES):
        if tract_name == "Other":
            continue
        for cluster_idx in TRACT_CLUSTER_MAPPING[tract_name]:
            lut[cluster_idx] = tract_idx
            # Outlier counterpart (cluster_idx + 800) stays as "Other"
    return lut

_CLUSTER_TO_TRACT_LUT = _buildLookupTable()


def cluster2tract_label(predicted_cluster_indices):
    """Convert 1600-class cluster predictions to 43-class tract labels.

    Args:
        predicted_cluster_indices: array-like of predicted cluster indices (0-1599).
            Indices 0-799 are plausible clusters, 800-1599 are outlier counterparts.

    Returns:
        numpy array of tract label indices (0-42), where the index corresponds
        to the position in TRACT_NAMES.
    """
    import numpy as np
    indices = np.asarray(predicted_cluster_indices, dtype=np.int32)
    return _CLUSTER_TO_TRACT_LUT[np.clip(indices, 0, 1599)]
