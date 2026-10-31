# Phase 1: H1 boilerplate-share analysis and go/no-go

**Decision: NO-GO**

Rule: GO if median share at tau=0.5 is >= 0.25 on ContractNLI AND on at least one of CUAD (within contract type) or MAUD.

## Medians at tau=0.5

| subset      |   median_share |
|:------------|---------------:|
| contractnli |          0     |
| cuad        |          0     |
| maud        |          0.173 |
| privacy_qa  |          0     |

## Medians at every tau

| subset      |   0.3 |   0.5 |   0.7 |   0.9 |
|:------------|------:|------:|------:|------:|
| contractnli | 0     | 0     | 0     | 0     |
| cuad        | 0     | 0     | 0     | 0     |
| maud        | 0.417 | 0.173 | 0.056 | 0.016 |
| privacy_qa  | 0     | 0     | 0     | 0     |

## Sensitivity check: is NO-GO a shingle-size artifact?

Before accepting NO-GO, we tested whether the config's 5-word shingle size was simply too
strict to catch real overlap (ContractNLI is independently reworded even where templated, so
exact 5-word runs rarely survive). Swept shingle size on ContractNLI only (1,951 leaves):

| shingle size | tau=0.2 median | tau=0.3 median | tau=0.5 median |
|---|---|---|---|
| 5 (config default) | 0.013 | 0.000 | 0.000 |
| 3 | 0.124 | 0.067 | 0.002 |
| 2 | **0.248** | 0.091 | 0.008 |

shingle=2, tau=0.2 lands right at the go_median_share threshold (0.25) -- looked promising.
A concrete pair also moved: the Bosch and JBF NDAs' near-identical "counterparts" clauses
("...deemed an original...constitute one and the same instrument...") score 0.0625 at 5-word
shingles but 0.289 at 2-word shingles.

**But a random sample of 8 of the 7,465 edges found at shingle=2/tau=0.2 showed this is mostly
false positives**, not real signal: matched pairs are thematically related NDA clauses (both
mention "Confidential Information", "Receiving Party", etc.) but are **different clause types**
-- e.g. a Representations & Warranties authority clause matched against an unrelated Authority
to Sign signature clause; an Exceptions-to-Confidential-Information clause matched against an
unrelated severability clause. Two-word shingles are short enough to match on shared *legal
vocabulary* alone, without the pair being the same templated clause.

**Conclusion: NO-GO is not a shingle-size artifact.** The 5-word config is, if anything,
validated by this check -- it's the setting that avoids exactly this false-positive mode. The
real finding stands: MAUD has genuine verbatim template reuse (large law firms copy-pasting
whole definition blocks between deals); ContractNLI, CUAD and PrivacyQA are templated in
*structure* but independently reworded, which lexical MinHash can't distinguish from "uses
similar legal vocabulary" at any shingle size we tried.

## Caveat on the MAUD result

MAUD's "most-shared leaves" list below is entirely `"________________"` (redaction/blank-line
placeholders appearing in 134 of 150 documents) -- a degenerate match, not real shared legal
text. These lines are short (10-50 chars), so they likely don't move the char-weighted median
share much, but the "most shared leaves" list as currently computed is not useful for MAUD until
these placeholder lines are filtered out. The underlying 0.173 median at tau=0.5 should still be
double-checked with placeholders excluded before being reported as final.

## 10 most-shared leaves per subset (tau=0.5)

### contractnli

- 4 docs | `contractnli/5-NSK-Confidentiality-Agreement-for-Suppliers.txt#35` | 12.2. Entire Agreement. This Agreement constitutes the entire agreement between
- 4 docs | `contractnli/Aspiegel_NDA_template.txt#44` | 8. Entire Agreement and Variation 8.1 This Agreement constitutes the entire agre
- 4 docs | `contractnli/IGC-Non-Disclosure-Agreement-LSE-Sample.txt#68` | 7. ENTIRE AGREEMENT AND VARIATION 7.1 This Agreement constitutes the entire agre
- 4 docs | `contractnli/Kenway-NDA-Form-Blank.txt#54` | 7.1 This Agreement constitutes the entire agreement between the Parties and supe
- 3 docs | `contractnli/Aspiegel_NDA_template.txt#41` | 6.2 Termination of this Agreement shall not affect any accrued rights or remedie
- 3 docs | `contractnli/Aspiegel_NDA_template.txt#51` | 12. No Partnership Nothing in this Agreement is intended to, or shall be deemed
- 3 docs | `contractnli/Aspiegel_NDA_template.txt#9` | (c) any information relating to: (i) the business, affairs, customers, clients,
- 3 docs | `contractnli/IGC-Non-Disclosure-Agreement-LSE-Sample.txt#25` | (e) Is or becomes generally available to the public other than as a result of it
- 3 docs | `contractnli/Kenway-NDA-Form-Blank.txt#6` | (a) the business, affairs, customers, clients, suppliers, plans, intentions, or
- 3 docs | `contractnli/Kenway-NDA-Form-Blank.txt#49` | 5.2 Each Recipient shall indemnify and keep fully indemnified the Disclosing Par

### cuad

- 6 docs | `cuad/ZEBRATECHNOLOGIESCORP_04_16_2014-EX-10.1-INTELLECTUAL PROPERTY AGREEMENT.txt#6` | ARTICLE I DEFINITIONS
- 6 docs | `cuad/CerenceInc_20191002_8-K_EX-10.4_11827494_EX-10.4_Intellectual Property Agreement.txt#27` | ARTICLE I DEFINITIONS
- 6 docs | `cuad/DRKOOPCOMINC_04_21_1999-EX-10.28-SPONSORSHIP AGREEMENT.txt#73` | 9.8.  ENTIRE AGREEMENT. This Agreement is the complete and exclusive agreement b
- 6 docs | `cuad/FIDELITYNATIONALINFORMATIONSERVICES,INC_08_05_2009-EX-10.3-INTELLECTUAL PROPERTY AGREEMENT.txt#2` | ARTICLE I DEFINITIONS...........................................................
- 6 docs | `cuad/VITAMINSHOPPECOMINC_09_13_1999-EX-10.26-SPONSORSHIP AGREEMENT.txt#80` | g)       Entire Agreement.  This Agreement is the complete and
- 6 docs | `cuad/GarrettMotionInc_20181001_8-K_EX-2.4_11364532_EX-2.4_Intellectual Property Agreement.txt#26` | ARTICLE I DEFINITIONS
- 6 docs | `cuad/GSVINC_05_15_1998-EX-10-SPONSORSHIP AGREEMENT.txt#84` | f)    Severability. In the event that any of the provisions of this
- 6 docs | `cuad/FIDELITYNATIONALINFORMATIONSERVICES,INC_08_05_2009-EX-10.3-INTELLECTUAL PROPERTY AGREEMENT.txt#73` | ARTICLE I                                    DEFINITIONS
- 6 docs | `cuad/N2KINC_10_16_1997-EX-10.16-SPONSORSHIP AGREEMENT.txt#59` | 16    17
- 6 docs | `cuad/STAMPSCOMINC_06_24_1999-EX-10.18-SPONSORSHIP AGREEMENT.txt#93` | 18.7 Entire Agreement.  This Agreement is the complete and exclusive agreement

### maud

- 134 docs | `maud/Acacia_Communications_Cisco_Systems.txt#68` | ________________
- 134 docs | `maud/Acacia_Communications_Cisco_Systems.txt#88` | ________________
- 134 docs | `maud/Acacia_Communications_Cisco_Systems.txt#138` | ________________
- 134 docs | `maud/Acacia_Communications_Cisco_Systems.txt#162` | ________________
- 134 docs | `maud/Acacia_Communications_Cisco_Systems.txt#205` | ________________
- 134 docs | `maud/Acacia_Communications_Cisco_Systems.txt#261` | ________________
- 134 docs | `maud/Acacia_Communications_Cisco_Systems.txt#417` | ________________
- 134 docs | `maud/Acacia_Communications_Cisco_Systems.txt#362` | ________________
- 134 docs | `maud/Constellation Pharmaceuticals, Inc._MorphoSys AG.txt#58` | ________________
- 134 docs | `maud/Constellation Pharmaceuticals, Inc._MorphoSys AG.txt#64` | ________________