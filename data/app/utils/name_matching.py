from fuzzywuzzy import fuzz
from typing import List
from app.models import TeamMember

def find_matching_team_members(host_name: str, min_score: int = 65) -> List[tuple]:
    """
    Find team members whose names fuzzy match the given host name.
    Returns a list of (TeamMember, score) tuples sorted by match score.
    """
    team_members = TeamMember.query.all()
    matches = []
    
    # Normalize the host name
    host_name = host_name.lower().strip()
    
    for member in team_members:
        # Get various forms of the name for matching
        full_name = member.name.lower()
        first_name = full_name.split()[0]
        last_name = full_name.split()[-1] if len(full_name.split()) > 1 else ""
        
        # Calculate different match scores
        scores = [
            fuzz.ratio(host_name, full_name),  # Full name match
            fuzz.ratio(host_name, first_name),  # First name match
            fuzz.partial_ratio(host_name, full_name),  # Partial match
            fuzz.token_sort_ratio(host_name, full_name),  # Word order independent match
        ]
        
        # Special case for initials (e.g., "Matt O" matching "Matt Ortiz")
        if ' ' in host_name and host_name.split()[-1].upper() == last_name[0].upper():
            scores.append(95)  # High score for initial match
        
        # Use the highest score
        best_score = max(scores)
        
        if best_score >= min_score:
            matches.append((member, best_score))
    
    # Sort by score descending
    return sorted(matches, key=lambda x: x[1], reverse=True) 