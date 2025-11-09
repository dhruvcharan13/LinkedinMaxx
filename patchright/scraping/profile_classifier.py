"""
Profile Classifier for LinkedIn Profiles

Classifies profiles into categories:
- waterloo: Students/alumni from University of Waterloo
- recruiter: Recruiters, talent acquisition, founders, hiring managers
"""

from typing import Dict, Optional


class ProfileClassifier:
    """Classifies LinkedIn profiles based on content."""
    
    # Keywords for recruiter detection
    RECRUITER_KEYWORDS = [
        # Talent acquisition
        "recruiter", "recruiting", "talent acquisition", "talent partner",
        "talent specialist", "hiring manager", "hiring lead",
        "people operations", "people ops", "head of talent",
        
        # Founders/Leadership
        "founder", "co-founder", "cofounder", "co founder",
        "startup founder", "ceo", "chief executive",
        "founder & ceo", "founder and ceo",
        
        # HR roles
        "human resources", "hr manager", "hr director",
        "talent management", "recruitment manager",
        "technical recruiter", "tech recruiter",
        
        # Hiring-related
        "hiring", "talent scout", "headhunter",
        "staffing", "employment specialist"
    ]
    
    # Keywords for Waterloo detection
    WATERLOO_KEYWORDS = [
        "waterloo", "uwaterloo", "university of waterloo",
        "uw", "waterloo university"
    ]
    
    @staticmethod
    def is_waterloo_student(profile_data: Dict) -> bool:
        """
        Check if profile is a Waterloo student based on education.
        
        Args:
            profile_data: Profile dictionary with education field
            
        Returns:
            True if Waterloo student, False otherwise
        """
        education = profile_data.get('education', [])
        
        if not education:
            return False
        
        # Check each education entry
        for edu in education:
            edu_text = str(edu).lower()
            
            # Check for Waterloo keywords
            for keyword in ProfileClassifier.WATERLOO_KEYWORDS:
                if keyword in edu_text:
                    return True
        
        return False
    
    @staticmethod
    def is_recruiter(profile_data: Dict) -> bool:
        """
        Check if profile is a recruiter/founder based on bio, headline, and experience.
        
        Args:
            profile_data: Profile dictionary with bio, headline, experience fields
            
        Returns:
            True if recruiter/founder, False otherwise
        """
        # Gather all text to search
        search_texts = []
        
        # Add bio
        bio = profile_data.get('bio', '')
        if bio:
            search_texts.append(bio.lower())
        
        # Add headline
        headline = profile_data.get('headline', '')
        if headline:
            search_texts.append(headline.lower())
        
        # Add experience titles and companies
        experience = profile_data.get('experience', [])
        for exp in experience:
            if isinstance(exp, dict):
                title = exp.get('title', '')
                company = exp.get('company', '')
                if title:
                    search_texts.append(title.lower())
                if company:
                    search_texts.append(company.lower())
        
        # Combine all text
        full_text = ' '.join(search_texts)
        
        # Check for recruiter keywords
        for keyword in ProfileClassifier.RECRUITER_KEYWORDS:
            if keyword in full_text:
                return True
        
        return False
    
    @staticmethod
    def classify_profile(profile_data: Dict) -> Optional[str]:
        """
        Classify a profile as 'waterloo', 'recruiter', or None.
        
        Priority: waterloo > recruiter (Waterloo students who are also recruiters count as waterloo)
        
        Args:
            profile_data: Profile dictionary
            
        Returns:
            'waterloo', 'recruiter', or None
        """
        # Check Waterloo first (higher priority)
        if ProfileClassifier.is_waterloo_student(profile_data):
            return "waterloo"
        
        # Check recruiter
        if ProfileClassifier.is_recruiter(profile_data):
            return "recruiter"
        
        return None
    
    @staticmethod
    def add_type_to_profile(profile_data: Dict) -> Dict:
        """
        Add 'Type' field to profile based on classification.
        
        Args:
            profile_data: Profile dictionary
            
        Returns:
            Profile dictionary with 'Type' field added
        """
        profile_type = ProfileClassifier.classify_profile(profile_data)
        
        if profile_type:
            profile_data['Type'] = profile_type
        else:
            profile_data['Type'] = 'other'
        
        return profile_data


# Helper functions for easy use
def classify_profile(profile_data: Dict) -> Optional[str]:
    """Classify a profile. Returns 'waterloo', 'recruiter', or None."""
    return ProfileClassifier.classify_profile(profile_data)


def is_waterloo(profile_data: Dict) -> bool:
    """Check if profile is a Waterloo student."""
    return ProfileClassifier.is_waterloo_student(profile_data)


def is_recruiter(profile_data: Dict) -> bool:
    """Check if profile is a recruiter/founder."""
    return ProfileClassifier.is_recruiter(profile_data)

