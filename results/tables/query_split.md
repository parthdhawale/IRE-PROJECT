# Dev / test query split (by gold document)

Dev = queries whose gold document is in routing fold(s) [0] of 5 (leak-safe: stratified by group, near-duplicates together); test = the rest.

| subset      |   dev_queries |   test_queries |   dev_documents |   test_documents |   dev_share_of_queries |
|:------------|--------------:|---------------:|----------------:|-----------------:|-----------------------:|
| contractnli |           195 |            782 |              19 |               76 |                  0.2   |
| cuad        |           860 |           3182 |              93 |              369 |                  0.213 |
| maud        |           329 |           1347 |              30 |              120 |                  0.196 |
| privacy_qa  |            19 |            175 |               1 |                6 |                  0.098 |
| all         |          1403 |           5486 |             143 |              571 |                  0.204 |
