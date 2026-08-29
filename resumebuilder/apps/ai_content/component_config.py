"""AI-assistable Resume Builder component fields."""

# model name -> field -> friendly label
AI_COMPONENT_FIELDS = {
    'resume': {
        'name': 'Name', 'title': 'Title', 'position': 'Position', 'tag_line': 'Tag Line',
        'short_desc': 'Short Description', 'summary': 'Summary', 'skills': 'Skills',
        'experience': 'Experience', 'education': 'Education', 'tags': 'Tags',
    },
    'contactsection': {
        'title': 'Title', 'subtitle': 'Subtitle', 'description': 'Description',
        'location': 'Location', 'phone_numbers': 'Phone Numbers', 'email_addresses': 'Email Addresses',
    },
    'contactmessage': {'subject': 'Subject', 'message': 'Message'},
    'faqsection': {'title': 'Title', 'subtitle': 'Subtitle'},
    'faq': {'question': 'Question', 'answer': 'Answer'},
    'journey': {'title': 'Title', 'short_desc': 'Short Description'},
    'resumejourney': {'description': 'Description'},
    'profession': {'title': 'Title', 'short_desc': 'Short Description'},
    'servicesection': {'title': 'Title', 'subtitle': 'Subtitle'},
    'service': {'title': 'Title', 'description': 'Description'},
    'skillcategory': {'title': 'Title'},
    'skill': {'name': 'Skill Name'},
    'testimonialsection': {'title': 'Title', 'subtitle': 'Subtitle'},
    'testimonial': {'quote': 'Quote', 'author_role': 'Author Role'},
    'excellence': {'title': 'Title', 'company': 'Company', 'date_range': 'Date Range', 'description': 'Description'},
}

MODEL_ALIASES = {
    'resume': 'resume',
    'resumestat': 'resumestat',
    'resumesocial': 'resumesocial',
    'resumefloatingcard': 'resumefloatingcard',
    'resumeskill': 'resumeskill',
    'resumejourney': 'resumejourney',
    'skillcategory': 'skillcategory',
    'skill': 'skill',
    'profession': 'profession',
    'journey': 'journey',
    'excellence': 'excellence',
    'servicesection': 'servicesection',
    'service': 'service',
    'testimonialsection': 'testimonialsection',
    'testimonial': 'testimonial',
    'faqsection': 'faqsection',
    'faq': 'faq',
    'contactsection': 'contactsection',
    'contactmessage': 'contactmessage',
}
