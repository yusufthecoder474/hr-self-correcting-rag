def rewrite_query(question):

    query = question.lower().strip()

    rewrite_rules = {

        "leave after joining":
            "What is the leave eligibility and approval process for employees during probation?",

        "leave eligibility for newly joined employees":
            "What is the leave policy for employees during probation, including approval requirements?",

        "what leave can a probation employee request":
            "What leave can employees on probation request and what approval is required?",

        "rules for taking leave during probation":
            "What are the leave rules and manager approval requirements during probation?",

        "leave policy for a newly joined employee":
            "What is the leave policy for newly joined employees during probation?",

        "annual leave and personal leave":
            "What are the annual leave and personal leave entitlements and rules?",

        "difference between annual leave and personal leave":
            "What are the entitlements and carry-forward rules for annual leave and personal leave?",

        "work from home during probation":
            "What are the remote and hybrid work eligibility rules during probation?",

        "difference between remote work and leave":
            "What is the difference between approved remote work and employee leave?",

        "home internet":
            "What is the monthly home internet reimbursement for approved long-term remote work?",

        "learning reimbursement after probation":
            "What is the learning budget and eligibility after completing probation?",

        "probation is extended":
            "What are the rules for probation extension and its maximum duration?",

        "employee confirmation after probation":
            "What are the requirements for employee confirmation after probation?",

        "emergency absence":
            "What should an employee do when advance notice is not reasonably possible for an absence?",

        "sick leave be carried forward":
            "Can sick leave be carried forward to the next calendar year?",

        "hybrid work eligibility":
            "What are the eligibility requirements for remote and hybrid work?",

        "notice period":
            "What is the standard notice period for permanent employees?"
    }

    for phrase, rewritten_query in rewrite_rules.items():

        if phrase in query:
            return rewritten_query

    return question