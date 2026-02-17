def get_sample_size(lot_size, inspection_level='II', aql=1.0):
    """
    Simplified AQL (ISO 2859-1) lookup.
    Returns (sample_size, acceptance_number, rejection_number).
    """
    # Sample Size Code Letters (General Inspection Levels)
    # Lot Size | I | II | III
    code_letters = [
        (2, 8, 'A', 'A', 'B'),
        (9, 15, 'A', 'B', 'C'),
        (16, 25, 'B', 'C', 'D'),
        (26, 50, 'C', 'D', 'E'),
        (51, 90, 'C', 'E', 'F'),
        (91, 150, 'D', 'F', 'G'),
        (151, 280, 'E', 'G', 'H'),
        (281, 500, 'F', 'H', 'J'),
        (501, 1200, 'G', 'J', 'K'),
        (1201, 3200, 'H', 'K', 'L'),
        (3201, 10000, 'J', 'L', 'M'),
        (10001, 35000, 'K', 'M', 'N'),
    ]
    
    letter = 'A'
    for low, high, l1, l2, l3 in code_letters:
        if low <= lot_size <= high:
            if inspection_level == 'I': letter = l1
            elif inspection_level == 'II': letter = l2
            elif inspection_level == 'III': letter = l3
            break
        elif lot_size > 35000:
            if inspection_level == 'I': letter = 'L'
            elif inspection_level == 'II': letter = 'N'
            elif inspection_level == 'III': letter = 'P'

    # Master Table (Normal Inspection)
    # Letter | Sample Size | Ac/Re (at AQL 1.0, 2.5, 4.0 example)
    master = {
        'A': {'size': 2,    'ac_re': {1.0: (0,1), 2.5: (0,1), 4.0: (0,1)}},
        'B': {'size': 3,    'ac_re': {1.0: (0,1), 2.5: (0,1), 4.0: (0,1)}},
        'C': {'size': 5,    'ac_re': {1.0: (0,1), 2.5: (0,1), 4.0: (1,2)}},
        'D': {'size': 8,    'ac_re': {1.0: (0,1), 2.5: (1,2), 4.0: (1,2)}},
        'E': {'size': 13,   'ac_re': {1.0: (0,1), 2.5: (1,2), 4.0: (2,3)}},
        'F': {'size': 20,   'ac_re': {1.0: (1,2), 2.5: (2,3), 4.0: (3,4)}},
        'G': {'size': 32,   'ac_re': {1.0: (1,2), 2.5: (3,4), 4.0: (5,6)}},
        'H': {'size': 50,   'ac_re': {1.0: (2,3), 2.5: (5,6), 4.0: (7,8)}},
        'J': {'size': 80,   'ac_re': {1.0: (3,4), 2.5: (7,8), 4.0: (10,11)}},
        'K': {'size': 125,  'ac_re': {1.0: (5,6), 2.5: (10,11), 4.0: (14,15)}},
        'L': {'size': 200,  'size': 200, 'ac_re': {1.0: (7,8), 2.5: (14,15), 4.0: (21,22)}},
        'M': {'size': 315,  'ac_re': {1.0: (10,11), 2.5: (21,22), 4.0: (21,22)}},
        'N': {'size': 500,  'ac_re': {1.0: (14,15), 2.5: (21,22), 4.0: (21,22)}},
        'P': {'size': 800,  'ac_re': {1.0: (21,22), 2.5: (21,22), 4.0: (21,22)}},
    }

    plan = master.get(letter, master['A'])
    size = plan['size']
    ac, re = plan['ac_re'].get(aql, plan['ac_re'].get(4.0)) # Default to 4.0 if AQL mismatch
    
    return size, ac, re
