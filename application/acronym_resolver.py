"""Exact source-grounded aliases; no guessed expansions."""
import json,re
from pathlib import Path
GLOSSARY=Path(__file__).parent/'research/review3/verified_glossary.json'
def resolve(question,entries=None):
    entries=json.loads(GLOSSARY.read_text()) if entries is None else entries
    matched=[]; expanded=question; ambiguous=False
    aliases={}
    for entry in entries:
        for alias in entry['aliases']: aliases.setdefault(alias,[]).append(entry)
    for alias,options in sorted(aliases.items(),key=lambda x:-len(x[0])):
        # Punctuation is optional, letters must remain contiguous except dots/spaces.
        pattern=r'(?<!\w)'+r'\.?\s*'.join(map(re.escape,alias))+r'\.?(?!\w)'
        if re.search(pattern,expanded,re.I):
            if len({e['full_form'] for e in options})>1: ambiguous=True;continue
            e=options[0]; matched.append(e)
            expanded=re.sub(pattern,e['full_form'],expanded,flags=re.I)
    unknown=[]
    for token in re.findall(r'\b[A-Z][A-Z.]{1,9}\b',question):
        if token.replace('.','') not in aliases and token not in {'VIT','HR','PDF'}: unknown.append(token)
    explicit=re.fullmatch(r"(?:what (?:is|does)|define|explain)\s+([a-z.]{2,10})(?:\s+(?:mean|stand for))?\??",question.strip(),re.I)
    if explicit and not matched and explicit.group(1).lower() not in {'leave','vacation','resignation'}:
        unknown.append(explicit.group(1))
    bare=bool(re.fullmatch(r'[A-Za-z.]{2,10}',question.strip()))
    definition_text=re.sub(r'^(?:what is|what does|define|explain)\s+', '', question.strip(), flags=re.I)
    definition_text=re.sub(r'\s+(?:mean|stand for)\??$', '', definition_text, flags=re.I)
    compact=re.sub(r'[.\s?]', '', definition_text).casefold()
    lookup=len(matched)==1 and compact in {re.sub(r'[.\s]', '', a).casefold() for a in matched[0]['aliases']}
    return {'query':expanded,'entries':matched,'status':'ambiguous' if ambiguous else 'unknown' if unknown or (bare and not matched) else 'resolved' if matched else 'unchanged','lookup_only':lookup}
