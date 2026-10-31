# Failure analysis: doc-first document selection (mini)

Doc-first = whole-document BM25 -> top-1 document. A miss is a query whose top-1 document is not the gold one (= DRM for doc-first). Causes, in priority order: name_missing (a distinctive word from the query's 'Consider ...;' clause is absent from the gold text), template_sibling (picked doc's MinHash Jaccard with the gold doc is >= 0.1 above the subset's random-pair background), other. fixed_by_filename_match = misses where the distinctive words match exactly one file name, the gold one.

| subset | queries | misses | drm@1 | background_jaccard | name_missing | template_sibling | other | fixed_by_filename_match |
|---|---|---|---|---|---|---|---|---|
| contractnli | 194 | 62 | 0.32 | 0.004 | 45 | 0 | 17 | 62 |
| cuad | 194 | 1 | 0.005 | 0.001 | 0 | 0 | 1 | 0 |
| maud | 194 | 11 | 0.057 | 0.038 | 0 | 0 | 11 | 11 |
| privacy_qa | 194 | 55 | 0.284 | 0.001 | 19 | 0 | 36 | 55 |

## Example misses

### contractnli
- [other] jac=0.02 missing=[] | Consider the Non-Disclosure Agreement between CEII and NDA; Does the document specify whether the Receiving Pa
  gold: `contractnli/ceii-and-nda.txt` picked: `contractnli/VELCO_20NDA_20rev0_20Dec_2014_202015.txt`
- [other] jac=0.02 missing=[] | Consider the Non-Disclosure Agreement between CEII and NDA; Does the document indicate that the Agreement does
  gold: `contractnli/ceii-and-nda.txt` picked: `contractnli/VELCO_20NDA_20rev0_20Dec_2014_202015.txt`
- [other] jac=0.02 missing=[] | Consider the Non-Disclosure Agreement between CEII and NDA; Does the document include a clause that prevents t
  gold: `contractnli/ceii-and-nda.txt` picked: `contractnli/VELCO_20NDA_20rev0_20Dec_2014_202015.txt`
- [other] jac=0.02 missing=[] | Consider the Non-Disclosure Agreement between CEII and NDA; Does the document state that Confidential Informat
  gold: `contractnli/ceii-and-nda.txt` picked: `contractnli/VELCO_20NDA_20rev0_20Dec_2014_202015.txt`
- [other] jac=0.02 missing=[] | Consider the Non-Disclosure Agreement between CEII and NDA; Does the document mention that some obligations of
  gold: `contractnli/ceii-and-nda.txt` picked: `contractnli/VELCO_20NDA_20rev0_20Dec_2014_202015.txt`
- [other] jac=0.02 missing=[] | Consider the Non-Disclosure Agreement between CEII and NDA; Does the document permit the Receiving Party to re
  gold: `contractnli/ceii-and-nda.txt` picked: `contractnli/VELCO_20NDA_20rev0_20Dec_2014_202015.txt`
- [other] jac=0.02 missing=[] | Consider the Non-Disclosure Agreement between CEII and NDA; Does the document allow the Receiving Party to sha
  gold: `contractnli/ceii-and-nda.txt` picked: `contractnli/VELCO_20NDA_20rev0_20Dec_2014_202015.txt`
- [other] jac=0.02 missing=[] | Consider the Non-Disclosure Agreement between CEII and NDA; Does the document permit the Receiving Party to cr
  gold: `contractnli/ceii-and-nda.txt` picked: `contractnli/VELCO_20NDA_20rev0_20Dec_2014_202015.txt`
- [other] jac=0.02 missing=[] | Consider the Non-Disclosure Agreement between CEII and NDA; Does the document require the Receiving Party to n
  gold: `contractnli/ceii-and-nda.txt` picked: `contractnli/VELCO_20NDA_20rev0_20Dec_2014_202015.txt`
- [other] jac=0.02 missing=[] | Consider the Non-Disclosure Agreement between CEII and NDA; Does the document allow the Receiving Party to sha
  gold: `contractnli/ceii-and-nda.txt` picked: `contractnli/VELCO_20NDA_20rev0_20Dec_2014_202015.txt`
- [other] jac=0.02 missing=[] | Consider the Non-Disclosure Agreement between CEII and NDA; Does the document restrict the use of Confidential
  gold: `contractnli/ceii-and-nda.txt` picked: `contractnli/VELCO_20NDA_20rev0_20Dec_2014_202015.txt`
- [other] jac=0.00 missing=[] | Consider Seeed's Non-Disclosure Agreement; Does the document allow the Receiving Party to share some Confident
  gold: `contractnli/NDA-Seeed.txt` picked: `contractnli/simply-fashion---standard-nda.txt`

### cuad
- [other] jac=0.00 missing=[] | Consider the Amendment No. 3 to Wireless Content License Agreement between Fox Mobile Entertainment, Inc. and 
  gold: `cuad/GluMobileInc_20070319_S-1A_EX-10.09_436630_EX-10.09_Content License Agreement4.txt` picked: `cuad/GluMobileInc_20070319_S-1A_EX-10.09_436630_EX-10.09_Content License Agreement1.txt`

### maud
- [other] jac=0.02 missing=[] | Consider the Merger Agreement between "First Bancorp" and "Select Bancorp, Inc."; What is the Type of Consider
  gold: `maud/Select_Bancorp_Inc_First_Bancorp.txt` picked: `maud/Dime Community Bancshares, Inc._Bridge Bancorp, Inc..txt`
- [other] jac=0.02 missing=[] | Consider the Merger Agreement between "First Bancorp" and "Select Bancorp, Inc."; Information about the Closin
  gold: `maud/Select_Bancorp_Inc_First_Bancorp.txt` picked: `maud/Dime Community Bancshares, Inc._Bridge Bancorp, Inc..txt`
- [other] jac=0.02 missing=[] | Consider the Merger Agreement between "First Bancorp" and "Select Bancorp, Inc."; Information about the Closin
  gold: `maud/Select_Bancorp_Inc_First_Bancorp.txt` picked: `maud/Dime Community Bancshares, Inc._Bridge Bancorp, Inc..txt`
- [other] jac=0.03 missing=[] | Consider the Merger Agreement between "First Bancorp" and "Select Bancorp, Inc."; What is the Target's Represe
  gold: `maud/Select_Bancorp_Inc_First_Bancorp.txt` picked: `maud/County Bancorp, Inc._Nicolet Bankshares, Inc..txt`
- [other] jac=0.02 missing=[] | Consider the Merger Agreement between "First Bancorp" and "Select Bancorp, Inc."; What is the Definition of "M
  gold: `maud/Select_Bancorp_Inc_First_Bancorp.txt` picked: `maud/Dime Community Bancshares, Inc._Bridge Bancorp, Inc..txt`
- [other] jac=0.02 missing=[] | Consider the Merger Agreement between "First Bancorp" and "Select Bancorp, Inc."; What is the Definition of "K
  gold: `maud/Select_Bancorp_Inc_First_Bancorp.txt` picked: `maud/Dime Community Bancshares, Inc._Bridge Bancorp, Inc..txt`
- [other] jac=0.02 missing=[] | Consider the Merger Agreement between "First Bancorp" and "Select Bancorp, Inc."; Where is the No-Shop Clause
  gold: `maud/Select_Bancorp_Inc_First_Bancorp.txt` picked: `maud/Dime Community Bancshares, Inc._Bridge Bancorp, Inc..txt`
- [other] jac=0.02 missing=[] | Consider the Merger Agreement between "First Bancorp" and "Select Bancorp, Inc."; What is the Definition of "S
  gold: `maud/Select_Bancorp_Inc_First_Bancorp.txt` picked: `maud/Dime Community Bancshares, Inc._Bridge Bancorp, Inc..txt`
- [other] jac=0.02 missing=[] | Consider the Merger Agreement between "First Bancorp" and "Select Bancorp, Inc."; What are the Ordinary course
  gold: `maud/Select_Bancorp_Inc_First_Bancorp.txt` picked: `maud/Dime Community Bancshares, Inc._Bridge Bancorp, Inc..txt`
- [other] jac=0.02 missing=[] | Consider the Merger Agreement between "First Bancorp" and "Select Bancorp, Inc."; I want information about the
  gold: `maud/Select_Bancorp_Inc_First_Bancorp.txt` picked: `maud/Dime Community Bancshares, Inc._Bridge Bancorp, Inc..txt`
- [other] jac=0.02 missing=[] | Consider the Merger Agreement between "First Bancorp" and "Select Bancorp, Inc."; Where is the Specific Perfor
  gold: `maud/Select_Bancorp_Inc_First_Bancorp.txt` picked: `maud/Dime Community Bancshares, Inc._Bridge Bancorp, Inc..txt`

### privacy_qa
- [name_missing] jac=0.00 missing=['list', 'reminder', 'day', 'planner'] | Consider "TickTick: To Do List with Reminder, Day Planner"'s privacy policy; is my task schedule being tracked
  gold: `privacy_qa/TickTick_ To Do List with Reminder, Day Planner.txt` picked: `privacy_qa/Wordscapes.txt`
- [name_missing] jac=0.00 missing=['list', 'reminder', 'day', 'planner'] | Consider "TickTick: To Do List with Reminder, Day Planner"'s privacy policy; can it view my real name?
  gold: `privacy_qa/TickTick_ To Do List with Reminder, Day Planner.txt` picked: `privacy_qa/Wordscapes.txt`
- [name_missing] jac=0.00 missing=['list', 'reminder', 'day', 'planner'] | Consider "TickTick: To Do List with Reminder, Day Planner"'s privacy policy; can i delete my personally identi
  gold: `privacy_qa/TickTick_ To Do List with Reminder, Day Planner.txt` picked: `privacy_qa/Wordscapes.txt`
- [name_missing] jac=0.00 missing=['list', 'reminder', 'day', 'planner'] | Consider "TickTick: To Do List with Reminder, Day Planner"'s privacy policy; will the application make money o
  gold: `privacy_qa/TickTick_ To Do List with Reminder, Day Planner.txt` picked: `privacy_qa/Wordscapes.txt`
- [name_missing] jac=0.00 missing=['list', 'reminder', 'day', 'planner'] | Consider "TickTick: To Do List with Reminder, Day Planner"'s privacy policy; who has access to whatever i crea
  gold: `privacy_qa/TickTick_ To Do List with Reminder, Day Planner.txt` picked: `privacy_qa/Viber Messenger.txt`
- [name_missing] jac=0.00 missing=['list', 'reminder', 'day', 'planner'] | Consider "TickTick: To Do List with Reminder, Day Planner"'s privacy policy; does this app capture my ip addre
  gold: `privacy_qa/TickTick_ To Do List with Reminder, Day Planner.txt` picked: `privacy_qa/Wordscapes.txt`
- [other] jac=0.00 missing=[] | Consider "Groupon"'s privacy policy; is my search and purchase history shared with advertisers?
  gold: `privacy_qa/Groupon.txt` picked: `privacy_qa/Wordscapes.txt`
- [other] jac=0.00 missing=[] | Consider "Groupon"'s privacy policy; does it need my location at all times, or can i just type in it whenever 
  gold: `privacy_qa/Groupon.txt` picked: `privacy_qa/Wordscapes.txt`
- [other] jac=0.00 missing=[] | Consider "23andMe"'s privacy policy; can i delete my personally identifying information?
  gold: `privacy_qa/23andMe.txt` picked: `privacy_qa/Wordscapes.txt`
- [other] jac=0.00 missing=[] | Consider "Keep"'s privacy policy; who has access to my workout plans?
  gold: `privacy_qa/Keep.txt` picked: `privacy_qa/Wordscapes.txt`
- [other] jac=0.00 missing=[] | Consider "Keep"'s privacy policy; will my fitness coach share my information with others?
  gold: `privacy_qa/Keep.txt` picked: `privacy_qa/Wordscapes.txt`
- [other] jac=0.00 missing=[] | Consider "Keep"'s privacy policy; will my progress only be posted to social media if i want it to?
  gold: `privacy_qa/Keep.txt` picked: `privacy_qa/Wordscapes.txt`
