# 海外文献レビュー：移民流入と選挙結果・政治態度

**対象テーマ**: 日本以外の国における「移民（外国人）の流入が選挙結果や有権者の政治態度に与える影響」の実証研究  
**用途**: 東大2026S「Data Science for Public Policy」グループプロジェクト — 日本版分析の比較基盤  
**作成日**: 2026-05-13

---

## A. ドイツ (AfD・難民危機)

- **Otto & Steinhardt (2014)** — "Immigration and Election Outcomes — Evidence from City Districts in Hamburg." *Regional Science and Urban Economics*, 45(C): 67–79.  
  [https://ideas.repec.org/a/eee/regeco/v45y2014icp67-79.html](https://ideas.repec.org/a/eee/regeco/v45y2014icp67-79.html)
  - **Setting:** ドイツ・ハンブルク市区 / 複数選挙 / 移民比率の変化 / 極右政党（ドイツ国家民主党等）得票率
  - **Identification:** OLS + 過去居住パターンを用いたシフトシェア型IV（内生性対処）
  - **Key finding:** 移民シェアの上昇は極右政党への得票増につながる。特に貧困地区で効果が顕著（グループ脅威メカニズム）。外国人の子どもが流入した幼稚園・学校近辺でも不満が拡大。
  - **日本への含意・差異:** 日本でも大都市の特定区・市（例：川崎市、浜松市）でシフトシェアIVの応用可能性あり。ただし日本では技能実習生など労働移民が主であり、難民ではないため政治的サリアンスが異なる。ハンブルク水準の移民比率（10%超）は日本では2024年時点でも未達。

- **Steinmayr (2021)** — "Contact versus Exposure: Refugee Presence and Voting for the Far Right." *Review of Economics and Statistics*, 103(2): 310–327.  
  [https://direct.mit.edu/rest/article-abstract/103/2/310/97666/](https://direct.mit.edu/rest/article-abstract/103/2/310/97666/)
  - **Setting:** オーストリア・上部オーストリア州 / 2015年難民危機 / 市町村レベル / 難民受け入れ(接触) vs 難民流入目撃(露出) / FPÖ得票率
  - **Identification:** 難民政策による市町村割り当てを利用した準実験（接触 vs 露出の区別）
  - **Key finding:** 難民との**直接接触**（受け入れ市町村）はFPÖ得票を約4pp**減少**させる（接触仮説を支持）。一方、難民が通過するだけの**露出**は約1.5pp**増加**させる。
  - **日本への含意・差異:** 日本では難民認定数が極めて少ない（年間数百人）ため「接触vs露出」の区別自体が適用困難。ただし外国人集住地域の住民態度研究（サーベイデータ）なら応用可能。Allport接触仮説の検証として参照価値が高い。

- **Cantoni, Hagemeister & Westcott (2020)** — "Persistence and Activation of Right-Wing Political Ideology." Working Paper, LMU Munich / CEPR Discussion Paper 143. [(PDF)](https://rationality-and-competition.de/wp-content/uploads/discussion_paper/143.pdf)
  - **Setting:** ドイツ全市町村 / 1933年NSDAP得票 vs 2013–2017年AfD得票 / テキスト分析でAfDの言説転換を計測
  - **Identification:** 1933年ナチス選挙得票を右翼イデオロギーの代理変数として使用（因果主張ではなく相関の持続性を論証）；量的テキスト分析で供給側変化を計測
  - **Key finding:** 1933年にナチスへの支持が強かった市町村は2017年AfDで1sd高い支持率（β≈0.15sd）。ただし2013年（移民強調前）には相関が弱い。需要（態度）が変化したのではなく、AfDが右翼的ニッチを満たすことでlatentな選好が顕在化した。
  - **日本への含意・差異:** 日本では戦前の政治的右翼支持の地理的分布データが利用可能か不明。歴史的持続性アプローチは在日コリアン集住地域（大阪・神奈川）の差別態度との関連研究に示唆を与えうる。

- **Gehrsitz & Ungerer (2022)** — "Jobs, Crime and Votes: A Short-run Evaluation of the Refugee Crisis in Germany." *Economica*, 89(355): 592–626. DOI: 10.1111/ecca.12420  
  [https://onlinelibrary.wiley.com/doi/abs/10.1111/ecca.12420](https://onlinelibrary.wiley.com/doi/abs/10.1111/ecca.12420)
  - **Setting:** ドイツ全郡（Landkreis）/ 2014–2015年難民危機 / 収容施設数×難民数 / 労働市場・犯罪・得票
  - **Identification:** 収容施設の場当たり的割り当て（空き物件次第）による郡レベルの外生的変動を利用したIV
  - **Key finding:** 難民流入は在来労働者の雇用を奪わず、難民自身も正規雇用困難。犯罪は小幅増。**マクロ**では難民増加と極右得票増が相関するが、**ミクロ（接触）**では難民集住地域ほど極右支持が小さい（Steinmayrと整合）。
  - **日本への含意・差異:** 日本での外国人集住（技能実習生等）と地域の選挙結果・治安・労働市場の同時分析に使えるマルチアウトカムの設計として参考になる。

---

## B. スウェーデン・デンマーク・ノルウェー・フィンランド

- **Dustmann, Vasiljeva & Damm (2019)** — "Refugee Migration and Electoral Outcomes." *Review of Economic Studies*, 86(5): 2035–2091. DOI: 10.1093/restud/rdy047  
  [https://academic.oup.com/restud/article-abstract/86/5/2035/5112970](https://academic.oup.com/restud/article-abstract/86/5/2035/5112970)
  - **Setting:** デンマーク全市町村 / 1986–2008年（難民分散政策13年分） / 3選挙サイクル / 難民割り当てシェア / 反移民政党得票率
  - **Identification:** デンマーク難民分散政策による**準ランダム市町村割り当て**（全国で人口比に基づき配分）をIVとして使用
  - **Key finding:** 難民シェア1pp増 → 非都市部では反移民政党得票が議会選1.23pp・市議選1.98pp増加。**最大都市圏では効果が逆転**（接触仮説に一致）。都市・農村間の態度差が鍵。
  - **日本への含意・差異:** 日本版難民分散政策は存在しないため**IV直接移転は不可**。ただし技能実習生の都道府県別割り当てデータ（厚生労働省）を擬似的IV（割り当て定員シェア）として使うアイデアは検討可能。デンマークと比較して日本の難民認定率は極小（0.3%程度）。

- **Dahlberg, Edmark & Lundqvist (2012)** — "Ethnic Diversity and Preferences for Redistribution." *Journal of Political Economy*, 120(1): 41–76.  
  [https://ideas.repec.org/p/ces/ceswps/_3325.html](https://ideas.repec.org/p/ces/ceswps/_3325.html)
  - **Setting:** スウェーデン全市町村 / 1985–1994年難民配置政策 / 市民の所得再分配選好（サーベイ）/ 移民シェア
  - **Identification:** スウェーデン1985–94年難民配置プログラム（市町村への強制割り当て）を外生的変動として使用
  - **Key finding:** 移民シェア増加 → 再分配への支持が有意に低下。高所得・高資産層で効果大。ただし後続研究で結果の頑健性に議論あり（サンプル選択バイアスの指摘）。
  - **日本への含意・差異:** 日本版では「外国人が増えた自治体ほど社会保険への支持が下がるか」を検証できる可能性。ただし日本の外国人は原則として社会保険の完全受給権を持たず、公的サービスへの「脅威感」の構造が異なる。

- **Harmon (2018)** — "Immigration, Ethnic Diversity, and Political Outcomes: Evidence from Denmark." *Scandinavian Journal of Economics*, 120(4): 1043–1074. DOI: 10.1111/sjoe.12239  
  [https://onlinelibrary.wiley.com/doi/10.1111/sjoe.12239](https://onlinelibrary.wiley.com/doi/10.1111/sjoe.12239)
  - **Setting:** デンマーク全市町村 / 1981–2001年 / 民族的多様性指数 / 国政・地方選挙の反移民政党得票率
  - **Identification:** **住宅ストック（歴史的空き物件数）をIV**として移民の内生的立地選択をコントロール（シフトシェアとは異なる）
  - **Key finding:** 民族的多様性増加 → 反移民民族主義政党の得票に有意な正の効果。左翼リベラル政党支持は低下。地方・国政選挙両方で確認。
  - **日本への含意・差異:** 住宅ストックIVは日本の公営住宅・外国人向け宿泊施設データで類似設計が理論上可能。ただし日本では外国人の内生的集住が「職場斡旋」（技能実習制度）に起因し、住宅市場とは別の力学が働く点に注意。

- **Folke (2014)** — "Shades of Brown and Green: Party Effects in Proportional Election Systems." *Journal of the European Economic Association*, 12(5): 1361–1395.  
  [https://ideas.repec.org/a/bla/jeurec/v12y2014i5p1361-1395.html](https://ideas.repec.org/a/bla/jeurec/v12y2014i5p1361-1395.html)
  - **Setting:** スウェーデン全市町村 / 比例代表制 / 小政党（移民強硬派・環境政党）の議席獲得 / 移民・環境・税政策
  - **Identification:** 比例代表制向けに開発されたRD設計（得票率閾値での議席獲得確率の不連続性を利用）
  - **Key finding:** 移民強硬派政党が閾値を超えて議席を得た市町村では移民政策が有意に厳格化。環境政党も環境政策に影響。税政策への効果は小。
  - **日本への含意・差異:** 日本は選挙制度が衆議院小選挙区比例代表並立制であり、Folke型のPR-RDは適用困難。ただし比例代表ブロック（11ブロック）でのRDは理論上可能。外国人に明確に言及する政党（参政党、日本第一党等）の議席閾値前後での政策変化を見るアプローチに示唆。

- **Martén, Hainmueller & Hangartner (2019)** — "Ethnic Networks Can Foster the Economic Integration of Refugees." *Proceedings of the National Academy of Sciences (PNAS)*, 116(33): 16280–16285.  
  [https://www.pnas.org/doi/10.1073/pnas.1820345116](https://www.pnas.org/doi/10.1073/pnas.1820345116)
  - **Setting:** スイス / 2008–2013年難民（一時的保護ステータス取得者8,590人）/ カントン間ランダム割り当て / 就労率（5年間）
  - **Identification:** スイスの26カントンへの**ランダム行政割り当て**（難民は5年間カントン外移住不可）
  - **Key finding:** 同郷コミュニティが大きいカントンに割り当てられた難民ほど就労率が高い（エスニックネットワーク経由の情報共有が効果）。分散政策は統合コストを持つことを示唆。
  - **日本への含意・差異:** 政治態度よりも労働統合の研究だが、外国人集住地域と地域経済への影響を同時に見る本プロジェクトの設計に参考になる。日本の技能実習生が「会社側」に割り当てられる構造はスイスの行政割り当てと一定類似性あり（ただし自発的選択ではない点が同じ）。

---

## C. フランス・オランダ・ベルギー

- **Edo, Giesing, Öztunc & Poutvaara (2019)** — "Immigration and Electoral Support for the Far-Left and the Far-Right." *European Economic Review*, 115(C): 99–143. DOI: 10.1016/j.euroecorev.2019.03.002  
  [https://www.sciencedirect.com/science/article/pii/S0014292119300418](https://www.sciencedirect.com/science/article/pii/S0014292119300418)
  - **Setting:** フランス / 1988–2017年大統領選挙 / 県レベル / 移民シェア（非西洋・低スキル） / 極右候補得票率
  - **Identification:** 1968年移民居住パターンをIVとして使用（シフトシェア型）
  - **Key finding:** 非西洋・低教育水準移民の増加 → 極右候補得票増。マグレブ系移民の流入が南仏・北仏ともに極右支持を押し上げ。極左への効果は非有意。高スキル・欧州系移民の効果は小。
  - **日本への含意・差異:** 日本では「非西洋・低スキル移民」に近いのが技能実習生（ベトナム・インドネシア等）。フランスのマグレブ系と異なり、日本では宗教的文化差は小さいが、「可視性」（見た目の差）は類似。1968年相当の歴史的移民居住データが日本では整備されていない可能性大（戦前の在日コリアン分布は代替候補）。

- **Dancygier (2010)** — *Immigration and Conflict in Europe*. Cambridge University Press.  
  [https://www.cambridge.org/core/books/immigration-and-conflict-in-europe/](https://www.cambridge.org/core/books/immigration-and-conflict-in-europe/)
  - **Setting:** イギリス・ドイツ・フランス / 移民-在来民・移民-国家間の衝突パターンの比較分析
  - **Identification:** 比較政治学的ケーススタディ（計量研究ではなく質的比較）
  - **Key finding:** 移民関連衝突の発生は「移民制度」と「地域労働市場・政治経済」の相互作用で決まる。経済的余裕のある都市部では衝突が少ない傾向。
  - **日本への含意・差異:** 外国人が特定地域に集中した場合の地域政治への影響を考える際の理論的枠組みとして有用。日本では外国人による「集団的政治行動」が抑制されており（投票権なし）、在来者側の反応が主要なアウトカムになる。

- **Dancygier (2017)** — *Dilemmas of Inclusion: Muslims in European Politics*. Princeton University Press.  
  [https://rdancygi.scholar.princeton.edu/books](https://rdancygi.scholar.princeton.edu/books)
  - **Setting:** オーストリア・ベルギー・ドイツ・イギリス / 数千の選挙コンテスト / イスラム系移民の政党内リクルート / 得票パターン
  - **Identification:** 回帰分析・比較事例分析（自然実験ではない）
  - **Key finding:** 政党がムスリム系ブロック票を急速に取り込もうとすると党内イデオロギー一貫性が損なわれ、クロスエスニック連合の構築に失敗しやすい。
  - **日本への含意・差異:** 日本では外国人の参政権がないため「ムスリム票」的ブロック票の形成自体が不可能。しかし帰化した外国人（在日コリアン等）の投票行動パターン研究には有用な枠組みを提供。

---

## D. イギリス

- **Becker & Fetzer (2016)** — "Does Migration Cause Extreme Voting?" CAGE Working Paper 306, University of Warwick.  
  [https://warwick.ac.uk/fac/soc/economics/research/centres/cage/publications/workingpapers/2016/does_migration_cause_extreme_voting/](https://warwick.ac.uk/fac/soc/economics/research/centres/cage/publications/workingpapers/2016/does_migration_cause_extreme_voting/)
  - **Setting:** イギリス全地方自治体 / 2004年EU拡大後の東欧移民流入 / UKIP欧州議会選挙得票率
  - **Identification:** EU拡大（2004年）という外生的ショック × イギリスが一時移動制限を課さなかった政策決定を自然実験として利用
  - **Key finding:** 東欧移民流入の多い地区でUKIP得票率が小幅だが有意に増加。低スキル労働市場への圧力と公的サービスへの競合がチャンネル。ただし効果量は小さく、Brexit結果を単独では説明できない。
  - **日本への含意・差異:** 日本での「外国人労働者解禁（2019年特定技能）」後の地方選挙への影響を分析する際の設計の参考になる。ただし日本には英国相当の「反移民政党」がまだ国政レベルで存在しない（参政党・日本第一党は小規模）。

- **Becker, Fetzer & Novy (2017)** — "Who Voted for Brexit? A Comprehensive District-Level Analysis." *Economic Policy*, 32(92): 601–650. DOI: 10.1093/economicpolicy/eiw017  
  [https://academic.oup.com/economicpolicy/article-abstract/32/92/601/4459491](https://academic.oup.com/economicpolicy/article-abstract/32/92/601/4459491)
  - **Setting:** イギリス380地方自治体 / 2016年Brexitレファレンダム / 移民・貿易・緊縮財政・教育・雇用
  - **Identification:** OLS多変量回帰 + 集計データと個票データの統合分析
  - **Key finding:** 教育水準・製造業依存・低所得・失業率がLeave投票の主因。移民・貿易露出だけでは変動の50%以下しか説明できない。東欧移民流入とUKIP支持には有意な相関。
  - **日本への含意・差異:** 移民だけでなく「地域の経済構造」が政治態度を決める複合要因分析の設計として参考。日本でも農村部・製造業依存地域と外国人受け入れ後の政治態度変化の関係を同時分析するモデルに応用可能。

- **Colantone & Stanig (2018a)** — "Global Competition and Brexit." *American Political Science Review*, 112(2): 201–218.  
  [https://www.cambridge.org/core/journals/american-political-science-review/article/abs/global-competition-and-brexit/](https://www.cambridge.org/core/journals/american-political-science-review/article/abs/global-competition-and-brexit/)
  - **Setting:** イギリス全地域 / 英国選挙研究 / 中国輸入ショック × 地域 / Brexit投票
  - **Identification:** 米国への中国輸入を道具変数とするCard型IV（中国輸入が労働市場を通じて政治態度に影響）
  - **Key finding:** 中国輸入ショックで打撃を受けた地域ほどLeave投票割合が高い。興味深いことに、**移民ストック・フローはLeave投票と直接相関せず**、中国輸入ショックが移民への態度を悪化させる間接効果（社会心理的経路）を示唆。
  - **日本への含意・差異:** 日本でも中国からの輸入圧力と地域の政治的右傾化の関係を検討できる。外国人嫌悪と通商問題の混合効果を識別する設計の手本。

- **Fetzer (2019)** — "Did Austerity Cause Brexit?" *American Economic Review*, 109(11): 3849–3886. DOI: 10.1257/aer.20181164  
  [https://www.aeaweb.org/articles?id=10.1257/aer.20181164](https://www.aeaweb.org/articles?id=10.1257/aer.20181164)
  - **Setting:** イギリス全選挙区 / 2000–2016年全選挙コンテスト / 個票パネル / 福祉給付削減（緊縮財政）/ UKIP得票・Brexit投票
  - **Identification:** 地域・個人レベルの福祉改革への露出量の差異を利用したパネルFE + 個票内変動
  - **Key finding:** 2010年以降の緊縮財政 → UKIP得票増（3.5〜11.9pp）。Brexitへの支持は緊縮なければ少なくとも6pp低かった可能性。福祉削減が既存の経済的不満を「活性化」した。
  - **日本への含意・差異:** 日本では財政緊縮（消費増税等）と外国人をめぐる政治態度の連動を分析する可能性がある。ただし日本には英国相当のBrexit的「移民投票」イベントが存在しない。

- **Goodwin & Heath (2016)** — "The 2016 Referendum, Brexit and the Left Behind." *Political Quarterly*, 87(3): 323–332.  
  [https://www.astrid-online.it/static/upload/good/goodwin_heath_pq_3-2016.pdf](https://www.astrid-online.it/static/upload/good/goodwin_heath_pq_3-2016.pdf)
  - **Setting:** イギリス380地方自治体 / 2011年国勢調査 × Brexit投票 / 学歴・年齢・経済的剥奪
  - **Identification:** 集計回帰（記述・相関）
  - **Key finding:** 低学歴・高齢・貧困層・製造業依存地域でLeave投票が強く、「取り残された人々（left behind）」テーゼを確立。東欧移民流入地域もLeave傾向。
  - **日本への含意・差異:** 日本で外国人受け入れに反対する層が農村・中高年・低学歴に偏るかを確認するための仮説構築に参照可能。「取り残された日本」仮説の検証への足掛かり。

---

## E. アメリカ

- **Mayda, Peri & Steingress (2022)** — "The Political Impact of Immigration: Evidence from the United States." *American Economic Journal: Applied Economics*, 14(1): 358–389. DOI: 10.1257/app.20190081  
  [https://www.aeaweb.org/articles?id=10.1257/app.20190081](https://www.aeaweb.org/articles?id=10.1257/app.20190081)
  - **Setting:** アメリカ全郡 / 1990–2016年 / 郡別移民数（高スキル・低スキル別）/ 共和党得票率
  - **Identification:** 歴史的居住パターンに基づくシフトシェアIV（スキル別）
  - **Key finding:** 低スキル移民増加 → 共和党得票増（反移民側）。高スキル移民増加 → 民主党得票増。効果は移民の出身国・人種に依存せず、スキル水準によって符号が逆転する。
  - **日本への含意・差異:** 日本では高スキル移民（専門人材）と低スキル移民（技能実習生）の政治的効果が異なる可能性を示唆する重要先行研究。日本版の「スキル分割モデル」を実装する際の直接の参考。ただし日本には米国型の二大政党制がなく、「反移民政党への得票」として何を使うかが課題。

- **Tabellini (2020)** — "Gifts of the Immigrants, Woes of the Natives: Lessons from the Age of Mass Migration." *Review of Economic Studies*, 87(1): 454–486. DOI: 10.1093/restud/rdz027  
  [https://ideas.repec.org/a/oup/restud/v87y2020i1p454-486..html](https://ideas.repec.org/a/oup/restud/v87y2020i1p454-486..html)
  - **Setting:** アメリカ主要都市 / 1910–1930年（大量移民期）/ WWI・移民割当法による外生的変動 / 移民シェア / 反移民議員選出・再配分縮小
  - **Identification:** WWI・1920年代移民割当法による移民フローの外生的縮小 + 歴史的定住パターンIV
  - **Key finding:** 大量移民は経済的に在来者雇用を増加させたにもかかわらず、**文化的距離が大きい移民（非プロテスタント・非英語圏）**ほど政治的反発を誘発。保守的議員選出・再分配縮小につながった。
  - **日本への含意・差異:** 「文化的距離」が政治反発の鍵という発見は日本にも高い示唆。在日外国人との文化的距離指標の構築（言語・宗教・出身地域）とJa本の地方選挙データの照合が可能かもしれない。

- **Alesina & Tabellini (2024)** — "The Political Effects of Immigration: Culture or Economics?" *Journal of Economic Literature*, 62(1): 5–46. DOI: 10.1257/jel.20221643  
  [https://www.aeaweb.org/articles?id=10.1257/jel.20221643](https://www.aeaweb.org/articles?id=10.1257/jel.20221643)
  - **Setting:** アメリカ・欧州 / 1850–2020年（文献サーベイ）/ 移民の政治・社会効果の包括的レビュー
  - **Identification:** サーベイ論文（メタ分析的視点で経済・文化チャンネルを識別）
  - **Key finding:** 移民は「しばしば」反移民政党への支持増・再配分選好低下を招くが、常にではない。経済的チャンネルよりも**文化的・社会的懸念**（誤認知・メディア・接触条件）が重要。今後の研究課題として「接触の質」「メディア効果」の識別を挙げる。
  - **日本への含意・差異:** プロジェクト全体のフレームとして最も網羅的なレビュー。日本でも「経済 vs 文化」チャンネルの識別が核心的研究課題になることを示す。

---

## F. オーストラリア・カナダ

- **Gibson, McAllister & Swenson (2002)** — "The Politics of Race and Immigration in Australia: One Nation Voting in the 1998 Election." *Ethnic and Racial Studies*, 25(5): 823–844. DOI: 10.1080/0141987022000000286  
  [https://www.tandfonline.com/doi/abs/10.1080/0141987022000000286](https://www.tandfonline.com/doi/abs/10.1080/0141987022000000286)
  - **Setting:** オーストラリア148連邦選挙区 / 1998年連邦・クイーンズランド州選挙 / One Nation得票率 / 人口・経済・態度データ
  - **Identification:** 多水準分析（サーベイ個票 + 選挙区集計データ）
  - **Key finding:** **人種・移民問題がOne Nation支持の主要動因**であり、経済的不安は副次的。農村部・男性・低スキル労働者・銃所持者で支持が高い。欧州の極右政党の台頭との構造的類似を確認。
  - **日本への含意・差異:** 日本では参政党・日本第一党がOne Nationに最も近い機能的アナログ。ただし国政での影響力は格段に小さい。文化的脅威 vs 経済的脅威の識別アプローチは日本の態度調査設計に直接応用可能。

- **Kage, Rosenbluth & Tanaka (2022)** — "Varieties of Public Attitudes toward Immigration: Evidence from Survey Experiments in Japan." *Political Research Quarterly*, 75(4): 1116–1131. DOI: 10.1177/1065912921993552  
  [https://journals.sagepub.com/doi/10.1177/1065912921993552](https://journals.sagepub.com/doi/10.1177/1065912921993552)
  - **Setting:** 日本 / 大規模サーベイ実験 / 移民属性コンジョイント実験 / 移民受け入れ選好
  - **Identification:** ランダム化されたコンジョイント実験（属性操作）
  - **Key finding:** 高スキル（医師・ITエンジニア）・日本語堪能な移民への選好が著しく高い。出身国では米独 > ベトナム・インド > 中国。経済貢献の情報提供で受け入れ賛成が増加。宗教・犯罪情報で反対が増加。
  - **日本への含意・差異:** **本プロジェクトの日本データ分析の直接的補完論文**。集合レベルの選挙分析との対比（個人態度 vs 集計結果）の解釈に必要。ただし因果識別は困難で、実際の選挙結果との連結が今後の課題。

---

## G. ギリシャ

- **Dinas, Matakos, Xefteris & Hangartner (2019)** — "Waking Up the Golden Dawn: Does Exposure to the Refugee Crisis Increase Support for Extreme-Right Parties?" *Political Analysis*, 27(2): 244–254. DOI: 10.1017/pan.2018.48  
  [https://www.cambridge.org/core/journals/political-analysis/article/waking-up-the-golden-dawn/](https://www.cambridge.org/core/journals/political-analysis/article/waking-up-the-golden-dawn/C50A127CC517968F2D0FA42A2A23FF85)
  - **Setting:** ギリシャ・エーゲ海諸島 / 2015年9月選挙 / トルコ近傍vs遠方島嶼の難民到達量の差 / 黄金の夜明け（GD）得票率
  - **Identification:** 地理的近接性（トルコとの距離）による**自然実験** — 難民がランダムではなく地理的に決まる流入量の差異を利用
  - **Key finding:** 難民流入の突然増加 → GD得票率約2pp増（平均から44%増）。ただし難民は島から本土へすぐに移動するため接触理論は適用しにくく、露出・脅威感覚が主因。
  - **日本への含意・差異:** 地理的距離をIV代替として使うアプローチは、日本でも「港湾都市・観光地への訪日外国人急増」のような突然の露出変化研究に応用できる。ただし日本での定住移民と通過難民では文脈が全く異なる。

---

## H. 難民分散配置型準実験（まとめ）

各国の難民分散政策は、移民の内生的立地選択を回避するための強力なIVを提供する。代表的事例を一覧する。

| 国 | 政策期間 | 制度概要 | 利用論文 |
|---|---|---|---|
| デンマーク | 1986–1999年 | 県・市への人口比割り当て | Dustmann et al. (2019), Harmon (2018) |
| スウェーデン | 1985–1994年 | 市町村への強制配置（3年定住義務） | Dahlberg et al. (2012) |
| スイス | 1998年– | 26カントンへのランダム行政割り当て | Martén et al. (2019), Bansak et al. (2018) |
| オーストリア | — | 難民通過地域 vs 収容地域の差異 | Steinmayr (2021) |
| ドイツ | 2014–2015 | 収容施設の空き物件次第での郡間配分 | Gehrsitz & Ungerer (2022) |
| ギリシャ | 2015年 | トルコとの地理的距離による自然実験 | Dinas et al. (2019) |

---

## I. クロスカントリー / 比較・理論

- **Margalit (2019)** — "Economic Insecurity and the Causes of Populism, Reconsidered." *Journal of Economic Perspectives*, 33(4): 152–170. DOI: 10.1257/jep.33.4.152  
  [https://www.aeaweb.org/articles?id=10.1257/jep.33.4.152](https://www.aeaweb.org/articles?id=10.1257/jep.33.4.152)
  - **Setting:** 欧米複数国 / レビュー・メタ分析
  - **Key finding:** ポピュリスト票の主因は「経済的不安」よりも**文化的不満（移民・人口構成変化）**。経済チャンネルの説明力は限定的。福祉拡充・再訓練プログラムは文化的不満を解消しない。
  - **日本への含意:** 経済的利害計算だけでなく、文化的アイデンティティ変化への脅威感を測定する調査設計の必要性を示す。

- **Inglehart & Norris (2016/2019)** — "Trump, Brexit, and the Rise of Populism: Economic Have-Nots and Cultural Backlash." HKS Working Paper RWP16-026 (2016); *Cultural Backlash: Trump, Brexit and Authoritarian Populism*. Cambridge University Press (2019).  
  [https://www.cambridge.org/core/books/cultural-backlash/](https://www.cambridge.org/core/books/cultural-backlash/3C7CB32722C7BB8B19A0FC005CAFD02B)
  - **Setting:** アメリカ・欧州30カ国以上 / 欧州社会調査 / 世代別価値観・権威主義スケール / ポピュリスト政党支持
  - **Key finding:** ポピュリスト票の背後には「静かな革命（進歩的価値観の世代間普及）」への**文化的反動**がある。高齢・低学歴・伝統的価値観層が権威主義的ポピュリストを支持。経済的貧困は条件付き要因に過ぎない。
  - **日本への含意・差異:** 日本でも高齢・保守的価値観層が外国人受け入れに反対する傾向（Kage et al. 2022と整合）。ただし日本には欧州型「権威主義的ポピュリスト政党」が定着していないため、党派的反移民動員の実証が困難。

- **Guriev & Papaioannou (2022)** — "The Political Economy of Populism." *Journal of Economic Literature*, 60(3): 753–832. DOI: 10.1257/jel.20201595  
  [https://www.aeaweb.org/articles?id=10.1257/jel.20201595](https://www.aeaweb.org/articles?id=10.1257/jel.20201595)
  - **Setting:** 全世界・1850年代以降 / 包括的文献サーベイ
  - **Key finding:** ポピュリズムの勃興は①グローバル化・自動化による長期経済変化、②2008–09年金融危機・緊縮財政、③文化的反動・信頼の低下、④移民・難民危機、⑤SNSの台頭の複合作用。移民と難民危機は経済・文化両チャンネルで機能。
  - **日本への含意:** ポピュリズムの多因子モデルを前提に、日本のケースで移民チャンネルが独自にどれだけ寄与するかを識別する必要性を示す。日本での④（移民・難民）の相対的重要性は欧州より小さい可能性。

---

## メソッド別比較表

| Paper | Country | Treatment | Outcome | ID Strategy | Effect Direction | Magnitude |
|---|---|---|---|---|---|---|
| Dustmann, Vasiljeva & Damm (2019) | Denmark | Refugee share (dispersal policy) | Anti-imm. party vote | Quasi-random dispersal IV | + (rural), -(urban) | 1.23–1.98pp per 1pp refugee |
| Halla, Wagner & Zweimüller (2017) | Austria | Immigrant share in community | FPÖ vote share | Card-style shift-share IV | + | ~10% of regional variation |
| Barone et al. (2016) | Italy | Immigrant share | Centre-right coalition vote | Shift-share IV | + | 0.86pp per 1pp immigrant |
| Mayda, Peri & Steingress (2022) | USA | Immigration (high-/low-skill) | Republican vote share | Shift-share IV (skill-split) | Low-skill: +, High-skill: − | Significant |
| Becker & Fetzer (2016) | UK | Eastern European migration (A8) | UKIP vote | 2004 EU enlargement natural experiment | + (small) | Small but significant |
| Steinmayr (2021) | Austria | Refugee contact vs. exposure | FPÖ vote | Dispersal quasi-experiment | Contact: −, Exposure: + | −4pp (contact), +1.5pp (exposure) |
| Otto & Steinhardt (2014) | Germany (Hamburg) | Foreign share change | Far-right vote | Shift-share IV | + | Significant |
| Tabellini (2020) | USA (historical) | Immigrant inflow (WWI/quota shock) | Conservative legislators, redistribution | IV (WWI, quota laws, settlement patterns) | + (backlash) | Significant |
| Harmon (2018) | Denmark | Ethnic diversity | Anti-imm. party vote | Housing stock IV | + | Significant |
| Gehrsitz & Ungerer (2022) | Germany | Refugee assignment | Far-right vote | Accommodation scramble IV | + (macro), − (micro-contact) | Small |
| Edo et al. (2019) | France | Immigration (low-skill, non-Western) | Far-right presidential vote | Shift-share IV (1968 settlement) | + | Significant |
| Colantone & Stanig (2018a) | UK | Chinese import shock | Brexit Leave vote | Card IV (Chinese exports to US) | + | 4.5pp (most vs. least exposed) |
| Fetzer (2019) | UK | Austerity exposure | UKIP vote / Brexit Leave | Individual-level welfare reform variation | + | 3.5–11.9pp UKIP; ~6pp Brexit |
| Dinas et al. (2019) | Greece | Refugee arrivals (island proximity) | Golden Dawn vote | Geographic natural experiment | + | ~2pp (44% increase) |
| Folke (2014) | Sweden | Small party representation | Immigration policy | PR-RD design | + (stricter policy when immigration party gains seats) | Large effect on policy |
| Cantoni et al. (2020) | Germany | Historical Nazi vote (1933) | AfD vote 2017 | Persistence correlation (not causal) | + | 0.15sd per 1sd Nazi vote |
| Gibson et al. (2002) | Australia | Immigration sentiment | One Nation vote | Multilevel OLS | + (cultural threat) | Primary driver |
| Dahlberg et al. (2012) | Sweden | Refugee share (dispersal program) | Redistribution preferences | Dispersal quasi-random IV | − (less redistribution) | Significant (esp. wealthy) |

---

## 日本でも実装可能な ID Strategy ランキング（実現可能性順）

### Rank 1: シフトシェア (Bartik) IV — 歴史的定住パターン利用

**実現可能性: 中〜高**

在日外国人の国籍別・都道府県別人口データは法務省「在留外国人統計」で1990年代以降入手可能。これを「過去の居住シェア × 全国の国籍別流入フロー変化」で構成するシフトシェアIVは、Barone et al. (2016) やMayda et al. (2022) が使ったものと同型。市区町村レベルの選挙データ（総務省）と照合すれば、移民比率変化が選挙結果に与える効果の推定が可能。  
**日本固有の課題**: 技能実習生は企業・自治体の斡旋で特定地域に集中するため、IV外生性の条件（過去の居住パターンが現在の経済状況と無相関）が崩れうる。バリデーションとして複数年の先行トレンドテストが必須。

### Rank 2: 特定技能・技能実習制度の政策変化を利用した差分の差分 (DID)

**実現可能性: 中**

2019年の「特定技能1号・2号」新設は外国人受け入れ業種・地域に段階的に影響を与えた。特定業種・特定地域での外国人増加を「処置」とし、該当しない類似地域を「対照」とするDID設計が可能。選挙結果（市区町村議会、参院比例等）との照合が必要。  
**制約**: 2019年以降の選挙データが少なく（参院選2019・2022・衆院選2021・2024）、時系列の長さが制限される。特定技能による外国人増は地域によって大きく異なり「処置強度」のバリエーション確保が課題。

### Rank 3: 都市・農村間比較を利用したクロスセクション IV（Harmon型住宅ストック代替）

**実現可能性: 低〜中**

Harmon (2018) が使った住宅ストックIVの日本版として、外国人向け公営住宅・雇用促進住宅の整備状況、または工業団地・農業集落の集積を「過去のインフラストック」として使う方法。これにより外国人の内生的立地選択を部分的にコントロールできる。  
**制約**: 日本では「Gerdes & Wadensjo型の難民分散政策」が存在しないため、純粋な準ランダム割り当てIVは構築困難。代替として技能実習生の送り出し国と受け入れ機関のマッチングデータ（JITCO等）を利用する探索的設計も考えられるが、データアクセスに障壁がある。

---

## 本プロジェクトに最も近い5本（重み付け推薦）

| 優先度 | 論文 | 推薦理由 |
|---|---|---|
| ★★★★★ | **Dustmann, Vasiljeva & Damm (2019)** | 都市・農村の都市差異、難民分散IV、複数選挙サイクルという設計が日本の都道府県×市区町村パネルの参照モデルとして最も完成度が高い。デンマークも日本同様に難民認定数が少なく、「難民」ではなく「経済移民」が主流だった点でも類似性がある。 |
| ★★★★☆ | **Mayda, Peri & Steingress (2022)** | 日本でも高スキル（専門人材）vs 低スキル（技能実習生）の区別がある点でスキル分割モデルの直接応用先。シフトシェアIVの設計が比較的日本データで再現しやすい。 |
| ★★★★☆ | **Barone et al. (2016)** | シフトシェアIVのベンチマーク。市区町村レベルデータを使う設計で日本の市区町村選挙データとの対応が取りやすい。 |
| ★★★☆☆ | **Steinmayr (2021)** | 接触仮説 vs 露出効果の識別という視点は日本でも外国人集住地域での態度研究に応用可能。ただし難民ではなく「技能実習生」でアウトカムが得られるかが問題。 |
| ★★★☆☆ | **Kage, Rosenbluth & Tanaka (2022)** | 唯一の日本サーベイ実験。プロジェクトの日本分析（集合レベル）の態度メカニズム解釈に不可欠な補完論文。本プロジェクトの「アウトカム → 態度リンク」を補強する。 |

---

## 参考文献リスト（引用形式）

1. Alesina, A. & Tabellini, M. (2024). "The Political Effects of Immigration: Culture or Economics?" *Journal of Economic Literature*, 62(1), 5–46.
2. Barone, G., D'Ignazio, A., de Blasio, G. & Naticchioni, P. (2016). "Mr. Rossi, Mr. Hu and politics." *Journal of Public Economics*, 136, 1–13.
3. Becker, S. O. & Fetzer, T. (2016). "Does Migration Cause Extreme Voting?" CAGE Working Paper 306.
4. Becker, S. O., Fetzer, T. & Novy, D. (2017). "Who Voted for Brexit?" *Economic Policy*, 32(92), 601–650.
5. Cantoni, D., Hagemeister, F. & Westcott, M. (2020). "Persistence and Activation of Right-Wing Political Ideology." CEPR DP 143.
6. Colantone, I. & Stanig, P. (2018). "Global Competition and Brexit." *APSR*, 112(2), 201–218.
7. Dahlberg, M., Edmark, K. & Lundqvist, H. (2012). "Ethnic Diversity and Preferences for Redistribution." *JPE*, 120(1), 41–76.
8. Dancygier, R. (2010). *Immigration and Conflict in Europe*. Cambridge University Press.
9. Dancygier, R. (2017). *Dilemmas of Inclusion*. Princeton University Press.
10. Dinas, E., Matakos, K., Xefteris, D. & Hangartner, D. (2019). "Waking Up the Golden Dawn." *Political Analysis*, 27(2), 244–254.
11. Dustmann, C., Vasiljeva, K. & Damm, A. P. (2019). "Refugee Migration and Electoral Outcomes." *Review of Economic Studies*, 86(5), 2035–2091.
12. Edo, A., Giesing, Y., Öztunc, J. & Poutvaara, P. (2019). "Immigration and Electoral Support for the Far-Left and the Far-Right." *European Economic Review*, 115, 99–143.
13. Fetzer, T. (2019). "Did Austerity Cause Brexit?" *American Economic Review*, 109(11), 3849–3886.
14. Folke, O. (2014). "Shades of Brown and Green." *Journal of the European Economic Association*, 12(5), 1361–1395.
15. Gehrsitz, M. & Ungerer, M. (2022). "Jobs, Crime and Votes." *Economica*, 89(355), 592–626.
16. Gibson, R., McAllister, I. & Swenson, T. (2002). "The Politics of Race and Immigration in Australia." *Ethnic and Racial Studies*, 25(5), 823–844.
17. Goodwin, M. J. & Heath, O. (2016). "The 2016 Referendum, Brexit and the Left Behind." *Political Quarterly*, 87(3), 323–332.
18. Guriev, S. & Papaioannou, E. (2022). "The Political Economy of Populism." *Journal of Economic Literature*, 60(3), 753–832.
19. Halla, M., Wagner, A. F. & Zweimüller, J. (2017). "Immigration and Voting for the Far Right." *JEEA*, 15(6), 1341–1385.
20. Harmon, N. A. (2018). "Immigration, Ethnic Diversity, and Political Outcomes." *Scandinavian Journal of Economics*, 120(4), 1043–1074.
21. Inglehart, R. & Norris, P. (2016). "Trump, Brexit, and the Rise of Populism." HKS Working Paper RWP16-026.
22. Inglehart, R. & Norris, P. (2019). *Cultural Backlash*. Cambridge University Press.
23. Kage, R., Rosenbluth, F. & Tanaka, S. (2022). "Varieties of Public Attitudes toward Immigration." *Political Research Quarterly*, 75(4), 1116–1131.
24. Margalit, Y. (2019). "Economic Insecurity and the Causes of Populism, Reconsidered." *Journal of Economic Perspectives*, 33(4), 152–170.
25. Martén, L., Hainmueller, J. & Hangartner, D. (2019). "Ethnic Networks Can Foster the Economic Integration of Refugees." *PNAS*, 116(33), 16280–16285.
26. Mayda, A. M., Peri, G. & Steingress, W. (2022). "The Political Impact of Immigration." *AEJ: Applied Economics*, 14(1), 358–389.
27. Otto, A. H. & Steinhardt, M. F. (2014). "Immigration and Election Outcomes." *Regional Science and Urban Economics*, 45, 67–79.
28. Steinmayr, A. (2021). "Contact versus Exposure." *Review of Economics and Statistics*, 103(2), 310–327.
29. Tabellini, M. (2020). "Gifts of the Immigrants, Woes of the Natives." *Review of Economic Studies*, 87(1), 454–486.

---

*注: 「Gerdes & Wadensjo (2010) Denmark」「Akbaba & Kanas (2024) comparative」「Gennaro & Lecce (2024) France」はウェブ検索で確認できなかった。Gerdes & Wadensjoは関連するDamm & Rosholm (2010, *Review of Economics of the Household*)が機能的代替として参照可能。他2本は未確認のため本文には含めていない。*
