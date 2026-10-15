"""Populate AI-authored candidates from source, never from model outputs."""
from pathlib import Path
import csv,json,hashlib,re
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[3]
EVAL=ROOT/'research/review3/independent_eval_30'
PDF=ROOT/'documents/vit/VIT_HR_Conditions_of_Service.pdf'
# category, question, section, PDF page(s), family, reference answer, excerpt anchor
DATA=[
('eligibility','Do the VIT Employee Leave Rules apply to a person appointed as an apprentice?','5.3','1','leave_scope','The stated leave rules exclude apprentices and trainees, along with casual, project and contract staff.','These rules do not apply'),
('eligibility','A faculty member has completed six continuous years at VIT and wants time to prepare a textbook. Is that purpose eligible for sabbatical consideration?','5.5.5','5','sabbatical_eligibility','The manual permits consideration after six years of continuous service for academic pursuits including preparation of textbooks. Sanction remains discretionary.','Preparation of Text books'),
('eligibility','Does a faculty member qualify for compensatory leave after working on a notified holiday?','5.5.8','7','compensatory_eligibility','No. The manual explicitly excludes faculty from compensatory off or leave.','Faculty are not eligible'),
('eligibility','Can a staff member with one year of service but only 70 percent physical attendance in the preceding semester claim summer vacation eligibility?','5.6.2','8','staff_vacation_eligibility','The stated eligibility requires one year of service and 75 percent physical attendance in the preceding semester. Seventy percent does not meet the stated attendance condition.','75% of physical attendance'),
('eligibility','A retired employee was not a casual employee. Can they request a service certificate?','5.8.2','10','service_certificate','Yes. An employee other than a casual employee who leaves, retires or is dismissed is to receive a service certificate without avoidable delay if they apply.','other than a casual Employee'),
('eligibility','When an employee dies during service, who may receive the encashment of accumulated earned leave?','5.7 Rule 3','8','encashment_heir','The nominated legal heir may receive the encashed accumulated earned leave.','nominated legal heir'),
('entitlement_limit','What is the maximum period for which sabbatical leave can be extended under this manual?','5.5.5 item 5','5','sabbatical_limit','The manual states that sabbatical leave cannot be extended beyond one year under any circumstances.','extended beyond one year'),
('entitlement_limit','What is the maximum medical leave balance that can be accumulated?','5.5.3(v)','4','medical_accumulation','Medical leave can accumulate up to 180 days.','maximum of 180 days'),
('entitlement_limit','How much summer vacation is normally available to eligible administrative and technical supporting staff?','5.6.2(i)','8','staff_vacation_duration','Normally ten calendar days during summer, subject to the stated eligibility and notification conditions.','10 Calendar days during Summer'),
('entitlement_limit','What is the annual On Duty limit for faculty academic work that is not directly related to university functioning?','5.5.7','6','on_duty_limit','The stated limit is 15 days in an academic year for academic work related to the university, with prior written permission.','15 days in an academic year'),
('entitlement_limit','How many faculty members from the same School may take sabbatical leave at one time?','5.5.5 item 9','6','sabbatical_concurrency','Only one faculty member from a School may avail sabbatical leave at a time.','Only one Faculty member'),
('entitlement_limit','What are the retirement ages stated for faculty and staff in the supplied manual?','5.8.1(h)','10','retirement_age','The supplied manual states 65 years for faculty and 62 years for staff. This is a statement about the supplied manual, not verification of current institutional policy.','Sixty Five years for Faculty and Sixty Two years for Staff'),
('procedure_approval','Who must notify the festival and national holidays that an employee may avail?','5.2','1','holiday_notification','The Registrar notifies the holidays in advance. Only holidays notified by the Registrar may be availed.','notified in advance by the Registrar'),
('procedure_approval','For a leave period exceeding one month, when must an extension request reach the Registrar and when must the approval order be obtained?','5.4(e)','2','leave_extension','The request must reach the Registrar 15 days before the actual rejoining date and the approval order must be obtained one week before rejoining.','15 days prior to the actual date'),
('procedure_approval','Who must attest a medical certificate obtained from a registered practitioner outside the VIT Health Centre for leave sanction?','5.5.3(iv)','4','medical_attestation','The Medical Officer of VIT Health Centre must attest the outside registered practitioner certificate.','duly attested by the Medical Officer of VIT'),
('procedure_approval','To whom should a report on university-related other-duty activities be submitted with the travel allowance claim?','5.5.7','6','on_duty_reporting','The activities report should be submitted to the Vice-Chancellor or Registrar along with the TA claim.','along with the TA claim'),
('procedure_approval','What two records must accompany the request for financial dues and a relieving order?','5.8.1','9','resignation_clearance','A No Dues Certificate in the prescribed form and a copy of the handing-over charge record endorsed by the relevant Dean, Director or Section Head.','No Dues Certificate'),
('procedure_approval','What advance institutional certificate is required when an employee wishes to apply for higher studies?','5.8.2','10','higher_studies_noc','The employee should obtain a No Objection Certificate from the Registrar in advance.','obtained from the Registrar in advance'),
('multi_condition','A faculty member is prevented from taking eight days of vacation because their services are essential. What additional earned leave ratio applies, and what does that imply for eight days?','5.6.1','7','vacation_compensation','The stated ratio is two vacation days to one additional earned-leave day. Eight prevented vacation days imply four additional earned-leave days under that rule.','2 days of vacation as 1 EL'),
('multi_condition','For a one-year sabbatical, how do the post-leave service bonds differ between full pay and half pay, and what repayment condition applies on non-compliance?','5.5.5 item 11','6','sabbatical_bond','Full pay requires service for twice the sponsorship duration (two years here); half pay requires the sponsorship duration (one year). Non-compliance requires repayment of salary drawn plus 20 percent annual interest.','20% interest per annum'),
('multi_condition','What continuous-service requirement, leave duration and return-service obligation apply to long leave without pay for higher studies?','5.5.6','6','long_leave_bond','Three years of continuous service may qualify an employee for one year without pay and allowances. The bond requires service equal to the leave duration; non-compliance requires Rs. 1 lakh payment under the manual.','3 years of continuous services'),
('multi_condition','An eligible supporting staff member chooses compensatory leave rather than payment for working a seventh continuous day. Within what period must that leave be used, and which staff groups are excluded from that payment alternative?','5.5.8','7','compensatory_options','Compensatory leave must be used within six months. The payment alternative excludes residential wardens and staff in key essential services departments or sections.','within six months'),
('multi_condition','For a resigning faculty member, what notice period and semester-release condition apply, and can accumulated leave reduce the notice period?','5.8.1','8;9','resignation_notice','Faculty normally give three months written notice and are relieved only at the end of an academic semester. Accumulated leave cannot be adjusted against notice. Waiver remains employer discretion.','cannot be adjusted towards the notice period'),
('multi_condition','How does earned leave treat holidays inside a leave period compared with holidays prefixed or suffixed to it?','5.5.2(v)','4','earned_leave_holidays','Intervening holidays and weekends count as earned leave. Prefixed or suffixed holidays and weekends do not count as earned leave.','Intervening holidays, Saturdays and Sundays'),
('ambiguous_unsupported','Can I take leave next week?','','','ambiguous_leave','Ask which leave type, employee category, service history and relevant dates apply. The question lacks enough information for a specific entitlement.',''),
('ambiguous_unsupported','What does XPL mean in this HR manual?','','','unknown_acronym','Clarify or abstain. No verified XPL expansion is supplied in this corpus.',''),
('ambiguous_unsupported','What is the maximum annual reimbursement for a home internet connection?','','','unsupported_internet','Abstain: the supplied chapter does not specify a home-internet reimbursement limit.',''),
('ambiguous_unsupported','How many days of paid adoption leave are available to an employee?','','','unsupported_adoption','Abstain: the supplied chapter does not establish an adoption-leave entitlement. Do not substitute maternity rules.',''),
('ambiguous_unsupported','Does this handbook allow an employee to work remotely from another country for a month?','','','unsupported_remote','Abstain: the supplied chapter does not establish international remote-work permission.',''),
('ambiguous_unsupported','Will my leave balance be paid to me?','','','ambiguous_encashment','Ask which leave type and whether the situation is routine encashment, resignation or death during service. Do not generalize earned-leave rules to every leave balance.','')]
def main():
 pages=[re.sub(r'\s+',' ',p.extract_text()) for p in PdfReader(PDF).pages]
 rows=[];refs=[]
 for i,(cat,q,sec,pagestr,fam,answer,anchor) in enumerate(DATA,1):
  qid=f'NEW{i:03}';pageids=[int(x) for x in pagestr.split(';') if x]
  excerpt=''
  if anchor:
   anchor=re.sub(r'\s+',' ',anchor)
   matches=[(n,pages[n-1].lower().find(anchor.lower())) for n in pageids]
   hits=[(n,pos) for n,pos in matches if pos>=0]
   if not hits:raise ValueError((qid,anchor,'anchor not found'))
   n,pos=hits[0];excerpt=pages[n-1][max(0,pos-150):pos+len(anchor)+220]
  rows.append(dict(question_id=qid,category=cat,question=q,answerability='answerable' if pageids else 'ambiguous' if fam.startswith('ambiguous') else 'unsupported',reference_section=sec,reference_page=pagestr,semantic_family_id=fam,author_id='AI_Codex_candidate',overlap_screened='PENDING',reviewer_approved='PENDING'))
  refs.append(dict(question_id=qid,reference_answer=answer,source_pdf=str(PDF.relative_to(ROOT)),source_sha256=hashlib.sha256(PDF.read_bytes()).hexdigest(),pdf_pages=pageids,printed_pages=[n+25 for n in pageids],sections=sec,source_excerpt=excerpt,reference_status='AI_DRAFT_REQUIRES_SOURCE_REVIEW'))
 path=EVAL/'development/question_authoring_template.csv'
 with path.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 (EVAL/'development/reference_answers_candidate.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in refs))
 (EVAL/'development/authoring_audit.json').write_text(json.dumps({'status':'AI_AUTHORED_CANDIDATES_NOT_FROZEN','count':len(rows),'system_answers_consulted':False,'replacements':[],'source_sha256':refs[0]['source_sha256']},indent=2))
 print('Authored',len(rows),'candidates; no human approvals recorded.')
if __name__=='__main__':main()
