"""Classifier-only reproduction from committed CSV; never writes a model."""
import csv,json,sys
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit,StratifiedGroupKFold
from sklearn.metrics import classification_report
ROOT=Path(__file__).resolve().parents[2]
def main():
    rows=list(csv.DictReader((ROOT/'research/vit_v1/training_halting_dataset_vit.csv').open()))
    names=['attempt','score','best_score','score_delta','chunk_overlap']
    X=[[float(r[k]) for k in names] for r in rows];y=[int(r['halt']) for r in rows];g=[r['original_question'] for r in rows]
    a,b=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=42).split(X,y,g));assert not ({g[i] for i in a}&{g[i] for i in b})
    model=LogisticRegression(class_weight='balanced',random_state=42,max_iter=1000).fit([X[i][:4] for i in a],[y[i] for i in a])
    out={'heldout_groups_train':len({g[i] for i in a}),'heldout_groups_test':len({g[i] for i in b}),'heldout_report':classification_report([y[i] for i in b],model.predict([X[i][:4] for i in b]),output_dict=True,zero_division=0),'always_stop_accuracy':sum(y)/len(y),'schema':names[:4],'note':'Exploratory grouped ablations; no final-test model selection','ablations':{}}
    for cols in [[0,1,2,3],[0,1,2,3,4],[1],[0,1,2],[0,1,3],[0,2,3]]:
        actual=[];preds=[]
        for a,b in StratifiedGroupKFold(5,shuffle=True,random_state=42).split(X,y,g):
            assert not ({g[i] for i in a}&{g[i] for i in b})
            m=LogisticRegression(class_weight='balanced',random_state=42,max_iter=1000).fit([[X[i][j] for j in cols] for i in a],[y[i] for i in a])
            preds.extend(m.predict([[X[i][j] for j in cols] for i in b]));actual.extend(y[i] for i in b)
        out['ablations'][str(cols)]=classification_report(actual,preds,output_dict=True,zero_division=0)
    Path(__file__).with_name('ml_audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print('Classifier reproduction complete; no model overwritten.')
if __name__=='__main__':main()
