# Quick descriptive stats — joined panel

> One row per (election × prefecture). 470 rows total. **NOT causal**, just first-look correlations.

## 1. Coverage

```
                            n_prefs  has_treat
election_id  election_date                    
2013_sangiin 2013-07-21          47          0
2014_shugiin 2014-12-14          47          0
2016_sangiin 2016-07-10          47          0
2017_shugiin 2017-10-22          47         47
2019_sangiin 2019-07-21          47         47
2021_shugiin 2021-10-31          47         47
2022_sangiin 2022-07-10          47         47
2024_shugiin 2024-10-27          47         47
2025_sangiin 2025-07-20          47         47
2026_shugiin 2026-02-08          47         47
```

## 2. Foreign-resident totals (national sum, latest pre-election period)

```
election_id
2017_shugiin    2381698
2019_sangiin    2729811
2021_shugiin    2820678
2022_sangiin    2949591
2024_shugiin    3578523
2025_sangiin    3949777
2026_shugiin    3949777
```

## 3. Top-10 prefectures by foreign share (latest = 2025 sangiin period)

```
prefecture  foreign_total
       東京都       775340.0
       大阪府       360390.0
       愛知県       345900.0
      神奈川県       306363.0
       埼玉県       277209.0
       千葉県       247580.0
       兵庫県       148569.0
       静岡県       128311.0
       福岡県       119392.0
       茨城県       106490.0
```

## 4. Correlation: foreign-residents level vs party vote share (latest sangiin = 2025)

```
       party  corr_with_foreign_total
share_日本維新の会                 0.255912
   share_公明党                -0.023793
 share_立憲民主党                -0.144481
 share_自由民主党                -0.570660
```

Interpretation: positive corr → party does *better* in prefectures with more foreign residents (which are also the urban / Tokyo / Osaka / Aichi triad). NOT a causal statement — confounded by population, urbanization, etc.

## 5. Correlation: foreign-residents YoY growth vs party vote share (2025 sangiin)

```
       party  corr_with_foreign_growth_yoy
   share_公明党                      0.317799
 share_立憲民主党                      0.088540
share_日本維新の会                      0.022696
 share_自由民主党                     -0.115764
```

## 6. Sanseitō (2026 shugiin) vs foreign-residents — the key relationship

- Sanseitō vote share vs foreign-residents level: r = **-0.121**

- Sanseitō vote share vs log(foreign-residents): r = **0.051**

- Sanseitō vote share vs YoY growth in foreign-residents: r = **0.013**


Top-10 Sanseitō-share prefectures (2026 shugiin):

```
prefecture  share_参政党  foreign_total  foreign_growth_yoy
       群馬県  15.387755        87299.0            0.098515
       福井県  15.364467        20783.0            0.097481
       熊本県  14.350972        30825.0            0.124713
       大分県  13.202402        21708.0            0.145299
       愛媛県  13.201404        19069.0            0.093469
       沖縄県  12.943137        31249.0            0.157542
       福岡県  12.815314       119392.0            0.136536
       栃木県  12.663343        59809.0            0.097554
       山口県  12.621849        21866.0            0.058937
       三重県  12.602393        71154.0            0.069840
```
