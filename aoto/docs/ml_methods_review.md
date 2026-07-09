# ML 手法レビュー: 移民・政治・選挙研究への応用

> **作成日:** 2026-05-13  
> **対象プロジェクト:** 「日本における外国人流入と選挙結果・政治態度」実証研究  
> **本ドキュメントの目的:** 採用候補 ML 手法を先行研究とともに整理し、分析パイプライン選択の根拠を提示する

---

## A. Causal ML for Treatment-Effect Estimation

### A-1. Double / Debiased Machine Learning (DML)

- **Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., & Robins, J. (2018)** — "Double/Debiased Machine Learning for Treatment and Structural Parameters". *The Econometrics Journal*, 21(1), C1–C68. [DOI: 10.1111/ectj.12097](https://academic.oup.com/ectj/article/21/1/C1/5056401) / [arXiv:1608.00060](https://arxiv.org/abs/1608.00060)
  - **Method:** Neyman 直交スコアとクロスフィッティングを組み合わせることで、高次元 ML（LASSO、Random Forest、Boosting 等）をニューサンス推定に使いながら、因果パラメータについて √N-一致・漸近正規な推定量を得る。
  - **Findings/Contribution:** 正則化バイアスと過学習が平均処置効果推定に与える "二重汚染" を除去する汎用フレームワークを確立した。DoubleML (Python/R) で実装済み。
  - **本プロジェクトへの応用可能性:** 都道府県 × 年のパネルで「在留外国人比率」を処置変数、「得票率変化」を結果変数とし、人口・経済・産業構造など多数の交絡変数を LASSO でコントロールしながら平均処置効果を推定できる。shift-share 操作変数との組み合わせ (Panel IV DML) も実行可能で、内生性に対処しつつ高次元制御変数を扱える点が日本の都道府県 × 在留資格 × 年データに適する。

- **Knaus, M. C. (2022)** — "Double Machine Learning Based Program Evaluation under Unconfoundedness". *Econometrics Journal*, 25(3), 602–627. [IZA DP 13051](https://www.iza.org/publications/dp/13051/)
  - **Method:** DML をプログラム評価に特化させ、平均効果・異質効果・最適処置ルール推定に拡張。
  - **Findings/Contribution:** スイスの積極的労働市場政策の包括評価に適用し、DML が実用的な政策分析ツールとして機能することを示した。
  - **本プロジェクトへの応用可能性:** 移民政策（特定在留資格の解禁・拡大）を「政策処置」、市区町村レベルの選挙結果を「結果」とした DML 評価のテンプレートとして参照できる。日本の市区町村レベル外国人登録データ × 統一地方選結果との接合が想定される。

- **Cockx, B., Lechner, M., & Bollens, J. (2020)** — "Priority to Unemployed Immigrants? A Causal Machine Learning Evaluation of Training in Belgium". *IZA Discussion Paper*. [IZA](https://www.iza.org/)
  - **Method:** 因果 ML（DML 系）を用いて移民向け職業訓練の効果を評価。
  - **Findings/Contribution:** 移民というサブグループに特化したプログラム評価に因果 ML が有効であることを示した。
  - **本プロジェクトへの応用可能性:** 移民属性（在留資格・国籍・定住年数）を共変量にした日本版ラボケースとして設計参考になる。

- **Ahrens, A. (2025)** — "An Introduction to Double/Debiased Machine Learning". *arXiv:2504.08324*. [arXiv](https://arxiv.org/pdf/2504.08324)
  - **Method:** DML の入門的解説論文。Stata/R/Python 実装と応用例を網羅。
  - **Findings/Contribution:** 実証研究者向けの DML 実装ガイドとして有用。
  - **本プロジェクトへの応用可能性:** チームの DML 実装の出発点として直接参照できる実践的リファレンス。

---

### A-2. Causal Forest / Generalized Random Forests (GRF)

- **Wager, S. & Athey, S. (2018)** — "Estimation and Inference of Heterogeneous Treatment Effects using Random Forests". *Journal of the American Statistical Association*, 113(523), 1228–1242. [arXiv:1510.04342](https://arxiv.org/abs/1510.04342)
  - **Method:** Random Forest を拡張し、条件付き平均処置効果 (CATE) を点ごとに漸近正規推定する Causal Forest を提案。「Honest」分割によりバイアスを制御。
  - **Findings/Contribution:** 最近傍マッチングより大幅に検出力が高く、不関連な共変量が多くても安定した CATE 推定が可能。`grf` パッケージ (R) として実装されている。
  - **本プロジェクトへの応用可能性:** 都道府県 × 在留資格 × 年のパネルで、「若年層比率が高い都市部 vs. 高齢農村部」「製造業集積地 vs. 農業地帯」など多次元の効果異質性を自動発見できる。処置効果の空間分布を地図化するのにも適しており、「どの種類の外国人流入がどの地域の選挙結果に効くか」の政策的含意を直接引き出せる。

- **Athey, S., Tibshirani, J., & Wager, S. (2019)** — "Generalized Random Forests". *Annals of Statistics*, 47(2), 1148–1178. [arXiv:1610.01271](https://arxiv.org/abs/1610.01271)
  - **Method:** Causal Forest を傾向スコア推定・量子処置効果・操作変数推定等に拡張した汎用フレームワーク GRF。
  - **Findings/Contribution:** `grf` パッケージとして実装済み。多様な因果推論設定に対応する統一的枠組みを提供した。
  - **本プロジェクトへの応用可能性:** IV-GRF を用いれば、在留外国人比率の内生性を操作変数で除去しつつ CATE を推定できる。Shift-share 操作変数（歴史的集積地 × 全国流入量）と組み合わせた Japan 版 CATE 推定が設計可能。

- **Zheng, L. & Yin, W. (2023)** — "Estimating and evaluating treatment effect heterogeneity: A causal forests approach". *Research & Politics*, 10(1). [DOI: 10.1177/20531680231153080](https://journals.sagepub.com/doi/10.1177/20531680231153080)
  - **Method:** 政治学の実証研究に Causal Forest を適用する実践ガイド。
  - **Findings/Contribution:** 政治学の既存研究を再分析し、従来手法では隠れていた HTE を発見。Causal Forest が政治学標準ツールとして機能することを示した。
  - **本プロジェクトへの応用可能性:** 政治学者向けのチュートリアルとして本プロジェクトの分析実装に直接活用できる。

---

### A-3. BART for Causal Inference

- **Hill, J. L. (2011)** — "Bayesian Nonparametric Modeling for Causal Inference". *Journal of Computational and Graphical Statistics*, 20(1), 217–240. [DOI: 10.1198/jcgs.2010.08162](https://www.tandfonline.com/doi/abs/10.1198/jcgs.2010.08162)
  - **Method:** BART（Bayesian Additive Regression Trees）で応答曲面を非パラメトリックモデリングし、個別処置効果 = E[Y(1)|X] - E[Y(0)|X] を直接推定する。
  - **Findings/Contribution:** 傾向スコアマッチング・重み付き推定・回帰調整より高精度な ATE 推定を実証。不確実性の定量化（事後分布）が自動的に得られる点が強み。
  - **本プロジェクトへの応用可能性:** 都道府県ごとの外国人比率と投票行動の非線形関係を柔軟に捉えられる。BART は交互作用・非線形性を自動考慮するため、移民流入の効果が特定の人口構造（高齢化率、持ち家率等）で逆転する可能性を検出できる。

- **Hahn, P. R., Murray, J. S., & Carvalho, C. M. (2020)** — "Bayesian Regression Tree Models for Causal Inference: Regularization, Confounding, and Heterogeneous Treatment Effects". *Bayesian Analysis*, 15(3). [DOI: 10.1214/19-BA1195](https://projecteuclid.org/journals/bayesian-analysis/volume-15/issue-3/Bayesian-Regression-Tree-Models-for-Causal-Inference--Regularization-Confounding/10.1214/19-BA1195.pdf)
  - **Method:** Bayesian Causal Forest (BCF)。応答曲面を予後関数 μ(x) + τ(x)·Z に分解し、処置効果関数 τ(x) を独立した BART で推定。傾向スコアを予後関数に取り込んで交絡を除去。
  - **Findings/Contribution:** ACIC 2016/2017 競技データで CATE 推定誤差最小を達成。強い交絡下での bias 低減と coverage 改善を実証した。
  - **本プロジェクトへの応用可能性:** 傾向スコア（外国人が流入しやすい都市特性）による強い交絡がある日本の都道府県データに BCF は特に有利。`bartCause` や `bcf` R パッケージで実装可能。

---

### A-4. TMLE

- **van der Laan, M. J. & Rose, S. (2011)** — "Targeted Learning: Causal Inference for Observational and Experimental Data". *Springer*. [springer.com](https://link.springer.com/)
  - **Method:** TMLE (Targeted Maximum Likelihood Estimation)。初期 ML 推定を二重ロバスト「ターゲティング」ステップで補正し、半パラメトリック効率を達成する。
  - **Findings/Contribution:** アウトカムモデルまたは処置モデルのどちらかが正しければ一致推定量（二重ロバスト）であることを示した。SuperLearner との組み合わせで実用的。
  - **本プロジェクトへの応用可能性:** Causal Forest や DML との比較・ロバストネスチェックとして使える。`tmle` / `tmle3` R パッケージで実装。計算量は中程度で、都道府県レベルデータなら現実的な計算時間に収まる。

---

## B. Heterogeneous Treatment Effects (HTE) for Political/Policy Contexts

- **Künzel, S. R., Sekhon, J. S., Bickel, P. J., & Yu, B. (2019)** — "Metalearners for Estimating Heterogeneous Treatment Effects using Machine Learning". *PNAS*, 116(10), 4156–4165. [DOI: 10.1073/pnas.1804597116](https://www.pnas.org/doi/10.1073/pnas.1804597116) / [arXiv:1706.03461](https://arxiv.org/abs/1706.03461)
  - **Method:** T-learner（処置群・対照群を別々に学習）、S-learner（処置インジケータを特徴量として統合）、X-learner（T-learner の残差を相互利用）の 3 メタラーナーを統一フレームワークで提示。
  - **Findings/Contribution:** 処置群・対照群のサンプルサイズ不均衡がある場合（観察研究で多い）に X-learner が優位。政治学の説得実験に適用し有効性を実証した。CausalML / EconML ライブラリで実装済み。
  - **本プロジェクトへの応用可能性:** 市区町村レベルで外国人比率が急増した地域（処置群）は少数であり、対照群（変化小）が多い典型的な不均衡設定。X-learner は T-learner より安定した CATE 推定を提供し、都市部 vs. 地方の効果差・在留資格ごとの効果差を分離できる。

- **Athey, S. & Imbens, G. (2017)** — "The State of Applied Econometrics: Causality and Policy Evaluation". *Journal of Economic Perspectives*, 31(2), 3–32. [NBER](https://www.nber.org/)
  - **Method:** 政策評価における因果推論手法の包括的サーベイ（RCT・IV・DiD・SC・ML）。
  - **Findings/Contribution:** Synthetic Control を「過去 15 年で最重要な政策評価のイノベーション」と評価。ML と因果推論の融合の方向性を示した。
  - **本プロジェクトへの応用可能性:** 本プロジェクトの手法選択の俯瞰的根拠として引用できる。

- **Rehill, P. (2025)** — "How Do Applied Researchers Use the Causal Forest? A Methodological Review". *International Statistical Review*. [DOI: 10.1111/insr.12610](https://onlinelibrary.wiley.com/doi/full/10.1111/insr.12610) / [arXiv:2404.13356](https://arxiv.org/html/2404.13356v2)
  - **Method:** 133 本の査読済論文で Causal Forest がどのように使われているかを体系的にレビュー。
  - **Findings/Contribution:** 社会科学での DiD + Causal Forest の組み合わせが増加傾向にあること、推定上の落とし穴と報告慣行を整理した。
  - **本プロジェクトへの応用可能性:** 選択した手法の正当性を裏付ける方法論的サーベイとして引用・参照できる。

---

## C. Synthetic Control + ML Extensions

- **Abadie, A., Diamond, A., & Hainmueller, J. (2010)** — "Synthetic Control Methods for Comparative Case Studies". *Journal of the American Statistical Association*, 105(490), 493–505. / **(2015)** "Comparative Politics and the Synthetic Control Method". *American Journal of Political Science*, 59(2), 495–510. [DOI: 10.1111/ajps.12116](https://onlinelibrary.wiley.com/doi/abs/10.1111/ajps.12116)
  - **Method:** 処置を受けた集計単位（都市・州・国）の反事実を対照群の加重平均（合成対照）で構築し、処置効果をプラセボ検定で推論する。
  - **Findings/Contribution:** 政治学・経済学での比較ケーススタディに広く適用。"最重要政策評価イノベーション" と評された（Athey & Imbens）。
  - **本プロジェクトへの応用可能性:** 特定の移民政策変更（e.g., 特定技能ビザ導入の 2019 年、技能実習制度改正）の前後で政治態度や得票率がどう変化したかを、制度変更のなかった都道府県群を合成対照として評価できる。都道府県数 N = 47 はこの手法に適切なサンプルサイズ。

- **Arkhangelsky, D., Athey, S., Hirshberg, D. A., Imbens, G. W., & Wager, S. (2021)** — "Synthetic Difference-in-Differences". *American Economic Review*, 111(12), 4088–4118. [DOI: 10.1257/aer.20190159](https://www.aeaweb.org/articles?id=10.1257%2Faer.20190159) / [arXiv:1812.09970](https://arxiv.org/abs/1812.09970)
  - **Method:** DiD の二元固定効果と Synthetic Control の最適重みを統合した SDID 推定量。並行トレンド仮定を大幅に緩和しつつ、DID より小さい標準誤差を達成する。
  - **Findings/Contribution:** SC より多くの処置単位に対応し、DiD より柔軟。双方向ロバスト性を持ち、理論的保証が強い。Stata `sdid` コマンドで実装済み。
  - **本プロジェクトへの応用可能性:** 複数都道府県が異なるタイミングで外国人急増を経験する "staggered adoption" 設定に対応可能。DiD より強い識別を保ちながら、合成対照の柔軟性も取り込めるため、移民流入と政治態度変容の分析に最適な手法の一つ。

- **Xu, Y. (2017)** — "Generalized Synthetic Control Method: Causal Inference with Interactive Fixed Effects Models". *Political Analysis*, 25(1), 57–76. [DOI: 10.1017/pan.2016.2](https://www.cambridge.org/core/journals/political-analysis/article/generalized-synthetic-control-method-causal-inference-with-interactive-fixed-effects-models/B63A8BD7C239DD4141C67DA10CD0E4F3) / [PDF](https://yiqingxu.org/papers/english/2016_Xu_gsynth/Xu_PA_2017.pdf)
  - **Method:** 処置単位の反事実を対照群の Interactive Fixed Effects (IFE) モデルで予測。EM アルゴリズムで潜在因子を推定し、複数処置単位・可変処置期間を扱える。
  - **Findings/Contribution:** *Political Analysis* 掲載で政治学研究者への普及が高く、`gsynth` R パッケージで実装済み。並行トレンド仮定を latent factor で代替する。
  - **本プロジェクトへの応用可能性:** 政治学のジャーナルに掲載された手法のため、本プロジェクトの政治学的貢献を主張しやすい。都道府県ごとに異なる時点で移民流入ショックを受ける状況に直接対応できる。

- **Doudchenko, N. & Imbens, G. W. (2016)** — "Balancing, Regression, Difference-In-Differences and Synthetic Control Methods: A Synthesis". *NBER Working Paper 22791*. [arXiv:1610.07748](https://arxiv.org/abs/1610.07748) / [NBER](https://www.nber.org/papers/w22791)
  - **Method:** SC 重みの非負制約・和制約を緩和し、Elastic Net 正則化で大規模対照群プールに対応した Penalized Synthetic Control 推定量を提案。
  - **Findings/Contribution:** DiD・SC・回帰を統一フレームワークで接続し、intercept shift も許容。多数の対照都市・都道府県があるケースで有効。
  - **本プロジェクトへの応用可能性:** 47 都道府県のうち多数を対照群として使い、penalized weights で最適な合成対照を構築できる。大都市圏と地方圏の移民流入パターンが大きく異なる Japan の構造に適する。

---

## D. Text-based ML for Political Analysis

- **Slapin, J. B. & Proksch, S.-O. (2008)** — "A Scaling Model for Estimating Time-Series Party Positions from Texts". *American Journal of Political Science*, 52(3), 705–722. [DOI: 10.1111/j.1540-5907.2008.00338.x](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-5907.2008.00338.x)
  - **Method:** Wordfish — Poisson ナイーブベイズ生成モデルに基づく教師なしテキストスケーリング。単語頻度から政党の潜在イデオロギー位置を推定する。
  - **Findings/Contribution:** ドイツ政党の 1990–2005 年マニフェストを用いて位置推定の時系列変化を可視化。人手によるコーダー不要で客観的位置推定が可能。
  - **本プロジェクトへの応用可能性:** 国会会議録（国会議事録 API）に Wordfish を適用し、移民関連発言における政党位置（移民容認—排斥 次元）を時系列で推定できる。移民流入時期との相関分析が可能。

- **Roberts, M. E., Stewart, B. M., Tingley, D., et al. (2014)** — "Structural Topic Models for Open-Ended Survey Responses". *American Journal of Political Science*, 58(4), 1064–1082. [DOI: 10.1111/ajps.12103](https://onlinelibrary.wiley.com/doi/10.1111/ajps.12103)
  - **Method:** STM (Structural Topic Model) — 文書レベルのメタデータ（政党、選挙区、時期等）をトピック出現率・内容に組み込んだ LDA 拡張。
  - **Findings/Contribution:** 開放型質問への回答を半自動分類し、実験的処置効果もトピック割合で推定できることを示した。`stm` R パッケージで実装済み。
  - **本プロジェクトへの応用可能性:** 国会発言・政党マニフェスト・メディア記事を STM で分析し、「移民」トピックのフレーミングが地域の外国人比率や選挙結果とどう関連するかを探索できる。共変量として在留外国人比率を組み込めるのが強み。

- **Lauderdale, B. E. & Herzog, A. (2016)** — "Measuring Political Positions from Legislative Speech". *Political Analysis*, 24(3), 374–394. [DOI: 10.1093/pan/mpw017](https://doi.org/10.1093/pan/mpw017)
  - **Method:** Wordshoal — Wordfish を議題（topic）ごとに分割推定し、個々の議題に依存しない通則的なイデオロギー位置を推定する二段階スケーリング。
  - **Findings/Contribution:** 単一議題への Wordfish 適用よりも安定した政治家位置推定を達成。
  - **本プロジェクトへの応用可能性:** 国会議事録（国会会議録検索システム API）を用いて衆参議員の移民政策スタンスを Wordshoal で推定し、外国人多住の選挙区出身議員ほど特定の発言パターンを持つか検証できる。東大政治学グループの既存研究（下記 Osaka et al.）との比較も有益。

- **Osaka, M., Oishi, T., & Shiratori, N. (2024)** — "Extracting Ideological Dimensions from Legislative Speeches in the Japanese Diet". *Social Science Japan Journal*, 29(1). [DOI: 10.1093/ssjj/jyag001](https://academic.oup.com/ssjj/article/29/1/jyag001/8507400)
  - **Method:** Wordshoal を国会会議録（1959–2019 年）に適用し、日本の政党イデオロギー位置を委員会発言ベースで推定。国会 API (`kaigiroku` R パッケージ) を活用。
  - **Findings/Contribution:** 日本の政党間対立を選挙外期間も含めて longitudinal に定量化した初の包括的研究。
  - **本プロジェクトへの応用可能性:** 本プロジェクトで国会発言を使う場合の先行研究として直接引用できる。同 API・方法論の踏台として活用し、移民関連サブコーパスへ分析を絞り込める。

- **KOKKAI DOC チーム (2025)** — "KOKKAI DOC: An LLM-Driven Framework for Scaling Parliamentary Representatives". *arXiv:2505.07118*. [arXiv](https://arxiv.org/html/2505.07118v1)
  - **Method:** LLM（GPT 系）で国会発言をノイズ除去・要約した後、政治的争点軸を自動抽出して政党位置を時系列スケーリングする 3 段階フレームワーク。
  - **Findings/Contribution:** 専門家評価との高相関を達成しつつ、手動ラベリング不要でスケーラブルな位置推定を実現した。
  - **本プロジェクトへの応用可能性:** 移民関連発言に LLM 要約を施してから Wordshoal/STM に投入する前処理パイプラインとして活用できる。日本語テキストの特殊性（改行・読点パターン）への対処が示されている点も重要。

---

## E. Spatial / Network ML for Political Diffusion

- **Bredtmann, J. (2022)** — "Immigration and Electoral Outcomes: Evidence from the 2015 Refugee Inflow to Germany". *Regional Science and Urban Economics*, 95. [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0166046222000473) / [IZA DP 15356](https://www.iza.org/publications/dp/15356/)
  - **Method:** 難民の行政割当（準ランダム）× 市区町村レベルパネルデータ。空間的スピルオーバーを隣接市区町村加重行列で捕捉し、右翼得票率への効果を DiD で推定。
  - **Findings/Contribution:** 難民 1% ポイント増で右翼政党得票率 +0.05% ポイント（小さいが有意）。集中収容施設の難民のみで効果が出現し、分散収容では効果なし。隣接市区町村スピルオーバーを考慮すると効果は拡大する。
  - **本プロジェクトへの応用可能性:** 日本版として、技能実習生の集住地域（浜松市・豊橋市等）周辺への空間的スピルオーバーを同様の Spatial DiD で検定できる。空間重み行列（隣接関係、距離逆数）の選択が推定結果に影響するため感度分析が必要。

- **Harmon, N. (2018)** — "After the Immigration Shock: The Causal Effect of Immigration on Electoral Preferences". *Electoral Studies*, 51, 86–97. [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S026137941630049X)
  - **Method:** ノルウェー市区町村レベルの移民人口データ（1977–2011）× 選挙結果を panel + DiD で分析。非西洋系移民流入を準ランダムと仮定し、進歩党（極右）得票への因果効果を推定。
  - **Findings/Contribution:** 非西洋系移民増は右翼政党支持を増加させるが効果は小さく、移民人口が一定規模に達すると効果は消える（接触仮説と整合）。
  - **本プロジェクトへの応用可能性:** 日本もノルウェーと同様に歴史的に均質な社会から移民急増期に入っており、初期の電撃効果（first arrival effect）の検証設計が直接参照できる。在日外国人比率が 0.5% 未満から急増した市区町村を「処置群」とする RD 設計にも転用可能。

- **Mehic, A. (2022)** — "Regional Aspects of Immigration-Related Changes in Political Preferences". *Journal of Regional Science*, 62(2). [DOI: 10.1111/jors.12608](https://onlinelibrary.wiley.com/doi/10.1111/jors.12608)
  - **Method:** ヨーロッパ地域パネルで移民流入と極右投票のリージョナル異質性を Spatial Panel モデルで分析。直接効果と空間間接効果（スピルオーバー）を分離。
  - **Findings/Contribution:** 移民の政治的効果は地域の経済状況・労働市場環境によって大きく異なり、空間的文脈が不可欠であることを示した。
  - **本プロジェクトへの応用可能性:** 都道府県 × 年パネルに空間自己回帰項を追加した SAR モデルを適用し、近隣県の外国人比率が本県の政治態度に与えるスピルオーバーを日本データで検証できる。

- **Maciag et al. (2025)** — "Spatial Spillover Effects on the Support for Populist Radical Right Parties in Slovakia". *Electoral Studies*, 94. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1757780225000885)
  - **Method:** スロバキア 79 地区 × 3 選挙サイクルの Spatial Panel で PRR 支持の直接効果・間接効果（スピルオーバー）を推定。Spatial Durbin Model を使用。
  - **Findings/Contribution:** PRR 支持のバリエーションは隣接地区の特性（人口移動・経済）からも有意に説明される。
  - **本プロジェクトへの応用可能性:** 日本版として Spatial Durbin Model を都道府県・市区町村データに適用するためのテンプレートとして参照できる。

---

## F. ML-based Prediction of Election Outcomes

- **Kage, R., Rosenbluth, F. M., & Tanaka, S. (2022)** — "Varieties of Public Attitudes toward Immigration: Evidence from Survey Experiments in Japan". *Political Research Quarterly*, 75(1), 216–230. [DOI: 10.1177/1065912921993552](https://journals.sagepub.com/doi/10.1177/1065912921993552)
  - **Method:** 日本国内のコンジョイント実験で移民属性（技能・国籍・言語能力等）を操作し、移民受け入れ態度の多次元構造を分析。
  - **Findings/Contribution:** 日本人の 60% 超が経済的または文化的理由で移民受け入れを支持。教育・職業・外国人との接触経験が態度の重要な決定因子。
  - **本プロジェクトへの応用可能性:** 地域レベルの移民流入データと個人レベルの態度データをリンクする分析で、本研究が示す「接触仮説」の地理的検証が可能。在留外国人比率が高い都道府県の回答者ほど受容的か、Causal Forest で検定できる。

- **Gallegos Torres, L. A. (2022)** — "The 2015 Refugee Inflow and Concerns over Immigration". *European Economic Review*, 147. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0176268022001264)
  - **Method:** 個人レベルパネルデータ (2012–2018) と地区レベルの難民流入データを結合し、移民懸念への因果効果を DiD で推定。
  - **Findings/Contribution:** 高移民流入地区では接触仮説に沿って移民懸念が 3% ポイント減少。ただし全体的なトレンドとしては懸念が 21% ポイント増加するパラドックスを示す。
  - **本プロジェクトへの応用可能性:** 個人レベルの態度変化 × 地域レベルの流入ショックを組み合わせたマルチレベル分析設計のモデルとなる。日本でも ISSP や NHK 世論調査の縦断データと外国人統計を接合する方向で応用可能。

- **Bredtmann, J. et al. (2023)** — "Becoming Neighbors with Refugees and Voting for the Far-Right? The Impact of Refugee Inflows at the Small-Scale Level". *Labour Economics*, 82. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0927537123001422)
  - **Method:** ハンブルク 1km × 1km グリッドレベルと郡レベルの二重スケール分析。空間近接性が右翼投票に与える効果を分離。
  - **Findings/Contribution:** 郡レベルでは右翼得票増、近隣グリッドでは有意でない（接触仮説の微細地理証拠）。
  - **本プロジェクトへの応用可能性:** 日本の市区町村レベル（NIED の外国人統計の最小単位）でも類似した二重スケール分析が設計できる可能性がある。

---

## 本プロジェクトで採用候補の ML パイプライン (Ranked Top 5)

---

### Pipeline 1 (最推奨): Causal Forest (GRF) + Shift-Share IV

| 項目 | 詳細 |
|---|---|
| **入力データ** | 都道府県 × 年パネル: 在留外国人数（在留資格別、法務省統計）、衆参選挙得票率（選管発表）、経済・人口共変量（国勢調査・国土数値情報）|
| **操作変数 (IV)** | 在留資格 × 国籍 × 都道府県の歴史的集積（Bartik shift-share） |
| **出力** | 都道府県 × 在留資格ごとの CATE（条件付き平均処置効果）と 95% CI |
| **Python ライブラリ** | `econml` (grf のラッパー含む), `grf` (R), `scikit-learn` |
| **計算量** | N = 47 都道府県 × 20–30 年 ≈ 1,000–1,500 観測。CPU のみで数分以内 |
| **採用すべき理由** | 都市部（製造業集積・技能実習）と農村部（高齢化・地域社会結束）で移民流入の政治効果が異なるという理論仮説を、交互作用の関数形を仮定せずに検定できる唯一の方法。政治学の主要ジャーナルで採用例が急増しており、査読通過の蓋然性も高い。 |

---

### Pipeline 2: Synthetic Difference-in-Differences (SDID)

| 項目 | 詳細 |
|---|---|
| **入力データ** | 都道府県 × 年パネル（同上）。処置: 特定政策変更（特定技能導入 2019 年等）の前後 |
| **出力** | ATT（処置を受けた都道府県の平均処置効果）と許容誤差 |
| **Python ライブラリ** | `sdid` (Stata), `synthdid` (R). Python では `pysynth` または手書き実装 |
| **計算量** | 軽量（数秒〜数分） |
| **採用すべき理由** | 並行トレンド仮定を最も緩やかに置きながら移民政策変更の因果効果を推定できる。47 都道府県という中規模パネルは SC 系手法に最適なサイズ。DiD では説明しにくい都道府県間の構造差を SDID は吸収できる。 |

---

### Pipeline 3: Double Machine Learning (DML / Panel IV)

| 項目 | 詳細 |
|---|---|
| **入力データ** | 市区町村レベル（全国約 1,700 市区町村）× 年パネル。在留外国人比率 + 40–60 個の交絡変数 |
| **出力** | ATE・LATE（局所平均処置効果）の √N-一致推定値と CI |
| **Python ライブラリ** | `doubleml` (Python/R), `econml`, `linearmodels` (Panel IV) |
| **計算量** | 市区町村レベルで N ≈ 30,000–50,000 観測。クロスフィット 5-fold で数十分 |
| **採用すべき理由** | 高次元の交絡変数（産業構造・労働市場・人口動態等）を LASSO/Random Forest で柔軟に制御しながら、移民流入の平均的因果効果を厳密に推定できる。市区町村レベルのサンプルサイズがあれば統計的検出力も十分。 |

---

### Pipeline 4: Structural Topic Model (STM) + Causal Analysis

| 項目 | 詳細 |
|---|---|
| **入力データ** | 国会会議録 API（1960–2024 年、委員会発言テキスト）× 在留外国人統計 × 都道府県選挙区情報 |
| **出力** | 移民関連トピックの出現割合時系列、政党・議員位置のスケール推定値 |
| **Python ライブラリ** | `stm` (R), `gensim` (Python LDA), `bertopic` (BERT ベース), `fugashi` (MeCab 形態素解析) |
| **計算量** | テキスト前処理（形態素解析）は時間がかかるが GPU 不要。STM 推定は数十分 |
| **採用すべき理由** | 移民流入が「選挙結果」だけでなく「政治的言説」をどう変容させるかを定量化できる。外国人比率を STM の共変量として組み込めば、移民多住地区の議員ほど受入賛成フレームを使うか直接検証できる。Panel A–C の計量分析を補完するテキスト分析として有効。 |

---

### Pipeline 5: Spatial Autoregressive Panel + Causal Forest

| 項目 | 詳細 |
|---|---|
| **入力データ** | 都道府県 × 年パネル + 隣接行列（Queen contiguity or 距離逆数）× CATE 推定値 (Pipeline 1 の出力) |
| **出力** | 直接効果 vs. 空間的スピルオーバー効果の分離。空間 CATE の可視化（choropleth map） |
| **Python ライブラリ** | `spreg` (PySAL), `libpysal`, `geopandas`, `pysal` |
| **計算量** | 軽量（分単位） |
| **採用すべき理由** | 都道府県をまたぐ「移民の政治的伝染効果」（隣県での外国人増加が本県の態度に波及するか）を検定できる。Bredtmann (2022) の Germany 研究や Mehic (2022) の欧州研究のジャパン版として、地理的コンテキストを明示的にモデルに取り込む点で発展的。 |

---

## 参考文献一覧 (URL 付き)

- Chernozhukov et al. (2018): https://academic.oup.com/ectj/article/21/1/C1/5056401 / https://arxiv.org/abs/1608.00060
- Wager & Athey (2018): https://arxiv.org/abs/1510.04342
- Athey, Tibshirani & Wager (2019): https://arxiv.org/abs/1610.01271
- Künzel et al. (2019): https://www.pnas.org/doi/10.1073/pnas.1804597116
- Hill (2011): https://www.tandfonline.com/doi/abs/10.1198/jcgs.2010.08162
- Hahn, Murray & Carvalho (2020): https://projecteuclid.org/journals/bayesian-analysis/volume-15/issue-3/Bayesian-Regression-Tree-Models-for-Causal-Inference--Regularization-Confounding/10.1214/19-BA1195.pdf
- Abadie, Diamond & Hainmueller (2010/2015): https://onlinelibrary.wiley.com/doi/abs/10.1111/ajps.12116
- Arkhangelsky et al. (2021): https://www.aeaweb.org/articles?id=10.1257%2Faer.20190159 / https://arxiv.org/abs/1812.09970
- Xu (2017): https://www.cambridge.org/core/journals/political-analysis/article/generalized-synthetic-control-method-causal-inference-with-interactive-fixed-effects-models/B63A8BD7C239DD4141C67DA10CD0E4F3
- Doudchenko & Imbens (2016): https://arxiv.org/abs/1610.07748
- Slapin & Proksch (2008): https://onlinelibrary.wiley.com/doi/10.1111/j.1540-5907.2008.00338.x
- Roberts et al. (2014): https://onlinelibrary.wiley.com/doi/10.1111/ajps.12103
- Lauderdale & Herzog (2016): https://doi.org/10.1093/pan/mpw017
- Osaka et al. (2024): https://academic.oup.com/ssjj/article/29/1/jyag001/8507400
- KOKKAI DOC (2025): https://arxiv.org/html/2505.07118v1
- Bredtmann (2022): https://www.sciencedirect.com/science/article/abs/pii/S0166046222000473
- Harmon (2018): https://www.sciencedirect.com/science/article/abs/pii/S026137941630049X
- Mehic (2022): https://onlinelibrary.wiley.com/doi/10.1111/jors.12608
- Kage, Rosenbluth & Tanaka (2022): https://journals.sagepub.com/doi/10.1177/1065912921993552
- Knaus (2022): https://www.iza.org/publications/dp/13051/
- Zheng & Yin (2023): https://journals.sagepub.com/doi/10.1177/20531680231153080
- Rehill (2025): https://onlinelibrary.wiley.com/doi/full/10.1111/insr.12610
