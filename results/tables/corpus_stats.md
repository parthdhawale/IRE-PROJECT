# Corpus statistics (LegalBench-RAG)

## Documents (characters)

| subset      |   docs |   total_chars |    min |   median |   mean |    max |   chunks_500 |
|:------------|-------:|--------------:|-------:|---------:|-------:|-------:|-------------:|
| contractnli |     95 |       1013969 |   2712 |     9361 |  10673 |  33405 |         2073 |
| cuad        |    462 |      25792044 |   1660 |    36820 |  55826 | 338211 |        51815 |
| maud        |    150 |      52721337 | 105682 |   335614 | 351475 | 999236 |       105522 |
| privacy_qa  |      7 |        176864 |   3179 |    27447 |  25266 |  54158 |          357 |
| ALL         |    714 |      79704214 |        |          |        |        |       159767 |

## Queries

Mini = 194 queries per subset, selected as in legalbenchrag/benchmark.py. The retrieval pool for every query is the full subset corpus.

| subset      |   queries_full |   queries_mini |   docs_touched_mini |   multi_doc_queries |   snippets |   mean_snippets_per_q | round_trip   | ok   |
|:------------|---------------:|---------------:|--------------------:|--------------------:|-----------:|----------------------:|:-------------|:-----|
| contractnli |            977 |            194 |                  18 |                   0 |       1389 |                  1.42 | 100.0%       | True |
| cuad        |           4042 |            194 |                  29 |                   0 |       6247 |                  1.55 | 100.0%       | True |
| maud        |           1676 |            194 |                  18 |                   0 |       2839 |                  1.69 | 100.0%       | True |
| privacy_qa  |            194 |            194 |                   7 |                   0 |        453 |                  2.34 | 100.0%       | True |
| ALL         |           6889 |            776 |                  72 |                   0 |      10928 |                       |              |      |

## CUAD contract types (parsed from file names, evaluation only)

| cuad_type          |   docs |
|:-------------------|-------:|
| License            |     41 |
| Sponsorship        |     31 |
| Distributor        |     29 |
| Strategic Alliance |     29 |
| Development        |     27 |
| Service            |     26 |
| Collaboration      |     26 |
| Maintenance        |     26 |
| Endorsement        |     24 |
| Co-Branding        |     21 |
| Outsourcing        |     17 |
| Supply             |     17 |
| IP                 |     16 |
| Hosting            |     15 |
| Manufacturing      |     14 |
| Transportation     |     13 |
| Agency             |     12 |
| Promotion          |     12 |
| Consulting         |     11 |
| Franchise          |     11 |
| Joint Venture      |     10 |
| Reseller           |     10 |
| Marketing          |     10 |
| Affiliate          |     10 |
| Non-Compete        |      3 |
| Other              |      1 |
