"""
Message Templates for LinkedIn Messaging

PLACEHOLDER - To be implemented
"""

# Connection request templates
CONNECTION_TEMPLATES = {
    "waterloo_student": "Hi {name}, I noticed you're also from Waterloo! Would love to connect.",
    "recruiter": "Hi {name}, I'm interested in learning more about opportunities at {company}.",
    "general": "Hi {name}, I'd like to add you to my professional network."
}

# Direct message templates
MESSAGE_TEMPLATES = {
    "introduction": "Hi {name}, I came across your profile and would love to chat about {topic}.",
    "follow_up": "Hi {name}, following up on our connection request. Would you be open to a quick chat?",
    "networking": "Hi {name}, I'm looking to expand my network in {industry}. Would love to connect!"
}


def format_template(template_name: str, template_type: str = "connection", **kwargs) -> str:
    """
    Format a message template with provided variables.
    
    Args:
        template_name: Name of the template
        template_type: 'connection' or 'message'
        **kwargs: Variables to fill in template (name, company, topic, etc.)
        
    Returns:
        Formatted message string
    """
    templates = CONNECTION_TEMPLATES if template_type == "connection" else MESSAGE_TEMPLATES
    
    if template_name not in templates:
        raise ValueError(f"Template '{template_name}' not found")
    
    template = templates[template_name]
    return template.format(**kwargs)


# TODO: Add more templates
# TODO: Add personalization logic
# TODO: Add template validation

