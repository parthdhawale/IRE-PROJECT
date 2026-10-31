# Where nb_band misfiles held-out documents

Same setup, folds and band as run_doc_grouping.py. For each miss, `pulled_by` lists the band words with the largest count * (log P(w|predicted) - log P(w|gold)), i.e. the words that pushed the document toward the wrong group (count in parentheses). `prior_gap` = log P(predicted) - log P(gold), the push from group size alone.

## coarse level: 34 misses of 714 documents (top-1 accuracy 0.952)

- Also missed by centroid: 2 of 34; nb_band-only misses: 32.
- Mean prior_gap on misses: -1.00 (positive = pushed toward the larger group).

### Most frequent confusions (gold -> predicted)

- 15x `cuad` -> `maud`
- 10x `cuad` -> `contractnli`
- 6x `contractnli` -> `cuad`
- 2x `cuad` -> `privacy_qa`
- 1x `contractnli` -> `privacy_qa`

### Accuracy by document length (band tokens)

| length_tercile   |   size |   mean |
|:-----------------|-------:|-------:|
| short            |    238 |  0.945 |
| medium           |    238 |  0.941 |
| long             |    238 |  0.971 |

### Example misses (coarse)

| doc_id                                                                                                                                                                     | gold        | pred        |   band_tokens |   prior_gap | pulled_by                                                                                                                                                     |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------|:------------|--------------:|------------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| cuad/WHITESMOKE,INC_11_08_2011-EX-10.26-PROMOTION AND DISTRIBUTION AGREEMENT.txt                                                                                           | cuad        | privacy_qa  |          2481 |       -4.31 | google(251), your(52), browser(41), you(60), app(16), user(82), users(25), privacy(9)                                                                         |
| cuad/CreditcardscomInc_20070810_S-1_EX-10.33_362297_EX-10.33_Affiliate Agreement.txt                                                                                       | cuad        | privacy_qa  |          1205 |       -4.12 | chase(115), com(71), www(31), your(12), vacation(22), website(18), deals(9), you(7)                                                                           |
| contractnli/Focus-Group-APIC-Seattle-Confidentiality-Agreement-031115.txt                                                                                                  | contractnli | privacy_qa  |           128 |       -2.54 | you(16), your(4), focus(8), study(4), pii(3), discussion(3), about(1), incident(1)                                                                            |
| cuad/KNOWLABS,INC_08_15_2005-EX-10-INTELLECTUAL PROPERTY AGREEMENT.txt                                                                                                     | cuad        | contractnli |           318 |       -1.59 | ronald(2), province(2), architectures(1), variation(2), drawings(2), sensitive(1), recordings(2), secrets(3)                                                  |
| cuad/Quaker Chemical Corporation - NON COMPETITION AND NON SOLICITATION AGREEMENT.txt                                                                                      | cuad        | contractnli |           649 |       -1.59 | buyer(18), sellers(9), solicitation(11), india(7), recipient(2), raymond(2), restrict(3), degree(2)                                                           |
| cuad/ReedsInc_20191113_10-Q_EX-10.4_11888303_EX-10.4_Development Agreement.txt                                                                                             | cuad        | contractnli |           716 |       -1.59 | reed(76), independently(5), neutral(6), secrets(4), concepts(3), alcohol(11), province(2), injunctive(2)                                                      |
| cuad/WOMENSGOLFUNLIMITEDINC_03_29_2000-EX-10.13-ENDORSEMENT AGREEMENT - Intellectual Property Rights                 Confidentiality and Non-Use Obligations Agreement.txt | cuad        | contractnli |           160 |       -1.58 | recipient(26), secret(3), designs(3), lawfully(2), disclosing(1), her(2), douglas(2), she(1)                                                                  |
| cuad/LIGHTBRIDGECORP_11_23_2015-EX-10.26-STRATEGIC ALLIANCE AGREEMENT.txt                                                                                                  | cuad        | contractnli |           459 |       -1.58 | recipient(23), disclosing(5), project(16), pursue(6), london(2), circumvention(1), reproductions(1), compilations(1)                                          |
| cuad/VERSOTECHNOLOGIESINC_12_28_2007-EX-99.3-INTELLECTUAL PROPERTY AGREEMENT.txt                                                                                           | cuad        | contractnli |           155 |       -1.58 | buyer(9), me(6), she(4), my(2), seller(8), came(2), proven(2), davis(2)                                                                                       |
| cuad/LECLANCHÉ S.A. - JOINT DEVELOPMENT AND MARKETING AGREEMENT.txt                                                                                                        | cuad        | contractnli |           589 |       -1.58 | ridge(27), oak(27), opportunities(8), recipient(2), what(6), sa(3), segregate(2), evaluate(2)                                                                 |
| cuad/ABILITYINC_06_15_2020-EX-4.25-SERVICES AGREEMENT.txt                                                                                                                  | cuad        | contractnli |           641 |       -1.58 | recipient(60), care(5), degree(2), computer(6), certify(2), restates(1), technique(2), tangible(2)                                                            |
| cuad/WASTE2ENERGYHOLDINGS,INC_06_03_2010-EX-10.2-STRATEGIC ALLIANCE AGREEMENT.txt                                                                                          | cuad        | contractnli |          1110 |       -1.58 | authorised(11), recipient(8), relation(10), endeavours(9), undertakings(8), unauthorised(3), clause(31), chambers(6)                                          |
| cuad/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT.txt                                                                                                     | cuad        | contractnli |           719 |       -1.58 | ___________________________(50), undersigned(57), ____________________________(20), _________________________(10), truly(10), print(10), yours(10), legend(6) |
| cuad/ALLISONTRANSMISSIONHOLDINGSINC_12_15_2014-EX-99.1-COOPERATION AGREEMENT.txt                                                                                           | cuad        | maud        |           911 |       -1.13 | board(41), stockholder(7), stockholders(6), shares(9), sec(5), outstanding(7), offer(8), proposal(3)                                                          |
| cuad/ALAMOGORDOFINANCIALCORP_12_16_1999-EX-1-AGENCY AGREEMENT.txt                                                                                                          | cuad        | maud        |          3249 |       -1.13 | shares(88), closing(48), respects(36), bank(282), statements(37), consummation(15), opinion(32), adverse(16)                                                  |

## fine level: 178 misses of 462 documents (top-1 accuracy 0.615)

- Also missed by centroid: 66 of 178; nb_band-only misses: 112.
- Mean prior_gap on misses: 0.09 (positive = pushed toward the larger group).

### Most frequent confusions (gold -> predicted)

- 6x `cuad/Collaboration` -> `cuad/Development`
- 5x `cuad/Strategic Alliance` -> `cuad/License`
- 4x `cuad/Supply` -> `cuad/Manufacturing`
- 4x `cuad/Hosting` -> `cuad/Co-Branding`
- 4x `cuad/Hosting` -> `cuad/License`
- 4x `cuad/Collaboration` -> `cuad/Strategic Alliance`
- 3x `cuad/Maintenance` -> `cuad/Distributor`
- 3x `cuad/Development` -> `cuad/Collaboration`
- 3x `cuad/Manufacturing` -> `cuad/Supply`
- 3x `cuad/Maintenance` -> `cuad/Outsourcing`
- 3x `cuad/License` -> `cuad/Development`
- 3x `cuad/Development` -> `cuad/License`

### Accuracy by document length (band tokens)

| length_tercile   |   size |   mean |
|:-----------------|-------:|-------:|
| short            |    154 |  0.623 |
| medium           |    154 |  0.584 |
| long             |    154 |  0.636 |

### Per contract type (top-1)

| gold                    |   docs |   nb_band |   centroid |
|:------------------------|-------:|----------:|-----------:|
| cuad/Marketing          |     10 |      0.1  |       0.2  |
| cuad/Other              |      4 |      0.25 |       0    |
| cuad/Affiliate          |     10 |      0.3  |       0.9  |
| cuad/Collaboration      |     26 |      0.35 |       0.73 |
| cuad/Outsourcing        |     17 |      0.35 |       0.76 |
| cuad/Hosting            |     15 |      0.4  |       0.8  |
| cuad/Maintenance        |     26 |      0.46 |       0.88 |
| cuad/Strategic Alliance |     29 |      0.48 |       0.79 |
| cuad/Promotion          |     12 |      0.5  |       0.83 |
| cuad/Development        |     27 |      0.56 |       0.67 |
| cuad/Manufacturing      |     14 |      0.57 |       0.71 |
| cuad/Service            |     26 |      0.58 |       0.77 |
| cuad/Supply             |     17 |      0.59 |       0.94 |
| cuad/Agency             |     12 |      0.67 |       0.67 |
| cuad/Co-Branding        |     21 |      0.67 |       0.95 |
| cuad/Sponsorship        |     31 |      0.71 |       0.97 |
| cuad/License            |     41 |      0.73 |       0.71 |
| cuad/IP                 |     16 |      0.75 |       0.69 |
| cuad/Transportation     |     13 |      0.77 |       1    |
| cuad/Reseller           |     10 |      0.8  |       0.9  |
| cuad/Joint Venture      |     10 |      0.8  |       0.7  |
| cuad/Endorsement        |     24 |      0.83 |       0.92 |
| cuad/Distributor        |     29 |      0.86 |       0.93 |
| cuad/Consulting         |     11 |      0.91 |       0.91 |
| cuad/Franchise          |     11 |      1    |       0.82 |

### Example misses (fine)

| doc_id                                                                                                              | gold                    | pred               |   band_tokens |   prior_gap | pulled_by                                                                                                             |
|:--------------------------------------------------------------------------------------------------------------------|:------------------------|:-------------------|--------------:|------------:|:----------------------------------------------------------------------------------------------------------------------|
| cuad/WatchitMediaInc_20061201_8-K_EX-10.1_4148672_EX-10.1_Content License Agreement.txt                             | cuad/License            | cuad/Affiliate     |            91 |       -1.39 | cable(10), 2006(4), screen(1), your(1), shown(2), advertisers(1), sponsorship(1), reserves(1)                         |
| cuad/VERSOTECHNOLOGIESINC_12_28_2007-EX-99.3-INTELLECTUAL PROPERTY AGREEMENT.txt                                    | cuad/IP                 | cuad/Other         |           176 |       -1.39 | backhaul(11), martin(3), me(6), she(4), he(4), robert(3), say(2), proven(2)                                           |
| cuad/IPAYMENT,INC_05_14_2007-EX-10.1-SPONSORSHIP AGREEMENT.txt                                                      | cuad/Sponsorship        | cuad/Affiliate     |          3509 |       -1.14 | iso(362), bank(101), program(66), systems(19), equipment(11), sec(14), network(11), debit(24)                         |
| cuad/GIGGLESN_HUGS,INC_06_23_2016-EX-10.2-STRATEGIC ALLIANCE AGREEMENT.txt                                          | cuad/Strategic Alliance | cuad/Consulting    |           880 |       -1.06 | consultant(54), innovations(9), awareness(6), moral(4), concept(5), social(4), brand(17), tv(6)                       |
| cuad/SONUSCORP_03_12_1997-EX-10.11-SPONSORSHIP AGREEMENT.txt                                                        | cuad/Sponsorship        | cuad/Agency        |           857 |       -1.02 | prospectus(40), issuer(63), securities(39), offering(8), certificate(13), subsidiaries(7), columbia(17), capital(6)   |
| cuad/TELKOMSALTD_01_30_2003-EX-10-LICENCE AND MAINTENANCE AGREEMENT.txt                                             | cuad/License            | cuad/Hosting       |          3867 |       -1.01 | 01(70), clause(39), licence(24), system(22), message(14), site(17), customer(19), authorised(6)                       |
| cuad/SUMMAFOURINC_06_19_1998-EX-10.3-SOFTWARE LICENSE AND MAINTENANCE AGREEMENT.txt                                 | cuad/License            | cuad/Hosting       |          3845 |       -0.98 | 1997(51), table(31), detected(36), august(51), detection(48), call(21), dual(18), voice(49)                           |
| cuad/ROCKYMOUNTAINCHOCOLATEFACTORY,INC_12_23_2019-EX-10.2-STRATEGIC ALLIANCE AGREEMENT.txt                          | cuad/Strategic Alliance | cuad/Agency        |          4215 |       -0.98 | registration(150), statement(117), shares(118), prospectus(37), securities(142), offering(26), stock(67), therein(38) |
| cuad/IntegrityFunds_20200121_485BPOS_EX-99.E UNDR CONTR_11948727_EX-99.E UNDR CONTR_Service Agreement.txt           | cuad/Service            | cuad/Marketing     |           945 |       -0.97 | integrity(81), registration(32), statement(58), prospectus(21), shares(28), untrue(9), omission(8), alleged(7)        |
| cuad/VerizonAbsLlc_20200123_8-K_EX-10.4_11952335_EX-10.4_Service Agreement.txt                                      | cuad/Service            | cuad/Marketing     |         11074 |       -0.97 | issuer(264), trustee(301), indenture(274), note(98), cap(72), acquisition(178), transferred(98), principal(71)        |
| cuad/URSCORPNEW_03_17_2014-EX-99-COOPERATION AGREEMENT.txt                                                          | cuad/Collaboration      | cuad/Joint Venture |          1650 |       -0.92 | board(68), ceo(16), chairman(12), director(30), shareholder(10), shares(12), served(12), creation(10)                 |
| cuad/HC2HOLDINGS,INC_05_14_2020-EX-10.1-COOPERATION AGREEMENT.txt                                                   | cuad/Collaboration      | cuad/Joint Venture |          2359 |       -0.92 | capital(83), board(64), mg(76), chairman(10), statements(19), director(31), shares(12), participants(5)               |
| cuad/TRANSMONTAIGNEPARTNERSLLC_03_13_2020-EX-10.9-SERVICES AGREEMENT.txt                                            | cuad/Service            | cuad/Joint Venture |           111 |       -0.92 | operating(8), article(2), inter(1), colorado(3), principle(1), capital(1), august(1), individuals(1)                  |
| cuad/EmeraldHealthBioceuticalsInc_20200218_1-A_EX1A-6 MAT CTRCT_11987205_EX1A-6 MAT CTRCT_Development Agreement.txt | cuad/Development        | cuad/Consulting    |           497 |       -0.89 | murray(46), dr(43), 001(7), consulting(2), his(2), travel(4), consultant(1), phoenix(3)                               |
| cuad/ElPolloLocoHoldingsInc_20200306_10-K_EX-10.16_12041700_EX-10.16_Development Agreement.txt                      | cuad/Development        | cuad/Franchise     |          2271 |       -0.85 | franchisor(150), franchise(74), restaurant(57), franchisee(15), restaurants(21), site(50), lease(17), marks(19)       |

