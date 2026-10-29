"""Skills taxonomy: the shared vocabulary between resumes, jobs and the model.

Resumes say "MS Excel", "MySQL" or "Kobo Toolbox"; the model needs `excel`, `sql`,
`survey_tools`. This module holds that mapping. It imports nothing from the rest of
`core`, so every other module can depend on it safely.
"""

SKILLS = [
    # digital & data
    "excel", "sql", "python", "data_analysis", "power_bi", "statistics", "data_entry", "data_visualization",
    "machine_learning", "monitoring_evaluation", "survey_tools",
    "web_development", "javascript", "graphic_design", "digital_marketing", "social_media",
    "content_writing", "it_support", "networking",
    # business & finance
    "bookkeeping", "accounting_software", "mobile_money_ops", "sales", "customer_service",
    "inventory_management", "procurement", "business_planning", "financial_literacy",
    # agriculture
    "agronomy", "poultry_management", "irrigation", "post_harvest_handling", "agribusiness",
    "extension_services", "aquaculture",
    # technical & green trades
    "electrical_installation", "solar_pv", "plumbing", "welding", "carpentry", "motor_mechanics",
    # logistics, health, creative
    "logistics", "driving", "warehouse_ops", "community_health", "first_aid",
    "fashion_design", "photography", "video_editing",
    # foundational
    "communication", "teamwork", "problem_solving", "english_writing", "project_management",
]
IDX = {s: i for i, s in enumerate(SKILLS)}

# phrase as it appears in documents -> canonical skill
SYNONYMS = {
    "ms excel": "excel", "microsoft excel": "excel", "spreadsheet": "excel", "spreadsheets": "excel",
    "pivot tables": "excel", "vlookup": "excel", "google sheets": "excel",
    "mysql": "sql", "postgresql": "sql", "postgres": "sql", "t-sql": "sql", "sql server": "sql", "bigquery": "sql",
    "python3": "python", "pandas": "python", "numpy": "python", "jupyter": "python",
    "data analytics": "data_analysis", "data analyst": "data_analysis", "analysing data": "data_analysis",
    "analyzing data": "data_analysis", "analyse data": "data_analysis", "analyze data": "data_analysis",
    "powerbi": "power_bi", "power bi": "power_bi", "dax": "power_bi",
    "data visualisation": "data_visualization", "dashboards": "data_visualization", "dashboard": "data_visualization",
    "tableau": "data_visualization", "looker studio": "data_visualization",
    "spss": "statistics", "stata": "statistics", "regression": "statistics", "statistical analysis": "statistics",
    "scikit-learn": "machine_learning", "sklearn": "machine_learning", "predictive modelling": "machine_learning",
    "predictive modeling": "machine_learning",
    "m&e": "monitoring_evaluation", "monitoring and evaluation": "monitoring_evaluation",
    "monitoring & evaluation": "monitoring_evaluation", "meal": "monitoring_evaluation",
    "kobo toolbox": "survey_tools", "kobotoolbox": "survey_tools", "kobocollect": "survey_tools", "odk": "survey_tools",
    "surveycto": "survey_tools", "survey design": "survey_tools",
    "html": "web_development", "css": "web_development", "frontend": "web_development", "react": "javascript",
    "canva": "graphic_design", "photoshop": "graphic_design", "figma": "graphic_design",
    "seo": "digital_marketing", "facebook ads": "digital_marketing", "google ads": "digital_marketing",
    "copywriting": "content_writing", "computer repair": "it_support", "help desk": "it_support",
    "quickbooks": "accounting_software", "sage": "accounting_software", "pos operations": "mobile_money_ops",
    "pos agent": "mobile_money_ops", "crm": "customer_service", "fish farming": "aquaculture",
    "poultry": "poultry_management", "solar installation": "solar_pv", "solar": "solar_pv",
    "electrician": "electrical_installation", "electrical wiring": "electrical_installation",
    "mechanic": "motor_mechanics", "tailoring": "fashion_design", "chw": "community_health",
    "written english": "english_writing", "report writing": "english_writing", "proposal writing": "english_writing",
    "stakeholder engagement": "communication", "presentation skills": "communication", "presentations": "communication",
    "communication skills": "communication", "team player": "teamwork", "collaboration": "teamwork",
    "critical thinking": "problem_solving", "project coordination": "project_management", "dispatch": "logistics",
}
# canonical names also count as phrases ("data_analysis" -> "data analysis")
PHRASES = {s.replace("_", " "): s for s in SKILLS}
PHRASES.update(SYNONYMS)
PHRASES = dict(sorted(PHRASES.items(), key=lambda kv: -len(kv[0])))   # longest first

COURSES = {
    "excel": "Excel for Work (2 wks)", "sql": "SQL Foundations (3 wks)", "python": "Python for Data (6 wks)",
    "data_analysis": "Data Analysis Bootcamp (4 wks)", "power_bi": "Power BI Dashboards (2 wks)",
    "statistics": "Practical Statistics (4 wks)", "data_visualization": "Data Storytelling & Visualisation (2 wks)",
    "machine_learning": "Intro to Machine Learning (6 wks)", "monitoring_evaluation": "M&E Fundamentals (3 wks)",
    "survey_tools": "Digital Data Collection with Kobo/ODK (1 wk)", "digital_marketing": "Digital Marketing Essentials (3 wks)",
    "solar_pv": "Solar PV Installer Certificate (8 wks)", "bookkeeping": "Bookkeeping for SMEs (3 wks)",
    "accounting_software": "QuickBooks / Sage Basics (2 wks)", "agribusiness": "Agribusiness Management (4 wks)",
    "customer_service": "Customer Service Excellence (1 wk)", "project_management": "Project Management Basics (3 wks)",
    "communication": "Workplace Communication (1 wk)", "english_writing": "Business & Report Writing (2 wks)",
}
def course_for(skill):
    return COURSES.get(skill, f"{skill.replace('_', ' ').title()} short course")

_NAMES = {"sql": "SQL", "power_bi": "Power BI", "solar_pv": "Solar PV", "it_support": "IT support",
          "monitoring_evaluation": "M&E", "data_visualization": "Data visualisation", "english_writing": "English / report writing"}
def pretty(skill):
    return _NAMES.get(skill, skill.replace("_", " ").capitalize())
