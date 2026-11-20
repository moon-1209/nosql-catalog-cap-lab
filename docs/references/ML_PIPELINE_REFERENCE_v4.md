# Data Mining & Machine Learning Pipeline Reference (v4.0)

- **Motivation/Background**: The transition from pure Deep Learning and classical Machine Learning coursework to comprehensive Data Mining requires expanding the modeling pipeline with explicit, rigorous emphasis on Business Understanding, Data Collection/Acquisition, Data Governance, Multi-Source Integration, Frequent Pattern Mining, and Operational Deployment.
- **Purpose**: Provide the authoritative, end-to-end engineering reference guide for Data Mining and Machine Learning workflows, uniting CRISP-DM and KDD methodologies with modern statistical validation, reproducible pipeline design, and strict leakage prevention.
- **Overview Pipeline**: Synthesizes the 6 CRISP-DM stages (Business Understanding → Data Understanding/Collection → Data Preparation → Modeling/Mining → Evaluation → Deployment) with the 5 KDD iterative phases, statistical rigor, and Python production engineering patterns.
- **Detailed Plan**: §0 CRISP-DM & KDD Architectural Framework; §1 Business Understanding & Problem Formulation; §2 Data Understanding, Acquisition & Collection Strategies; §3 Data Lineage, Governance & Immutable Raw Ingestion; §4 Data Quality Auditing & Profiling (6 Dimensions); §5 Multi-Source Data Integration & Entity Resolution; §6 Exploratory Data Analysis & Geometric Survey (EDA); §7 Missing Value Imputation; §8 Outlier Detection & Anomaly Mining; §9 Feature Scaling & Normalization; §10 Categorical Encoding & Dimensionality Management; §11 Class Imbalance & Cost-Sensitive Learning; §12 Feature Engineering & Dimensionality Reduction; §13 Data Partitioning & The Leakage Boundary; §14 Baseline Thinking & Benchmark Formulation; §15 Core Mining Paradigms (Association Rules, Clustering, Classification/Regression); §16 Model Selection, Inductive Bias & No Free Lunch; §17 Bias-Variance Tradeoff; §18 Hyperparameter Optimization; §19 Evaluation Metrics (Technical & Business ROI); §20 Cross-Validation Strategies; §21 Scientific Experimentation (Single-Variable Principle); §22 Statistical Significance Testing; §23 Error Analysis & Residual Diagnostics (5W Framework); §24 Model Interpretability & Explainable AI (SHAP/LIME); §25 Business Evaluation & Knowledge Validation; §26 Deployment, Actionability & Operational Monitoring; §27 Data Mining vs ML vs DL Comparative Matrix; §28 Practical End-to-End API Patterns.
- **References**: [agents/rules/AGENT_AI.md](../../agents/rules/AGENT_AI.md), [agents/rules/MD_CONVENTION.md](../../agents/rules/MD_CONVENTION.md), [agents/rules/LOGGING_CHECKPOINT_RULES.md](../../agents/rules/LOGGING_CHECKPOINT_RULES.md), [agents/rules/NAMING_CONVENTION.md](../../agents/rules/NAMING_CONVENTION.md), [agents/rules/RESULTS_REPORTING.md](../../agents/rules/RESULTS_REPORTING.md), [docs/references/ML_PIPELINE_REFERENCE_v3.md](ML_PIPELINE_REFERENCE_v3.md).
- **Created**: 2026-09-30T11:53:48+07:00
- **Last Updated**: 2026-09-30T11:53:48+07:00

[STATUS: ACTIVE]

| Field                   | Value                                                                                                                           |
| :---------------------- | :------------------------------------------------------------------------------------------------------------------------------ |
| **Document Type** | Comprehensive Data Mining & ML Engineering Reference Guide                                                                      |
| **Status**        | Canonical Active Reference (v4.0)                                                                                               |
| **Owner**         | Research Team, Human Practitioners & AI Coding Agents                                                                           |
| **Scope**         | End-to-End Data Mining, KDD, CRISP-DM & Machine Learning Lifecycle                                                              |
| **Created**       | 2026-09-30T11:53:48+07:00                                                                                                       |
| **Last Updated**  | 2026-09-30T11:53:48+07:00                                                                                                       |
| **Predecessor**   | [docs/references/ML_PIPELINE_REFERENCE_v3.md](ML_PIPELINE_REFERENCE_v3.md) (v3.0, Superseded)                                    |
| **References**    | [docs/README.md](../README.md), [docs/references/README.md](README.md), [agents/rules/AGENT_AI.md](../../agents/rules/AGENT_AI.md) |

---

## Table of Contents

- [0. The Overarching Paradigm: CRISP-DM, KDD, and ML](#0-the-overarching-paradigm-crisp-dm-kdd-and-ml)
  - [0.1 CRISP-DM Lifecycle](#01-crisp-dm-lifecycle)
  - [0.2 KDD (Knowledge Discovery in Databases) Process](#02-kdd-knowledge-discovery-in-databases-process)
  - [0.3 The Full Pipeline at a Glance](#03-the-full-pipeline-at-a-glance)
- [1. Business Understanding &amp; Problem Formulation](#1-business-understanding--problem-formulation)
  - [1.1 Determining Business Objectives &amp; Success Criteria](#11-determining-business-objectives--success-criteria)
  - [1.2 Assessing the Situation, Resources &amp; Operational Constraints](#12-assessing-the-situation-resources--operational-constraints)
  - [1.3 Error Cost Asymmetry &amp; The Cost-Benefit Matrix](#13-error-cost-asymmetry--the-cost-benefit-matrix)
  - [1.4 Translating Business Objectives to Data Mining Tasks](#14-translating-business-objectives-to-data-mining-tasks)
  - [1.5 Producing the Data Mining Project Charter](#15-producing-the-data-mining-project-charter)
- [2. Data Understanding, Acquisition &amp; Collection Strategies](#2-data-understanding-acquisition--collection-strategies)
  - [2.1 The Data Collection Imperative](#21-the-data-collection-imperative)
  - [2.2 Data Source Topologies](#22-data-source-topologies)
  - [2.3 Ingestion Protocols: Batch vs. Streaming vs. On-Demand Scraping](#23-ingestion-protocols-batch-vs-streaming-vs-on-demand-scraping)
  - [2.4 Web Crawling &amp; Scraping Standards](#24-web-crawling--scraping-standards)
  - [2.5 API Harvesting &amp; Rate-Limit Management](#25-api-harvesting--rate-limit-management)
- [3. Data Lineage, Governance &amp; Immutable Raw Ingestion](#3-data-lineage-governance--immutable-raw-ingestion)
  - [3.1 Rule #0: Immutable Raw Zone](#31-rule-0-immutable-raw-zone)
  - [3.2 Data Provenance, Manifests &amp; Cryptographic Hashing](#32-data-provenance-manifests--cryptographic-hashing)
  - [3.3 Legal, Ethical &amp; Privacy Governance (PII, GDPR, Anonymization)](#33-legal-ethical--privacy-governance-pii-gdpr-anonymization)
- [4. Data Quality Auditing &amp; Profiling (The 6 Dimensions)](#4-data-quality-auditing--profiling-the-6-dimensions)
  - [4.1 The Six Pillars of Data Quality](#41-the-six-pillars-of-data-quality)
  - [4.2 Measurement Scales &amp; Attribute Typologies](#42-measurement-scales--attribute-typologies)
  - [4.3 Data Structures in Mining](#43-data-structures-in-mining)
  - [4.4 Constructing the Data Catalog / Data Dictionary](#44-constructing-the-data-catalog--data-dictionary)
- [5. Multi-Source Data Integration &amp; Entity Resolution](#5-multi-source-data-integration--entity-resolution)
  - [5.1 Heterogeneous Schema Integration](#51-heterogeneous-schema-integration)
  - [5.2 Entity Resolution, Deduplication &amp; Record Linkage](#52-entity-resolution-deduplication--record-linkage)
  - [5.3 Resolving Semantic &amp; Numerical Data Value Conflicts](#53-resolving-semantic--numerical-data-value-conflicts)
  - [5.4 Redundancy &amp; Independence Analysis](#54-redundancy--independence-analysis)
- [6. Exploratory Data Analysis &amp; Geometric Survey (EDA)](#6-exploratory-data-analysis--geometric-survey-eda)
  - [6.1 The Three Lenses of EDA](#61-the-three-lenses-of-eda)
  - [6.2 Univariate Distribution &amp; Normality Diagnostics](#62-univariate-distribution--normality-diagnostics)
  - [6.3 Bivariate &amp; Multivariate Interaction Analysis](#63-bivariate--multivariate-interaction-analysis)
  - [6.4 How Data Geometry Governs Downstream Pipelines](#64-how-data-geometry-governs-downstream-pipelines)
- [7. Missing Values: Mechanisms &amp; Imputation](#7-missing-values-mechanisms--imputation)
  - [7.1 Mechanisms: MCAR, MAR, and MNAR](#71-mechanisms-mcar-mar-and-mnar)
  - [7.2 Numerical Imputation Strategies](#72-numerical-imputation-strategies)
  - [7.3 Categorical Imputation Strategies](#73-categorical-imputation-strategies)
  - [7.4 Missingness as Informative Signal](#74-missingness-as-informative-signal)
  - [7.5 Imputation Selection Decision Tree](#75-imputation-selection-decision-tree)
- [8. Outlier Detection &amp; Anomaly Mining](#8-outlier-detection--anomaly-mining)
  - [8.1 Outlier Taxonomy: Noise vs. High-Value Signal](#81-outlier-taxonomy-noise-vs-high-value-signal)
  - [8.2 Statistical Outlier Detection (IQR, Z-Score, Grubbs)](#82-statistical-outlier-detection-iqr-z-score-grubbs)
  - [8.3 Distance &amp; Proximity-Based Detection (k-NN)](#83-distance--proximity-based-detection-k-nn)
  - [8.4 Density-Based Detection (Local Outlier Factor - LOF)](#84-density-based-detection-local-outlier-factor---lof)
  - [8.5 Isolation-Based Detection (Isolation Forest)](#85-isolation-based-detection-isolation-forest)
  - [8.6 Outlier Treatment Strategies &amp; Non-Linear Transformations](#86-outlier-treatment-strategies--non-linear-transformations)
- [9. Feature Scaling &amp; Normalization](#9-feature-scaling--normalization)
  - [9.1 Geometric Necessity of Scaling](#91-geometric-necessity-of-scaling)
  - [9.2 Algorithm Sensitivity Matrix](#92-algorithm-sensitivity-matrix)
  - [9.3 Scaling Formulations (Standard, MinMax, Robust, Quantile)](#93-scaling-formulations-standard-minmax-robust-quantile)
  - [9.4 Scaling Selection Decision Tree](#94-scaling-selection-decision-tree)
- [10. Categorical Encoding &amp; Dimensionality Management](#10-categorical-encoding--dimensionality-management)
  - [10.1 Encoding as Metric Space Construction](#101-encoding-as-metric-space-construction)
  - [10.2 Ordinal &amp; Label Encoding](#102-ordinal--label-encoding)
  - [10.3 One-Hot Encoding &amp; Dummy Variable Trap](#103-one-hot-encoding--dummy-variable-trap)
  - [10.4 High-Cardinality Encodings (Frequency, Target, Weight of Evidence)](#104-high-cardinality-encodings-frequency-target-weight-of-evidence)
  - [10.5 Curse of Dimensionality in Data Mining](#105-curse-of-dimensionality-in-data-mining)
  - [10.6 Encoding Selection Decision Tree](#106-encoding-selection-decision-tree)
- [11. Class Imbalance &amp; Cost-Sensitive Learning](#11-class-imbalance--cost-sensitive-learning)
  - [11.1 The Base Rate Fallacy &amp; The Accuracy Paradox](#111-the-base-rate-fallacy--the-accuracy-paradox)
  - [11.2 Resampling Paradigms: Random, SMOTE, Borderline-SMOTE, Tomek](#112-resampling-paradigms-random-smote-borderline-smote-tomek)
  - [11.3 Cost-Sensitive Learning &amp; Loss Weighting](#113-cost-sensitive-learning--loss-weighting)
  - [11.4 Threshold Moving via Cost Matrix Optimization](#114-threshold-moving-via-cost-matrix-optimization)
- [12. Feature Engineering, Selection &amp; Reduction](#12-feature-engineering-selection--reduction)
  - [12.1 Domain-Driven Feature Construction](#121-domain-driven-feature-construction)
  - [12.2 Geometric Meaning of Feature Expansion](#122-geometric-meaning-of-feature-expansion)
  - [12.3 Feature Selection Triad (Filter, Wrapper, Embedded)](#123-feature-selection-triad-filter-wrapper-embedded)
  - [12.4 Unsupervised Dimensionality Reduction (PCA, SVD, t-SNE, UMAP)](#124-unsupervised-dimensionality-reduction-pca-svd-t-sne-umap)
  - [12.5 Numerosity Reduction &amp; Discretization (Equal-Width vs. Equal-Frequency)](#125-numerosity-reduction--discretization-equal-width-vs-equal-frequency)
- [13. Data Partitioning &amp; The Leakage Boundary](#13-data-partitioning--the-leakage-boundary)
  - [13.1 The Golden Leakage Boundary](#131-the-golden-leakage-boundary)
  - [13.2 Partitioning Schemes: Random, Stratified, Temporal, Group-Based](#132-partitioning-schemes-random-stratified-temporal-group-based)
  - [13.3 Implementation Invariant: `fit()` vs. `transform()`](#133-implementation-invariant-fit-vs-transform)
- [14. Baseline Thinking &amp; Benchmark Formulation](#14-baseline-thinking--benchmark-formulation)
  - [14.1 The Role of the Baseline in Scientific Discovery](#141-the-role-of-the-baseline-in-scientific-discovery)
  - [14.2 Trivial &amp; Empirical Baselines Across Mining Tasks](#142-trivial--empirical-baselines-across-mining-tasks)
  - [14.3 Minimum Viable Accuracy &amp; Cost-Benefit Thresholds](#143-minimum-viable-accuracy--cost-benefit-thresholds)
- [15. Core Mining &amp; Modeling Paradigms](#15-core-mining--modeling-paradigms)
  - [15.1 Frequent Pattern &amp; Association Rule Mining](#151-frequent-pattern--association-rule-mining)
    - [15.1.1 Market Basket Representation &amp; Core Metrics (Support, Confidence, Lift, Leverage, Conviction)](#1511-market-basket-representation--core-metrics-support-confidence-lift-leverage-conviction)
    - [15.1.2 The Apriori Principle &amp; Candidate Generation](#1512-the-apriori-principle--candidate-generation)
    - [15.1.3 FP-Growth &amp; FP-Tree Architecture](#1513-fp-growth--fp-tree-architecture)
    - [15.1.4 ECLAT &amp; Vertical Data Layout](#1514-eclat--vertical-data-layout)
    - [15.1.5 Actionable Rule Mining vs. Spurious Associations](#1515-actionable-rule-mining-vs-spurious-associations)
  - [15.2 Cluster Analysis &amp; Density Mining](#152-cluster-analysis--density-mining)
    - [15.2.1 Partitioning: K-Means &amp; K-Medoids (PAM)](#1521-partitioning-k-means--k-medoids-pam)
    - [15.2.2 Hierarchical: Agglomerative Linkage Criteria &amp; Dendrogram Analysis](#1522-hierarchical-agglomerative-linkage-criteria--dendrogram-analysis)
    - [15.2.3 Density-Based: DBSCAN, OPTICS &amp; HDBSCAN](#1523-density-based-dbscan-optics--hdbscan)
    - [15.2.4 Model-Based: Gaussian Mixture Models &amp; Expectation-Maximization](#1524-model-based-gaussian-mixture-models--expectation-maximization)
    - [15.2.5 Cluster Validation Metrics (Silhouette, Davies-Bouldin, Calinski-Harabasz, Dunn)](#1525-cluster-validation-metrics-silhouette-davies-bouldin-calinski-harabasz-dunn)
  - [15.3 Supervised Classification &amp; Regression](#153-supervised-classification--regression)
    - [15.3.1 Decision Trees (ID3, C4.5, CART: Entropy, Information Gain, Gini)](#1531-decision-trees-id3-c45-cart-entropy-information-gain-gini)
    - [15.3.2 Ensembles: Bagging, Random Forests, Gradient Boosting (XGBoost, LightGBM, CatBoost)](#1532-ensembles-bagging-random-forests-gradient-boosting-xgboost-lightgbm-catboost)
    - [15.3.3 Distance-Based: K-Nearest Neighbors (KNN)](#1533-distance-based-k-nearest-neighbors-knn)
    - [15.3.4 Probabilistic: Naive Bayes Classifiers &amp; Laplace Correction](#1534-probabilistic-naive-bayes-classifiers--laplace-correction)
    - [15.3.5 Maximum Margin: Support Vector Machines &amp; The Kernel Trick](#1535-maximum-margin-support-vector-machines--the-kernel-trick)
    - [15.3.6 Linear &amp; Logistic Models with Regularization](#1536-linear--logistic-models-with-regularization)
- [16. Model Selection, Inductive Bias &amp; No Free Lunch](#16-model-selection-inductive-bias--no-free-lunch)
  - [16.1 The No Free Lunch Theorem](#161-the-no-free-lunch-theorem)
  - [16.2 Inductive Bias: Matching Assumptions to Data Geometry](#162-inductive-bias-matching-assumptions-to-data-geometry)
  - [16.3 Systematic Model Selection Flowchart](#163-systematic-model-selection-flowchart)
- [17. Bias–Variance Tradeoff &amp; Regularization](#17-biasvariance-tradeoff--regularization)
  - [17.1 Mathematical Decomposition of Expected Generalization Error](#171-mathematical-decomposition-of-expected-generalization-error)
  - [17.2 Diagnostic Signatures: Learning Curves &amp; Error Gaps](#172-diagnostic-signatures-learning-curves--error-gaps)
  - [17.3 Regularization Mechanics: L1 (Lasso), L2 (Ridge), ElasticNet, Tree Pruning](#173-regularization-mechanics-l1-lasso-l2-ridge-elasticnet-tree-pruning)
- [18. Hyperparameter Optimization &amp; Tuning](#18-hyperparameter-optimization--tuning)
  - [18.1 Parameters vs. Hyperparameters](#181-parameters-vs-hyperparameters)
  - [18.2 Search Strategies: Grid, Random, Bayesian (Optuna TPE)](#182-search-strategies-grid-random-bayesian-optuna-tpe)
  - [18.3 Tuning Inside Cross-Validation Folds](#183-tuning-inside-cross-validation-folds)
- [19. Comprehensive Evaluation Metrics: Technical &amp; Business Impact](#19-comprehensive-evaluation-metrics-technical--business-impact)
  - [19.1 Supervised Classification Metrics](#191-supervised-classification-metrics)
  - [19.2 Supervised Regression Metrics](#192-supervised-regression-metrics)
  - [19.3 Association Mining Metrics](#193-association-mining-metrics)
  - [19.4 Clustering Metrics](#194-clustering-metrics)
  - [19.5 Translating Technical Metrics into Expected Monetary Value ($)](#195-translating-technical-metrics-into-expected-monetary-value-)
- [20. Cross-Validation &amp; Resampling Strategies](#20-cross-validation--resampling-strategies)
  - [20.1 K-Fold &amp; Stratified K-Fold](#201-k-fold--stratified-k-fold)
  - [20.2 Temporal Cross-Validation (Expanding &amp; Rolling Window)](#202-temporal-cross-validation-expanding--rolling-window)
  - [20.3 Group &amp; Entity Cross-Validation](#203-group--entity-cross-validation)
  - [20.4 Nested Cross-Validation (Unbiased Generalization Estimate)](#204-nested-cross-validation-unbiased-generalization-estimate)
- [21. Scientific Experimentation &amp; The Single-Variable Principle](#21-scientific-experimentation--the-single-variable-principle)
  - [21.1 The Single-Variable Isolation Principle](#211-the-single-variable-isolation-principle)
  - [21.2 Seed Control &amp; Multi-Run Stability](#212-seed-control--multi-run-stability)
  - [21.3 Experiment Logging &amp; Metadata Tracking](#213-experiment-logging--metadata-tracking)
- [22. Statistical Significance Testing &amp; Confidence Intervals](#22-statistical-significance-testing--confidence-intervals)
  - [22.1 Comparing Model Performance Beyond Mean Scores](#221-comparing-model-performance-beyond-mean-scores)
  - [22.2 Parametric vs. Non-Parametric Tests (Paired t-test, Wilcoxon, McNemar)](#222-parametric-vs-non-parametric-tests-paired-t-test-wilcoxon-mcnemar)
  - [22.3 Bootstrapped Confidence Intervals (95% CI)](#223-bootstrapped-confidence-intervals-95-ci)
- [23. Error Analysis &amp; Residual Diagnostics (The 5W Framework)](#23-error-analysis--residual-diagnostics-the-5w-framework)
  - [23.1 Subgroup Slicing &amp; Error Decomposition](#231-subgroup-slicing--error-decomposition)
  - [23.2 Residual Diagnostic Plots for Regression](#232-residual-diagnostic-plots-for-regression)
  - [23.3 The 5W Framework for Rigorous Metric Reporting](#233-the-5w-framework-for-rigorous-metric-reporting)
- [24. Model Interpretability &amp; Explainable AI](#24-model-interpretability--explainable-ai)
  - [24.1 Intrinsic vs. Post-Hoc Interpretability](#241-intrinsic-vs-post-hoc-interpretability)
  - [24.2 Global Interpretability: Permutation Importance &amp; PDP](#242-global-interpretability-permutation-importance--pdp)
  - [24.3 Local Interpretability: SHAP (Shapley Values) &amp; LIME](#243-local-interpretability-shap-shapley-values--lime)
- [25. Business Evaluation &amp; Knowledge Validation (CRISP-DM Phase 5)](#25-business-evaluation--knowledge-validation-crisp-dm-phase-5)
  - [25.1 Validating Findings Against Initial Business Criteria](#251-validating-findings-against-initial-business-criteria)
  - [25.2 The Actionability Filter: Novel, Non-Trivial, Actionable Knowledge](#252-the-actionability-filter-novel-non-trivial-actionable-knowledge)
  - [25.3 Go / No-Go Deployment Decision Gate](#253-go--no-go-deployment-decision-gate)
- [26. Deployment, Actionability &amp; Operational Monitoring (CRISP-DM Phase 6)](#26-deployment-actionability--operational-monitoring-crisp-dm-phase-6)
  - [26.1 Deployment Modalities: Batch, REST API, Embedded, BI Rule Engines](#261-deployment-modalities-batch-rest-api-embedded-bi-rule-engines)
  - [26.2 Continuous Monitoring: Data Drift vs. Concept Drift](#262-continuous-monitoring-data-drift-vs-concept-drift)
  - [26.3 Automated Retraining Loops &amp; Fail-Safe Fallbacks](#263-automated-retraining-loops--fail-safe-fallbacks)
- [27. Comparative Matrix: Data Mining vs. Machine Learning vs. Deep Learning](#27-comparative-matrix-data-mining-vs-machine-learning-vs-deep-learning)
- [28. Practical End-to-End API Patterns](#28-practical-end-to-end-api-patterns)
  - [28.1 Data Collection &amp; Raw Ingest with Hash Auditing](#281-data-collection--raw-ingest-with-hash-auditing)
  - [28.2 Data Quality Audit &amp; Schema Validation](#282-data-quality-audit--schema-validation)
  - [28.3 Leakage-Free Preprocessing Pipeline (`scikit-learn`)](#283-leakage-free-preprocessing-pipeline-scikit-learn)
  - [28.4 Association Rule Mining Pipeline (`mlxtend`)](#284-association-rule-mining-pipeline-mlxtend)
  - [28.5 Density &amp; Partitioning Clustering Pipeline](#285-density--partitioning-clustering-pipeline)
  - [28.6 Cost-Sensitive Classification with Nested CV &amp; SHAP](#286-cost-sensitive-classification-with-nested-cv--shap)

---

## 0. The Overarching Paradigm: CRISP-DM, KDD, and ML

In classical Machine Learning (ML) and Deep Learning (DL) courses, problems typically begin with a clean, pre-partitioned CSV file or a torchvision dataset. In contrast, **Data Mining** is an enterprise-wide, scientific journey that extracts non-trivial, implicit, previously unknown, and potentially actionable knowledge from messy, heterogeneous, multi-source enterprise data stores.

Two foundational industry and academic frameworks govern Data Mining:

### 0.1 CRISP-DM Lifecycle

The **CRoss-Industry Standard Process for Data Mining (CRISP-DM)** decomposes projects into six cyclical, highly iterative phases:

```text
       ┌────────────────────────────────────────────────────────┐
       │                 BUSINESS UNDERSTANDING                 │
       └───────────────────────────┬────────────────────────────┘
                                   │▲ (Refine Objectives)
                                   ▼│
       ┌────────────────────────────────────────────────────────┐
       │             DATA UNDERSTANDING & COLLECTION            │
       └───────────────────────────┬────────────────────────────┘
                                   │▲ (Data Gaps Identified)
                                   ▼│
       ┌────────────────────────────────────────────────────────┐
       │                    DATA PREPARATION                    │
       └───────────────────────────┬────────────────────────────┘
                                   │▲ (Feature Formatting Needs)
                                   ▼│
       ┌────────────────────────────────────────────────────────┐
       │                    MODELING & MINING                   │
       └───────────────────────────┬────────────────────────────┘
                                   │▲
                                   ▼│
       ┌────────────────────────────────────────────────────────┐
       │                       EVALUATION                       │
       └───────────────────────────┬────────────────────────────┘
                                   │▲ (Fail Business Gate -> Loop Back)
                                   ▼│
       ┌────────────────────────────────────────────────────────┐
       │                       DEPLOYMENT                       │
       └────────────────────────────────────────────────────────┘
```

> **Key Takeaway:** Notice the bidirectional arrows. Modeling is never a straight one-way path. Evaluating model errors regularly sends the engineer back to Data Preparation (to engineer missing signals) or back to Business Understanding (if the original framing was misaligned with operational constraints).

---

### 0.2 KDD (Knowledge Discovery in Databases) Process

The academic **KDD Process** outlines the data-to-knowledge transformation pipeline:

```text
Raw Data
   │
   ▼ [1. Selection]
Target Data
   │
   ▼ [2. Preprocessing / Cleaning]
Preprocessed Data
   │
   ▼ [3. Transformation / Reduction]
Transformed Data
   │
   ▼ [4. Data Mining / Pattern Extraction]
Patterns / Models
   │
   ▼ [5. Interpretation / Evaluation]
Actionable Knowledge
```

---

### 0.3 The Full Pipeline at a Glance

This reference integrates both CRISP-DM and KDD into an executable 26-stage engineering pipeline:

```text
 1. Business Understanding (KPIs, Feasibility, Cost-Matrix)
         ↓
 2. Data Collection & Acquisition (APIs, Scraping, SQL, Streams)
         ↓
 3. Lineage, Governance & Immutable Raw Ingestion (data/raw/)
         ↓
 4. Data Quality Auditing (6 Dimensions, Data Catalog)
         ↓
 5. Multi-Source Integration & Entity Resolution
         ↓
 6. Exploratory Data Analysis & Geometric Survey (EDA)
         ↓
 7. Missing Value Imputation
         ↓
 8. Outlier Detection & Anomaly Mining (LOF, iForest, IQR)
         ↓
 9. Feature Scaling & Normalization
         ↓
10. Categorical Encoding & Dimensionality Management
         ↓
11. Class Imbalance & Cost-Sensitive Resampling
         ↓
12. Feature Engineering & Reduction (Construction, Selection, PCA)
         ↓
13. Data Partitioning (Train / Val / Test)  ← GOLDEN LEAKAGE BOUNDARY
         ↓
14. Baseline Benchmark Formulation
         ↓
15. Core Mining & Modeling Execution:
    ├─► Association Rule Mining (Apriori, FP-Growth)
    ├─► Cluster Analysis (K-Means, DBSCAN, Hierarchical)
    └─► Supervised Models (Trees, Ensembles, KNN, Linear, SVM)
         ↓
16. Model Selection & Inductive Bias Matching
         ↓
17. Bias–Variance Analysis
         ↓
18. Hyperparameter Optimization (Optuna Bayesian TPE)
         ↓
19. Comprehensive Evaluation (Technical Metrics + Business ROI)
         ↓
20. Cross-Validation (Stratified, Group, Temporal)
         ↓
21. Scientific Experimentation (Single-Variable Principle)
         ↓
22. Statistical Significance Testing (p-values, Wilcoxon, Bootstrap CI)
         ↓
23. Error Analysis & Residual Diagnostics (5W Framework)
         ↓
24. Model Interpretability & Explainable AI (SHAP, LIME)
         ↓
25. Business Evaluation & Knowledge Validation (CRISP-DM Gate)
         ↓
26. Deployment, Operationalization & Drift Monitoring
```

> **The Constitutional Invariant:** Step 13 (Data Partitioning) creates an impenetrable leakage boundary. Preprocessing stages (§7–§12) are conceptually planned during initial data audits, but their **mathematical fitting** (`fit()`) must occur exclusively on the training partition. See [§13](#13-data-partitioning--the-leakage-boundary).

---

## 1. Business Understanding & Problem Formulation

> **Rule #0 of Engineering:** The most mathematically sophisticated algorithm solving the wrong business problem produces negative value. Always start from the business domain.

In a Data Mining context, projects are triggered by business friction, revenue opportunities, or operational bottlenecks—not by an urge to run XGBoost.

---

### 1.1 Determining Business Objectives & Success Criteria

1. **Understand Business Context:**
   - What organization or division is sponsoring this work?
   - What is the operational workflow today without data mining?
   - What specific business decision will change once this pipeline runs?
2. **Translate Business Goals to Concrete Success Criteria:**

| Business Objective        | Bad / Vague Metric   | Actionable Business Success Criteria                                    | Technical Data Mining Metric                |
| :------------------------ | :------------------- | :---------------------------------------------------------------------- | :------------------------------------------ |
| Reduce customer churn     | "Make churn low"     | Retain 15% of at-risk subscribers within a $50k intervention budget     | Top-decile Lift > 2.5; Precision@10% > 40%  |
| Retail Cross-Selling      | "Sell more items"    | Increase average basket value by $3.50 via checkout recommendations     | Association Rule Lift > 2.0; Support > 1.5% |
| Credit Default Risk       | "Predict bad loans"  | Reduce default losses by $1.2M while holding rejection rate < 8%        | Cost-weighted Recall > 85% at FPR < 5%      |
| Medical Anomaly Detection | "Find rare diseases" | Flag early-stage sepsis 4 hours before onset with < 5% false alarm rate | Sensitivity > 92% at Specificity > 95%      |

---

### 1.2 Assessing the Situation, Resources & Operational Constraints

Before acquiring data or writing code, audit the operational landscape:

- **Compute & Hardware Constraints:** Is inference performed on a server cluster, a mobile device, or an embedded edge controller? Does the model require GPU acceleration or must it run on CPU?
- **Latency & Throughput Requirements:**
  - Real-time online scoring (e.g., fraud scoring within 50ms of card swipe).
  - Near real-time micro-batch (e.g., scoring telemetry every 10 seconds).
  - Offline batch scoring (e.g., nightly churn risk calculation over 10M records).
- **Interpretability & Legal Compliance:**
  - Does the model make life-altering decisions (loans, hiring, medicine, criminal justice)?
  - If regulated under Fair Lending (ECOA/FCRA), GDPR (Right to Explanation), or HIPAA, a black-box neural network is legally non-viable without certified explainability proofs ([§24](#24-model-interpretability--explainable-ai)).

---

### 1.3 Error Cost Asymmetry & The Cost-Benefit Matrix

In textbooks, all errors are created equal. In real-world data mining, **false positives and false negatives carry drastically different financial and operational costs**.

```text
                  Actual Positive (Fraud / Disease)    Actual Negative (Legitimate / Healthy)
Predicted Pos     True Positive (TP)                   False Positive (FP)
                  Benefit: Caught fraud ($500 saved)   Cost: Annoyed customer, manual review ($15)
Predicted Neg     False Negative (FN)                  True Negative (TN)
                  Cost: Catastrophic loss ($500 lost)  Benefit: Smooth operation ($0)
```

The total expected operational cost is formalized as:

$$
\text{Expected Cost} = C_{\text{FP}} \cdot \text{FP} + C_{\text{FN}} \cdot \text{FN}
$$

If $C_{\text{FN}} \gg C_{\text{FP}}$, optimizing for raw accuracy produces a catastrophic business outcome. The data mining task must optimize **Expected Monetary Value (EMV)** or cost-weighted utility.

---

### 1.4 Translating Business Objectives to Data Mining Tasks

Every business problem maps onto one or more core data mining paradigms:

```text
Business Question
   │
   ├─► "Which customers belong to distinct behavioral groups?"
   │      └── Task: Clustering / Customer Segmentation (Unsupervised)
   │
   ├─► "Which products are frequently purchased together?"
   │      └── Task: Association Rule Mining / Market Basket Analysis (Unsupervised)
   │
   ├─► "Will this customer default or cancel their subscription?"
   │      └── Task: Binary Classification / Scoring (Supervised)
   │
   ├─► "What will warehouse demand be over the next quarter?"
   │      └── Task: Time Series Forecasting / Regression (Supervised)
   │
   └─► "Are there fraudulent transactions or anomalous equipment failures?"
          └── Task: Outlier / Anomaly Detection (Unsupervised or Semi-Supervised)
```

---

### 1.5 Producing the Data Mining Project Charter

Document the agreed project constraints in `docs/PURPOSE.md`:

1. Problem statement and business justification.
2. Target mining tasks and algorithm families under evaluation.
3. Quantifiable business success thresholds.
4. Resource boundaries (memory, compute, cloud budget).
5. Known regulatory, privacy, and explainability mandates.

---

## 2. Data Understanding, Acquisition & Collection Strategies

> In academic ML, data is handed to you on a silver platter. In real-world Data Mining, **data acquisition, ingestion, and verification account for 60% to 80% of project time**.

---

### 2.1 The Data Collection Imperative

Data does not exist as a single clean file. It is scattered across operational relational databases (OLTP), analytical warehouses (OLAP), third-party web APIs, streaming message queues, and public web pages.

A flawed data collection strategy poisons the entire project before modeling begins. If collection samples are biased, the model will learn sampling artifacts rather than underlying reality.

---

### 2.2 Data Source Topologies

| Data Source Category                   | Common Systems                           | Characteristics                                           | Primary Extraction Technique             |
| :------------------------------------- | :--------------------------------------- | :-------------------------------------------------------- | :--------------------------------------- |
| **Relational Databases (OLTP)**  | PostgreSQL, MySQL, SQL Server            | Normalized (3NF), ACID transactions, primary/foreign keys | SQL queries with indexed range filters   |
| **Analytical Lakehouses (OLAP)** | BigQuery, Snowflake, Databricks          | Columnar storage, de-normalized, petabyte scale           | Partitioned SQL, Parquet export          |
| **Semi-Structured / NoSQL**      | MongoDB, Elasticsearch, Redis            | Flexible schema, JSON documents, key-value stores         | Document queries, index searches         |
| **Web REST / GraphQL APIs**      | Stripe, Salesforce, OpenWeather, Twitter | Paginated JSON, rate-limited, authentication tokens       | HTTP client with exponential backoff     |
| **Web Crawling / Scraping**      | E-commerce sites, news portals           | Unstructured HTML, dynamically rendered JS                | BeautifulSoup, Scrapy, Playwright        |
| **Telemetry & IoT Streams**      | Apache Kafka, AWS Kinesis, MQTT          | High velocity, chronological event logs                   | Stream consumer, windowed micro-batches  |
| **Open Data Repositories**       | Kaggle, UCI ML Repository, Data.gov      | Static archival CSV/JSON, standardized benchmarks         | Direct HTTPS download, versioned caching |

---

### 2.3 Ingestion Protocols: Batch vs. Streaming vs. On-Demand Scraping

- **Batch Ingestion:** Scheduled extract-transform-load (ETL) jobs extracting data in periodic chunks (hourly, daily, weekly). Best for macro-level pattern mining and model training.
- **Streaming Ingestion:** Real-time ingestion of continuous event streams. Necessary for real-time anomaly detection and operational dashboards.
- **On-Demand Harvesting:** Automated web crawling and API scraping targeting ephemeral external data sources.

---

### 2.4 Web Crawling & Scraping Standards

When collecting data via web scraping (e.g. market competitor intelligence, sentiment analysis, product review harvesting):

1. **Verify Legal & Ethical Compliance:**
   - Inspect `robots.txt` (`https://domain.com/robots.txt`) before initiating crawlers. Respect `Disallow` directives and `Crawl-delay`.
   - Inspect Website Terms of Service (ToS) regarding commercial automated collection.
2. **Implement Polite Harvesting:**
   - Always supply an identifiable `User-Agent` header with contact information.
   - Insert randomized delays (`time.sleep(uniform(1.0, 3.0))`) between requests to avoid server denial of service.
   - Cache raw HTML responses locally so re-parsing does not repeatedly hit remote servers.
3. **Handle Dynamic DOMs Gracefully:**
   - Use fast static parsers (`BeautifulSoup`, `lxml`) for static HTML.
   - Use headless browser automation (`Playwright`, `Selenium`) only when client-side JavaScript rendering is strictly required.

---

### 2.5 API Harvesting & Rate-Limit Management

When consuming REST APIs:

- **Pagination Handling:** Never assume a single request returns the full dataset. Handle cursor-based (`after_token`), offset-based (`offset=100`), or page-based (`page=2`) pagination loops until exhausted.
- **Exponential Backoff with Jitter:** Handle HTTP 429 (Too Many Requests) and HTTP 503 (Service Unavailable) by exponentially increasing wait intervals with randomized jitter:

$$
t_{\text{wait}} = 2^{\text{attempt}} + \text{random\_uniform}(0, 1)
$$

---

## 3. Data Lineage, Governance & Immutable Raw Ingestion

---

### 3.1 Rule #0: Immutable Raw Zone

> **The Immutable Raw Invariant:** The raw data directory (`data/raw/`) is strictly **read-only**. Once raw data is fetched, written, or downloaded, it must never be modified, overwritten, or cleaned in-place.

All transformations, cleaning operations, and imputations must write exclusively to `data/interim/` or `data/processed/`. If raw data is mutated, experimental reproducibility is destroyed and debugging pipeline bugs becomes impossible.

---

### 3.2 Data Provenance, Manifests & Cryptographic Hashing

Every collected dataset artifact stored in `data/raw/` must be paired with an ingestion manifest (`manifest.json`):

```json
{
  "dataset_name": "ecommerce_customer_transactions",
  "raw_file": "data/raw/transactions_2026_09_30.csv",
  "source_uri": "https://api.internal.org/v1/extracts/transactions",
  "collected_at": "2026-09-30T11:53:48+07:00",
  "sha256_checksum": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "total_records": 154280,
  "collection_agent_version": "ingest_v4.2.0"
}
```

Computing a cryptographic hash (SHA-256) guarantees data integrity across development environments.

---

### 3.3 Legal, Ethical & Privacy Governance (PII, GDPR, Anonymization)

Collecting human data brings severe legal and moral liabilities:

1. **Personally Identifiable Information (PII) Scrubbing:**
   - Direct Identifiers (must be purged immediately upon ingestion): Full names, national ID / SSN, passport numbers, email addresses, phone numbers.
   - Quasi-Identifiers (can identify individuals when combined): Postal / ZIP code, date of birth, gender, job title.
2. **Anonymization & Pseudonymization Techniques:**
   - **Salted Hashing:** Replace customer IDs with a cryptographically salted hash (`SHA-256(user_id + secret_salt)`).
   - **$k$-Anonymity:** Ensure that for any combination of quasi-identifiers in the dataset, at least $k$ distinct records share those exact properties.
   - **Differential Privacy ($\epsilon$-DP):** Add controlled mathematical Laplacian or Gaussian noise to summary queries to prevent membership inference attacks.
3. **Ethical Sampling:** Audit collection protocols for geographic, demographic, or economic underrepresentation. A model trained on biased historical collection will perpetuate systematic exclusion in production.

---

## 4. Data Quality Auditing & Profiling (The 6 Dimensions)

Before transforming a single column, conduct a systematic quality audit across the six foundational dimensions of data health.

---

### 4.1 The Six Pillars of Data Quality

```text
┌─────────────────┬────────────────────────────────────────────────────────┐
│ Dimension       │ Audit Question & Verification Check                    │
├─────────────────┼────────────────────────────────────────────────────────┤
│ 1. Completeness │ Are values missing across rows or columns?             │
│                 │ -> Compute null percentage per feature. Check if null  │
│                 │    is structural (e.g. spouse_name for single person). │
├─────────────────┼────────────────────────────────────────────────────────┤
│ 2. Accuracy     │ Do recorded values conform to physical reality?       │
│                 │ -> Check bounds: Age < 0 or > 120; Negative prices.    │
├─────────────────┼────────────────────────────────────────────────────────┤
│ 3. Consistency  │ Do values contradict each other across tables/systems? │
│                 │ -> User marked "Status: Active" but has "Deactivated"  │
│                 │    timestamp in audit log.                             │
├─────────────────┼────────────────────────────────────────────────────────┤
│ 4. Timeliness   │ Is the data current, or has temporal drift occurred?   │
│                 │ -> Evaluate lag between event occurrence and logging.   │
├─────────────────┼────────────────────────────────────────────────────────┤
│ 5. Uniqueness   │ Are there duplicate entity records or ghost rows?     │
│                 │ -> Audit primary key uniqueness and fuzzy duplicates.  │
├─────────────────┼────────────────────────────────────────────────────────┤
│ 6. Validity     │ Do values conform to mandated syntax and regex rules?  │
│                 │ -> ISO 8601 timestamps, valid email patterns, regex.   │
└─────────────────┴────────────────────────────────────────────────────────┘
```

---

### 4.2 Measurement Scales & Attribute Typologies

Attribute transformations depend entirely on the measurement scale (Stevens' Typology):

- **Nominal (Categorical Unordered):** Categories with no inherent ranking (e.g., `Color: Red, Blue, Green`). Mathematical operations allowed: Equality (`=`), Mode. Mean and order are undefined.
- **Ordinal (Categorical Ordered):** Categories with a definitive, ranked sequence (e.g., `Education: HighSchool < Bachelor < Master < PhD`). Operations allowed: Greater/less than (`>`), Median, Percentiles. Subtraction is undefined.
- **Interval (Numerical with Arbitrary Zero):** Continuous scale where differences have meaning, but zero does not imply absence (e.g., Temperature in Celsius/Fahrenheit, Calendar Years). Operations allowed: Addition, Subtraction, Mean, Variance. Ratios are meaningless ($20^\circ\text{C}$ is not twice as hot as $10^\circ\text{C}$).
- **Ratio (Numerical with Absolute True Zero):** Continuous scale with a true physical zero representing absence (e.g., Revenue, Kelvin Temperature, Weight, Duration). All arithmetic operations allowed (Multiplication, Division, Geometric Mean).

---

### 4.3 Data Structures in Mining

Data mining processes diverse topological formats:

- **Tabular / Relational:** Fixed $N \times D$ matrices (samples $\times$ features).
- **Transactional (Market Basket):** Variable-length sets of discrete items per transaction ID (`T1: {Milk, Bread}, T2: {Diapers, Beer, Chips}`).
- **Sequence / Time Series:** Ordered sequences where chronological or grammatical order conveys semantic signal.
- **Graph & Network:** Nodes (entities) and edges (relationships), e.g., social graphs, citation networks, financial wire transfer routes.
- **Spatial / GIS:** Geocoded coordinates, polygons, and spatial distance topologies.

---

### 4.4 Constructing the Data Catalog / Data Dictionary

Document every dataset in a formal catalog (`docs/DATA_CATALOG.md`):

| Column Name            | Business Description           | Storage Type | Scale Typology | Allowable Range / Domain                       | Nullable?       | Primary/Foreign Key |
| :--------------------- | :----------------------------- | :----------- | :------------- | :--------------------------------------------- | :-------------- | :------------------ |
| `customer_id`        | Unique customer UUID           | String       | Nominal        | UUIDv4 string                                  | No              | Primary Key         |
| `account_age_months` | Months since account opening   | Int32        | Ratio          | $[0, 480]$                                   | No              | None                |
| `tier_level`         | Loyalty membership tier        | String       | Ordinal        | `Bronze`, `Silver`, `Gold`, `Platinum` | No              | None                |
| `last_login_utc`     | Timestamp of last user session | Timestamp    | Interval       | ISO 8601 UTC                                   | Yes (1.2% null) | None                |
| `monthly_spend_usd`  | Average monthly invoice spend  | Float64      | Ratio          | $[0.00, \infty)$                             | Yes (0.3% null) | None                |

---

## 5. Multi-Source Data Integration & Entity Resolution

In enterprise mining, data must be fused from disparate silos.

---

### 5.1 Heterogeneous Schema Integration

When merging data from multiple operational systems (e.g., online web store and in-person retail POS):

- **Attribute Name Discrepancies:** `client_id` vs. `customer_uuid` vs. `user_no`. Standardize on a canonical schema before concatenation.
- **Unit & Currency Mismatches:** System A logs revenue in USD; System B logs in EUR or VND. Harmonize to a single base currency using historical exchange rates matching transaction timestamps.
- **Timezone Normalization:** Always convert local timestamps to UTC ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`) before joining temporal tables.

---

### 5.2 Entity Resolution, Deduplication & Record Linkage

When disparate systems lack a universal primary key, apply **Record Linkage**:

1. **Deterministic Matching:** Exact joins across reliable identifier combinations (e.g. `normalized_phone == other.phone` AND `birth_date == other.birth_date`).
2. **Probabilistic / Fuzzy Matching:**
   - **Levenshtein Distance:** Minimum edit operations (insertions, deletions, substitutions) to transform string A to string B.
   - **Jaro-Winkler Similarity:** Weights character agreements with prefix bonuses (optimal for human names and address lines).
   - **Token Sort / Cosine Similarity:** Tokenize address lines and measure cosine similarity of n-gram vectors.
   - Establish high-confidence acceptance thresholds (e.g., similarity $\ge 0.92$) and route intermediate scores ($[0.75, 0.92)$) to human auditing queues.

---

### 5.3 Resolving Semantic & Numerical Data Value Conflicts

When merged records present contradictory facts for the same entity (e.g. CRM says age is 34, Billing DB says age is 36):

- **Establish Hierarchy of Truth:** Define authoritative source systems per attribute domain (e.g., Billing DB is authoritative for payment details; CRM is authoritative for contact preferences).
- **Recency Rules:** Use the record with the most recent verified audit timestamp.

---

### 5.4 Redundancy & Independence Analysis

Merging tables frequently introduces collinear and redundant attributes:

- **Categorical Redundancy via Chi-Square ($\chi^2$) Test:**

$$
\chi^2 = \sum \frac{(O - E)^2}{E}
$$

If two categorical features exhibit near-perfect correlation (e.g., `City` and `ZIP Code`), retaining both inflates dimensionality without providing novel information.

- **Numerical Redundancy via Pearson ($r$) and Spearman ($\rho$) Correlation:** Drop or combine features exhibiting collinearity $|r| > 0.90$.

---

## 6. Exploratory Data Analysis & Geometric Survey (EDA)

> **Mental Model:** Conceptualize every dataset sample as a single point positioned in an $N$-dimensional geometric space. Preprocessing does not mean applying arbitrary rules; it is the geometric reshaping of this coordinate space.

---

### 6.1 The Three Lenses of EDA

```text
               ┌────────────────────────────────────────────────────────┐
               │              LENS 1: GLOBAL TOPOLOGY                   │
               │  df.shape, df.dtypes, memory footprint, null counts    │
               └──────────────────────────┬─────────────────────────────┘
                                          │
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │          LENS 2: UNIVARIATE DISTRIBUTIONS              │
               │  Mean, Median, Skewness, Kurtosis, Histograms, KDE     │
               └──────────────────────────┬─────────────────────────────┘
                                          │
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │         LENS 3: MULTIVARIATE INTERACTIONS              │
               │  Correlation heatmaps, Pairplots, Mutual Information   │
               └────────────────────────────────────────────────────────┘
```

---

### 6.2 Univariate Distribution & Normality Diagnostics

Examine each feature independently to assess its empirical probability distribution:

- **Skewness ($S$):**
  - $S \approx 0$: Symmetric, bell-shaped (Gaussian candidate). Mean is representative.
  - $S > 1$: Strong right-skew (long positive tail, e.g., income, prices, web clicks). Median is representative; mean is distorted. Logarithmic or Box-Cox transformation indicated.
  - $S < -1$: Strong left-skew (long negative tail, e.g., age at retirement).
- **Kurtosis ($K$):** Measures tail heaviness. High kurtosis indicates extreme outlier vulnerability.
- **Statistical Normality Tests:** Shapiro-Wilk (small $N$), D'Agostino's $K^2$, or Q-Q plot visual inspection.

---

### 6.3 Bivariate & Multivariate Interaction Analysis

- **Linear Dependencies:** Pearson correlation matrix.
- **Monotonic Non-Linear Dependencies:** Spearman rank correlation.
- **Arbitrary Non-Linear Dependencies:** Mutual Information (MI).

> **Crucial Warning:** Two features can have a Pearson correlation $r = 0.00$ while sharing a strict deterministic non-linear relationship (e.g., $y = x^2$). Never eliminate a feature based solely on low linear correlation. Verify with scatter plots and Mutual Information.

---

### 6.4 How Data Geometry Governs Downstream Pipelines

| Observed Data Geometry              | Inevitable Downstream Requirement                                                               |
| :---------------------------------- | :---------------------------------------------------------------------------------------------- |
| Heavy right tail / exponential skew | Use median imputation (§7); apply log1p or Yeo-Johnson transform (§8); avoid standard MinMax. |
| Multimodal distribution             | Avoid global mean/median imputation; use Gaussian Mixture or KNN imputer (§7).                 |
| High collinearity among features    | Regularize models with L1 Lasso (§17); apply PCA dimensionality reduction (§12).              |
| Isolated density clusters           | Use DBSCAN density clustering (§15.2); avoid K-Means spherical assumptions.                    |

---

## 7. Missing Values: Mechanisms & Imputation

---

### 7.1 Mechanisms: MCAR, MAR, and MNAR

Before selecting an imputation technique, diagnose the statistical mechanism producing the missingness:

1. **MCAR (Missing Completely at Random):** Missingness is completely independent of both observed and unobserved features. Probability of missingness is uniform across all samples.
   - *Example:* A lab technician randomly drops a test tube.
   - *Action:* Dropping rows or standard mean/median imputation produces unbiased estimates.
2. **MAR (Missing at Random):** Missingness depends systematically on observed data, but not on the missing value itself.
   - *Example:* Men are less likely to report depression symptoms on a survey, but conditional on gender, missingness is random.
   - *Action:* Impute using multivariate regression or KNN models conditioned on observed features.
3. **MNAR (Missing Not at Random):** Missingness depends directly on the unobserved value itself.
   - *Example:* High-income earners refusing to disclose their salary.
   - *Action:* Imputing with mean or median introduces severe bias. Missingness itself must be modeled as an explicit feature indicator.

---

### 7.2 Numerical Imputation Strategies

- **Mean Imputation:** Use only when data is strictly Gaussian and missingness is MCAR.
- **Median Imputation:** Robust default for skewed numerical distributions or data containing outliers.
- **KNN Imputation:** Replaces missing values using the weighted average of the sample's $K$ nearest neighbors in feature space. Preserves local topological relationships.
- **Iterative / MICE (Multivariate Imputation by Chained Equations):** Models each feature with missing values as a regression function of other features in an iterative round-robin.

---

### 7.3 Categorical Imputation Strategies

- **Mode (`most_frequent`):** Suitable only when a single category overwhelmingly dominates the distribution ($> 70\%$).
- **Explicit "Missing" / "Unknown" Category:** Best practice when missingness may be non-random or carry semantic meaning.

---

### 7.4 Missingness as Informative Signal

When data is MAR or MNAR, the fact that a field is absent is itself predictive:

```python
# Create explicit missingness indicators
df['salary_was_missing'] = df['salary'].isnull().astype(int)
df['salary'] = df['salary'].fillna(df['salary'].median())
```

---

### 7.5 Imputation Selection Decision Tree

```text
Is the feature numerical?
  YES ──► Is missingness MNAR or informative?
            YES ──► Add MissingIndicator column + Median/KNN impute
            NO  ──► Is distribution Gaussian without severe outliers?
                      YES ──► Mean Imputation
                      NO  ──► Does missingness correlate with other features?
                                YES ──► KNNImputer or IterativeImputer
                                NO  ──► Median Imputation
  NO (Categorical) ──►
        Is missingness informative or distribution diverse?
            YES ──► Impute with new explicit category "Unknown"
            NO  ──► Impute with Mode (most frequent)
```

---

## 8. Outlier Detection & Anomaly Mining

---

### 8.1 Outlier Taxonomy: Noise vs. High-Value Signal

- **Corrupt Noise / Data Errors:** Sensor glitches, human typing errors (e.g. typing `99999` for missing income). These must be corrected or eliminated.
- **Novelty / High-Value Anomalies:** Fraudulent wire transfers, rare oncology symptoms, network intrusion attacks. **These points are the primary target of the data mining process.** Never blindly delete outliers without domain confirmation.

---

### 8.2 Statistical Outlier Detection (IQR, Z-Score, Grubbs)

- **IQR Rule (Non-Parametric):**

$$
\text{IQR} = Q_3 - Q_1, \quad \text{Lower} = Q_1 - 1.5 \cdot \text{IQR}, \quad \text{Upper} = Q_3 + 1.5 \cdot \text{IQR}
$$

- **Z-Score (Parametric, Gaussian Assumption):**

$$
z = \frac{x - \mu}{\sigma}, \quad \text{Flag if } |z| > 3.0
$$

---

### 8.3 Distance & Proximity-Based Detection (k-NN)

Computes the Euclidean distance from sample $x_i$ to its $k$-th nearest neighbor. Points residing in sparse regions exhibit significantly larger $k$-NN distances than points in dense clusters.

---

### 8.4 Density-Based Detection (Local Outlier Factor - LOF)

LOF compares the local density of a sample to the local densities of its neighbors:

$$
\text{LOF}(p) = \frac{\sum_{o \in N_k(p)} \frac{\text{lrd}(o)}{\text{lrd}(p)}}{|N_k(p)|}
$$

- $\text{LOF} \approx 1$: Normal density comparable to neighbors.
- $\text{LOF} > 1.5$: Outlier located in a region significantly sparser than its surrounding neighborhood. Effective for finding local anomalies embedded near dense clusters.

---

### 8.5 Isolation-Based Detection (Isolation Forest)

Instead of modeling normal points, **Isolation Forest** isolates anomalies:

- Randomly select a feature and randomly select a split value.
- Because anomalies are few and geometrically distinct, they are isolated in very few tree splits (shallow tree depth).
- Highly scalable, handles high-dimensional data, and requires no distance calculations.

---

### 8.6 Outlier Treatment Strategies & Non-Linear Transformations

| Strategy                          | When to Apply                                          | Implementation Pattern                                           |
| :-------------------------------- | :----------------------------------------------------- | :--------------------------------------------------------------- |
| **Purge / Delete**          | Verified data corruption or sensor failure             | `df = df[df[col].between(lower, upper)]`                       |
| **Winsorization (Capping)** | Legitimate extreme values in distance-sensitive models | `df[col] = df[col].clip(lower, upper)`                         |
| **Log1p Transform**         | Heavy right skew with strictly non-negative values     | `np.log1p(df[col])`                                            |
| **Yeo-Johnson Transform**   | Heavy skew with positive, zero, and negative values    | `sklearn.preprocessing.PowerTransformer(method='yeo-johnson')` |

---

## 9. Feature Scaling & Normalization

---

### 9.1 Geometric Necessity of Scaling

Algorithms calculating geometric distances (Euclidean, Manhattan) or computing gradients are corrupted when feature scales differ by orders of magnitude:

$$
\text{Distance} = \sqrt{(\Delta \text{Age}_{0-100})^2 + (\Delta \text{Income}_{0-10,000,000})^2} \approx \Delta \text{Income}
$$

Income completely dominates the metric space; Age contributes zero effective gradient.

---

### 9.2 Algorithm Sensitivity Matrix

| Algorithm Family                                        | Scale Sensitive?    | Rationale                                                                                |
| :------------------------------------------------------ | :------------------ | :--------------------------------------------------------------------------------------- |
| **KNN, K-Means, DBSCAN, PCA**                     | **EXTREMELY** | Operate directly on pairwise geometric distances or variance maximization                |
| **SVM (RBF Kernel)**                              | **EXTREMELY** | Kernel distances$\exp(-\gamma \|x_1 - x_2\|^2)$ distort without scaling                |
| **Linear / Logistic Regression, Neural Networks** | **YES**       | Gradient descent converges slowly or oscillates along unscaled ellipsoidal loss surfaces |
| **Decision Trees, Random Forest, XGBoost**        | **NO**        | Invariant to monotonic transformations; splits evaluate one feature threshold at a time  |
| **Association Rule Mining (Apriori, FP-Growth)**  | **NO**        | Operates on discrete transaction itemsets                                                |

---

### 9.3 Scaling Formulations (Standard, MinMax, Robust, Quantile)

- **Standardization (Z-score):**

$$
x' = \frac{x - \mu}{\sigma} \quad (\mu = 0, \sigma = 1)
$$

- **Min-Max Scaling:**

$$
x' = \frac{x - x_{\min}}{x_{\max} - x_{\min}} \quad (x' \in [0, 1])
$$

*Warning: Highly vulnerable to outliers. One outlier compresses all normal data.*

- **Robust Scaling:**

$$
x' = \frac{x - \text{median}}{\text{IQR}}
$$

*Outlier-resistant because median and IQR ignore extreme tail values.*

- **Quantile Transformation:** Maps empirical distribution to uniform or Gaussian distribution, completely neutralizing outlier distortion.

---

### 9.4 Scaling Selection Decision Tree

```text
Is the model tree-based (Random Forest, XGBoost) or Association Mining?
  YES ──► Scaling is not required.
  NO  ──► Are there significant, un-removable outliers?
            YES ──► RobustScaler or QuantileTransformer
            NO  ──► Does the algorithm require a bounded [0, 1] range (e.g. image pixels, neural activations)?
                      YES ──► MinMaxScaler
                      NO  ──► StandardScaler (Default)
```

---

## 10. Categorical Encoding & Dimensionality Management

---

### 10.1 Encoding as Metric Space Construction

Converting text categories to numbers is not simple format conversion. **Encoding embeds discrete symbols into a geometric metric space.** The chosen encoding dictates distances and geometric angles between classes.

---

### 10.2 Ordinal & Label Encoding

- **Ordinal Encoding:** Maps ranked categories to integers preserving ordering (`Low: 0, Medium: 1, High: 2`).
- **Misuse of Label Encoding:** Assigning nominal categories (`Red: 0, Green: 1, Blue: 2`) implies $2 > 1 > 0$ and $\text{dist}(\text{Red}, \text{Blue}) = 2 \times \text{dist}(\text{Red}, \text{Green})$. Linear models and neural networks will learn this false linear ordering.

---

### 10.3 One-Hot Encoding & Dummy Variable Trap

Each category receives its own orthogonal binary axis.

- **Advantage:** Imposes no false ordering; all categories are equidistant ($\sqrt{2}$).
- **Dummy Variable Trap:** In linear models with an intercept, including all $K$ binary columns introduces perfect multicollinearity ($\sum x_k = 1$). Set `drop='first'` to preserve $K-1$ columns.

---

### 10.4 High-Cardinality Encodings (Frequency, Target, Weight of Evidence)

When a categorical feature contains hundreds or thousands of unique values (e.g. `Postal_Code`, `Device_Model`), One-Hot Encoding causes extreme dimensional explosion.

- **Frequency / Count Encoding:** Replace category with its normalized frequency in training data.
- **Target Encoding:** Replace category with the mean of target $y$ for that category.
  - **⚠️ Severe Leakage Hazard:** Target encoding must be computed **strictly inside cross-validation training folds** with smoothing (empirical Bayes) to prevent target leakage.
- **Weight of Evidence (WoE):**

$$
\text{WoE} = \ln \left( \frac{\% \text{ of Good}}{\% \text{ of Bad}} \right)
$$

Widely used in financial credit scoring.

---

### 10.5 Curse of Dimensionality in Data Mining

As dimensionality $D$ increases:

1. **Space volume grows exponentially:** Data points become extremely sparse.
2. **Distance metrics collapse:** In high-dimensional spaces, the ratio of the distance to the nearest neighbor versus the farthest neighbor approaches 1:

$$
\lim_{D \to \infty} \frac{\text{dist}_{\max} - \text{dist}_{\min}}{\text{dist}_{\min}} \to 0
$$

All samples become equidistant. Clustering (K-Means) and distance-based classification (KNN) lose mathematical meaning.

---

### 10.6 Encoding Selection Decision Tree

```text
Does the categorical attribute possess an inherent natural ranking?
  YES ──► Ordinal Encoding
  NO  ──► Is cardinality low (unique values ≤ 10-15)?
            YES ──► One-Hot Encoding (use drop='first' for linear models)
            NO  ──► Is the target available and leakage strictly isolated?
                      YES ──► Target Encoding with Smoothing (inside CV folds only)
                      NO  ──► Frequency / Count Encoding or Embedding Layers
```

---

## 11. Class Imbalance & Cost-Sensitive Learning

---

### 11.1 The Base Rate Fallacy & The Accuracy Paradox

When predicting rare events (e.g. 99.5% legitimate transactions, 0.5% fraud):

- A trivial dummy classifier predicting "Legitimate" for every transaction achieves **99.5% accuracy**.
- It catches 0 fraudulent transactions and is commercially useless.
- **Golden Rule:** On imbalanced datasets, **Accuracy is an invalid metric**. Use Precision, Recall, F1, PR-AUC, and Cost-Weighted Loss.

---

### 11.2 Resampling Paradigms: Random, SMOTE, Borderline-SMOTE, Tomek

- **Random Oversampling:** Duplicates minority records. Prone to overfitting on specific samples.
- **SMOTE (Synthetic Minority Over-sampling Technique):** Synthesizes new points along line segments connecting existing minority samples to their $k$ nearest minority neighbors:

$$
x_{\text{new}} = x_i + \lambda (x_{zi} - x_i), \quad \lambda \sim U(0, 1)
$$

- **Borderline-SMOTE:** Synthesizes points only near the decision boundary where minority points are surrounded by majority points.
- **Tomek Links (Undersampling):** Identifies pairs of minimally distant samples of different classes and removes the majority sample, clarifying the decision boundary.

> **CRITICAL LEAKAGE INVARIANT:** Resampling techniques (SMOTE, undersampling) must be applied **exclusively to the training partition**. Never resample the validation or test partitions. The test partition must reflect real-world natural class distributions.

---

### 11.3 Cost-Sensitive Learning & Loss Weighting

Instead of artificially modifying dataset sizes, penalize errors on minority classes directly in the loss function:

```python
# scikit-learn built-in weighting
model = LogisticRegression(class_weight='balanced')

# PyTorch cost-weighted Cross-Entropy
class_weights = torch.tensor([1.0, 99.0])  # [majority, minority]
criterion = nn.CrossEntropyLoss(weight=class_weights)
```

---

### 11.4 Threshold Moving via Cost Matrix Optimization

Standard classifiers predict positive when probability $p \ge 0.5$. In asymmetric cost environments, shift threshold $T^*$ to minimize expected dollar loss:

$$
T^* = \arg\min_T \left[ C_{\text{FP}} \cdot \text{FP}(T) + C_{\text{FN}} \cdot \text{FN}(T) \right]
$$

---

## 12. Feature Engineering, Selection & Reduction

---

### 12.1 Domain-Driven Feature Construction

Feature engineering embeds business and physical domain knowledge into explicit columns:

- **Ratios & Proportions:** `debt_to_income = total_debt / annual_income`.
- **Temporal Windows & Recency:** `days_since_last_purchase`, `tx_count_last_7_days`.
- **Aggregation Signals:** `customer_mean_basket_value`, `ratio_to_category_average`.
- **Interaction Crosses:** Combining two categorical features (`gender x age_bracket`).

---

### 12.2 Geometric Meaning of Feature Expansion

Feature engineering lifts data points into higher-dimensional representations where non-linearly separable relationships become linearly separable (analogous to the Kernel Trick in SVMs).

---

### 12.3 Feature Selection Triad (Filter, Wrapper, Embedded)

```text
┌─────────────────┬────────────────────────────────────────────────────────┐
│ Selection Type  │ Mechanism, Pros & Cons                                 │
├─────────────────┼────────────────────────────────────────────────────────┤
│ 1. Filter       │ Evaluates statistical score between each feature and   │
│                 │ target independently of any model.                     │
│                 │ -> Methods: VarianceThreshold, Chi2, Mutual Info.      │
│                 │ -> Pros: Extremely fast, model-agnostic.               │
│                 │ -> Cons: Ignores feature interactions and dependencies.│
├─────────────────┼────────────────────────────────────────────────────────┤
│ 2. Wrapper      │ Uses model performance as an evaluation metric to test │
│                 │ feature subsets.                                       │
│                 │ -> Methods: Recursive Feature Elimination (RFE), SFS.  │
│                 │ -> Pros: Finds optimal interactions for given model.   │
│                 │ -> Cons: Computationally expensive; risks overfitting. │
├─────────────────┼────────────────────────────────────────────────────────┤
│ 3. Embedded     │ Feature selection is performed internally as part of   │
│                 │ model training.                                        │
│                 │ -> Methods: Lasso L1 regularization, Tree Feature      │
│                 │    Importance (MDI / Gain), XGBoost.                   │
│                 │ -> Pros: Optimal tradeoff between speed and interaction│
│                 │    capture.                                            │
└─────────────────┴────────────────────────────────────────────────────────┘
```

---

### 12.4 Unsupervised Dimensionality Reduction (PCA, SVD, t-SNE, UMAP)

- **Principal Component Analysis (PCA):** Linear orthogonal transformation projecting data onto directions of maximum variance. Preserves global Euclidean structure.
- **t-SNE:** Non-linear dimensionality reduction modeling pairwise local similarities with Student-t distributions. Designed strictly for 2D/3D visualization, **not for training downstream models**.
- **UMAP (Uniform Manifold Approximation and Projection):** Preserves both local and global topological structure; orders of magnitude faster than t-SNE.

---

### 12.5 Numerosity Reduction & Discretization (Equal-Width vs. Equal-Frequency)

- **Equal-Width Binning:** Divides attribute range $[x_{\min}, x_{\max}]$ into $k$ equal intervals. Sensitive to outliers.
- **Equal-Frequency Binning:** Divides sorted values such that each bin contains an identical count of records (quantiles). Outlier-robust.

---

## 13. Data Partitioning & The Leakage Boundary

---

### 13.1 The Golden Leakage Boundary

> **Data Leakage Defined:** The fatal flaw where information from outside the training partition (from the validation set, test set, or future timeline) inadvertently leaks into the model training pipeline.

```text
======================= FULL RAW DATASET =======================
                  │
                  ▼
         [TRAIN / TEST SPLIT]  ← PERFORMED BEFORE ANY STATISTIC IS COMPUTED
         ┌────────┴────────┐
         ▼                 ▼
   TRAINING SET        TEST SET (Locked in a vault)
   [80% of data]       [20% of data]
         │                 │
Compute μ, σ, medians      │
Fit scalers, imputers      │
Fit SMOTE, encoders        │
Train model weights        │
         │                 │
         │          Apply frozen transformations (transform only)
         │                 │
         └────────► Evaluate final generalization metrics
```

---

### 13.2 Partitioning Schemes: Random, Stratified, Temporal, Group-Based

- **Random Split:** Valid only for balanced, independent and identically distributed (IID) tabular data without temporal or grouped structures.
- **Stratified Split:** Mandatory for classification tasks. Preserves identical class proportions across train, validation, and test splits.
- **Temporal / Chronological Split:** Mandatory for time series or event logs. Train on past records ($t_0 \dots t_k$), validate on intermediate records ($t_{k+1} \dots t_m$), test on most recent records ($t_{m+1} \dots t_{\text{now}}$). Random splitting on temporal data causes massive lookahead leakage.
- **Group / Entity Split (`GroupKFold`):** Mandatory when multiple records belong to the same entity (e.g. multiple transactions per customer, multiple X-rays per patient). All records for a given patient must reside entirely in train or entirely in test. Random splitting allows the model to memorize patient identities.

---

### 13.3 Implementation Invariant: `fit()` vs. `transform()`

```python
# CORRECT: Leakage-Free Pipeline
scaler.fit(X_train)                  # Learn statistics ONLY from train
X_train_scaled = scaler.transform(X_train)
X_val_scaled   = scaler.transform(X_val)    # Transform using train statistics
X_test_scaled  = scaler.transform(X_test)

# FATAL LEAKAGE: Leaks test distribution into training
scaler.fit(X_all)                    # VIOLATION
```

---

## 14. Baseline Thinking & Benchmark Formulation

---

### 14.1 The Role of the Baseline in Scientific Discovery

Never evaluate a complex data mining model in a vacuum. A model reporting 88% accuracy is unimpressive if a simple two-line heuristic achieves 89%.

The baseline represents the **lower bound of acceptable performance**. Every added layer of model complexity must empirically justify its computational and operational cost above the baseline.

---

### 14.2 Trivial & Empirical Baselines Across Mining Tasks

| Mining Task                 | Trivial Baseline                                              | Simple ML Baseline                                            |
| :-------------------------- | :------------------------------------------------------------ | :------------------------------------------------------------ |
| **Classification**    | Majority class prediction (`DummyClassifier`)               | Single shallow Decision Tree ($D=3$) or Logistic Regression |
| **Regression**        | Mean or Median prediction (`DummyRegressor`)                | Ordinary Least Squares (OLS) Linear Regression                |
| **Time Series**       | Naive persistence ($\hat{y}_{t+1} = y_t$) or Moving Average | Auto-ARIMA or Exponential Smoothing                           |
| **Association Rules** | Random co-occurrence frequency                                | Top-$k$ global most popular itemsets                        |
| **Clustering**        | Random cluster assignment                                     | Standard K-Means with random centroids                        |

---

### 14.3 Minimum Viable Accuracy & Cost-Benefit Thresholds

Before training complex models, establish the **Minimum Viable Performance (MVP)** required for production deployment based on the business cost matrix (§1.3). If a baseline cannot clear the MVP threshold, the problem framing or data collection must be revised.

---

## 15. Core Mining & Modeling Paradigms

---

### 15.1 Frequent Pattern & Association Rule Mining

Frequent Pattern Mining discovers co-occurrence relationships and associations embedded in transactional databases, event logs, and shopping baskets.

#### 15.1.1 Market Basket Representation & Core Metrics (Support, Confidence, Lift, Leverage, Conviction)

Let $I = \{i_1, i_2, \dots, i_m\}$ be the universe of items, and $D = \{T_1, T_2, \dots, T_n\}$ be the transactional database. An association rule is an implication $X \implies Y$, where $X \subset I$, $Y \subset I$, and $X \cap Y = \emptyset$.

```text
┌─────────────────┬────────────────────────────────────────────────────────┐
│ Metric          │ Formula & Interpretation                               │
├─────────────────┼────────────────────────────────────────────────────────┤
│ Support         │ supp(X) = count(X) / |D|                               │
│                 │ Fraction of transactions containing itemset X.         │
│                 │ Filters out rare, statistically insignificant noise.   │
├─────────────────┼────────────────────────────────────────────────────────┤
│ Confidence      │ conf(X => Y) = supp(X U Y) / supp(X)                   │
│                 │ Conditional probability: Given X is purchased, what    │
│                 │ is the probability Y is also purchased? P(Y | X).      │
├─────────────────┼────────────────────────────────────────────────────────┤
│ Lift            │ lift(X => Y) = conf(X => Y) / supp(Y)                  │
│                 │              = supp(X U Y) / (supp(X) * supp(Y))       │
│                 │ Ratio of observed joint support to expected support    │
│                 │ under statistical independence.                        │
│                 │ -> Lift = 1: X and Y are independent.                  │
│                 │ -> Lift > 1: Positive association (co-occur more than  │
│                 │    chance).                                            │
│                 │ -> Lift < 1: Negative association (substitutes).       │
├─────────────────┼────────────────────────────────────────────────────────┤
│ Leverage        │ lev(X => Y) = supp(X U Y) - supp(X) * supp(Y)          │
│                 │ Difference between observed and expected support in    │
│                 │ absolute probability units.                            │
├─────────────────┼────────────────────────────────────────────────────────┤
│ Conviction      │ conv(X => Y) = (1 - supp(Y)) / (1 - conf(X => Y))      │
│                 │ Measures degree of implication failure; approaches     │
│                 │ infinity if rule holds perfectly.                      │
└─────────────────┴────────────────────────────────────────────────────────┘
```

#### 15.1.2 The Apriori Principle & Candidate Generation

The search space for frequent itemsets contains $2^{|I|} - 1$ possible combinations (combinatorial explosion). The **Apriori Principle** prunes this space:

> **The Apriori Downward-Closure Property:** If an itemset is frequent, all of its subsets must also be frequent. Conversely, if an itemset $S$ is infrequent, any superset containing $S$ is guaranteed to be infrequent and is immediately pruned without database scanning.

```text
Level 1: Scan DB -> Find Frequent 1-itemsets (L1)
Level 2: Join L1 with L1 -> Candidate 2-itemsets (C2) -> Scan DB -> Prune -> L2
Level k: Join L_{k-1} with L_{k-1} -> C_k -> Prune infrequent subsets -> Scan DB -> L_k
Repeat until no frequent itemsets remain.
```

#### 15.1.3 FP-Growth & FP-Tree Architecture

Apriori requires repeated, costly scans of the entire database. **FP-Growth (Frequent Pattern Growth)** eliminates candidate generation:

1. Scans database twice: First to find frequent items; second to build a compact memory-resident **FP-Tree** (Frequent Pattern Tree) where transactions share prefix branches.
2. Mines the FP-Tree recursively by building conditional pattern bases and conditional FP-Trees. Typically orders of magnitude faster than Apriori.

#### 15.1.4 ECLAT & Vertical Data Layout

**ECLAT (Equivalence Class Clustering and bottom-up Lattice Traversal)** operates on a **vertical data format**:

- Instead of mapping `Transaction_ID -> {Item1, Item2}`, ECLAT maps `Item -> {TID_1, TID_4, TID_9}` (TID-list).
- Itemset support is computed via simple set intersection of TID-lists:

$$
\text{TID-list}(X \cup Y) = \text{TID-list}(X) \cap \text{TID-list}(Y)
$$

#### 15.1.5 Actionable Rule Mining vs. Spurious Associations

Not all high-confidence rules are useful:

- **Trivial Rules:** Rules that reflect tautologies or business policies (e.g. `Maintenance Agreement => Equipment Purchase`, `Pregnant => Female`).
- **Spurious Rules (High Confidence, Misleading Lift):** If 90% of all customers buy Milk, any rule `Bread => Milk` will have high confidence ($> 90\%$) simply because Milk is ubiquitous, even if Bread and Milk are completely independent ($\text{Lift} \approx 1.0$). Always filter by **Lift > 1.5** and Leverage, not Confidence alone.

---

### 15.2 Cluster Analysis & Density Mining

Cluster analysis partitions unlabeled data into distinct geometric groups such that intra-cluster similarity is maximized and inter-cluster similarity is minimized.

#### 15.2.1 Partitioning: K-Means & K-Medoids (PAM)

- **K-Means (Lloyd's Algorithm):**

  1. Initialize $K$ centroids randomly (or via K-Means++).
  2. Assign each sample to its nearest Euclidean centroid.
  3. Recompute centroids as the mean coordinates of assigned samples.
  4. Repeat until convergence.

  - *Assumptions:* Clusters are spherical, similarly sized, and linearly separable. Highly sensitive to feature scaling and outliers.
- **K-Medoids / PAM (Partitioning Around Medoids):** Centroids must be actual observed data points (medoids). Minimizes absolute pairwise distances (Manhattan) rather than squared Euclidean error. Extremely robust to outliers.

#### 15.2.2 Hierarchical: Agglomerative Linkage Criteria & Dendrogram Analysis

Builds a bottom-up cluster hierarchy tree (dendrogram):

- **Single Linkage:** Minimum distance between any point in cluster A and any point in cluster B. Prone to chaining effects (long stringy clusters).
- **Complete Linkage:** Maximum distance between clusters. Produces compact, spherical clusters.
- **Average Linkage:** Average pairwise distance between all member points.
- **Ward's Linkage:** Minimizes total within-cluster variance increase upon merging. Best default for balanced clusters.

#### 15.2.3 Density-Based: DBSCAN, OPTICS & HDBSCAN

- **DBSCAN (Density-Based Spatial Clustering of Applications with Noise):**
  - Defines clusters as dense continuous regions separated by low-density zones.
  - Parameters: $\epsilon$ (neighborhood radius) and $\text{MinPts}$ (minimum points within $\epsilon$).
  - Point classifications:
    - **Core Point:** Has $\ge \text{MinPts}$ within distance $\epsilon$.
    - **Border Point:** Has $< \text{MinPts}$ within $\epsilon$, but falls within $\epsilon$ of a Core Point.
    - **Noise Point:** Neither Core nor Border. Automatically labeled as anomaly/outlier.
  - *Superpower:* Finds arbitrarily shaped clusters (crescents, rings, spirals) and isolates noise without forcing points into artificial clusters.
- **HDBSCAN:** Hierarchical density clustering that eliminates the brittle fixed $\epsilon$ threshold, finding clusters across varying densities.

#### 15.2.4 Model-Based: Gaussian Mixture Models & Expectation-Maximization

Assumes data is generated from a mixture of $K$ underlying Gaussian distributions with individual means $\mu_k$ and covariance matrices $\Sigma_k$.

- Applies the **Expectation-Maximization (EM)** algorithm to compute soft probabilistic cluster assignments: $P(\text{Cluster}_k \mid x_i)$.
- Supports ellipsoidal clusters with varying orientations and sizes.

#### 15.2.5 Cluster Validation Metrics (Silhouette, Davies-Bouldin, Calinski-Harabasz, Dunn)

- **Silhouette Coefficient ($s$):**

$$
s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}, \quad s \in [-1, 1]
$$

Where $a(i)$ is mean intra-cluster distance and $b(i)$ is mean nearest-cluster distance. Scores near +1 indicate dense, well-separated clusters.

- **Davies-Bouldin Index (DBI):** Ratio of within-cluster scatter to between-cluster separation. Lower is better.
- **Calinski-Harabasz (CH) Index:** Ratio of between-cluster dispersion to within-cluster dispersion. Higher is better.

---

### 15.3 Supervised Classification & Regression

#### 15.3.1 Decision Trees (ID3, C4.5, CART: Entropy, Information Gain, Gini)

Recursively partitions feature space using orthogonal axis-aligned thresholds:

- **Entropy & Information Gain (ID3):**

$$
H(S) = -\sum p_i \log_2(p_i), \quad \text{Gain}(S, A) = H(S) - \sum \frac{|S_v|}{|S|} H(S_v)
$$

- **Gini Impurity (CART):**

$$
\text{Gini}(S) = 1 - \sum p_i^2
$$

- **Pruning:** Unrestricted trees grow until leaf nodes are pure, resulting in severe overfitting. Apply pre-pruning (`max_depth`, `min_samples_leaf`) or post-pruning (Cost-Complexity Pruning $\alpha$).

#### 15.3.2 Ensembles: Bagging, Random Forests, Gradient Boosting (XGBoost, LightGBM, CatBoost)

- **Bagging (Bootstrap Aggregation):** Trains independent models on bootstrap samples of the training set; averages predictions to reduce **variance**.
- **Random Forest:** Bagging combined with random feature subspace sampling at every split, decorrelating individual decision trees.
- **Gradient Boosting:** Sequentially trains trees where each successive tree fits the pseudo-residuals (negative gradient of the loss function) of the previous ensemble. Reduces **bias and variance**.
  - **XGBoost:** Second-order Taylor gradient expansion with tree complexity regularization.
  - **LightGBM:** Histogram-based feature binning and Leaf-wise (best-first) tree growth for petabyte-scale speed.
  - **CatBoost:** Native handling of categorical features via ordered target statistics, preventing target leakage.

#### 15.3.3 Distance-Based: K-Nearest Neighbors (KNN)

Predicts target based on majority vote or distance-weighted average of the $K$ closest training samples. Non-parametric, zero training time (lazy learner), but $O(N)$ inference cost and highly scale-sensitive.

#### 15.3.4 Probabilistic: Naive Bayes Classifiers & Laplace Correction

Applies Bayes' Theorem assuming features are conditionally independent given class label:

$$
P(y \mid X) \propto P(y) \prod_{j=1}^D P(x_j \mid y)
$$

- **Laplace Smoothing:** Adds pseudo-counts to prevent zero-probability lockouts when a feature value was unobserved during training:

$$
\hat{P}(x_j \mid y) = \frac{\text{count}(x_j, y) + 1}{\text{count}(y) + K}
$$

#### 15.3.5 Maximum Margin: Support Vector Machines & The Kernel Trick

Finds the optimal separating hyperplane that maximizes the margin (distance to closest points of any class, the Support Vectors).

- Maps non-linearly separable points into higher dimensions via Mercer kernels:
  - Polynomial Kernel: $K(x, x') = (x^T x' + c)^d$
  - Radial Basis Function (RBF): $K(x, x') = \exp(-\gamma \|x - x'\|^2)$

#### 15.3.6 Linear & Logistic Models with Regularization

- **Linear Regression (OLS):** Closed-form analytical solution $\hat{\beta} = (X^T X)^{-1} X^T y$.
- **Logistic Regression:** Sigmoid link function $\sigma(z) = \frac{1}{1 + e^{-z}}$ optimizing binary cross-entropy loss via gradient descent.

---

## 16. Model Selection, Inductive Bias & No Free Lunch

---

### 16.1 The No Free Lunch Theorem

> **Wolpert's No Free Lunch (NFL) Theorem:** Averaged across all possible data-generating distributions, no machine learning algorithm is universally superior to any other—even random guessing.

An algorithm outperforms another only because its **inductive bias** matches the geometric reality of the specific problem.

---

### 16.2 Inductive Bias: Matching Assumptions to Data Geometry

| Algorithm                              | Core Inductive Bias                                                           | Optimal Data Geometry                                       |
| :------------------------------------- | :---------------------------------------------------------------------------- | :---------------------------------------------------------- |
| **Linear / Logistic Regression** | Target is a linear combination of features; classes are hyper-plane separable | Smooth, additive linear relationships                       |
| **Naive Bayes**                  | All features are conditionally independent given class label                  | High-dimensional text / bag-of-words                        |
| **KNN**                          | Samples close in Euclidean feature space share similar target labels          | Dense, smooth local manifolds ($D < 20$)                  |
| **Decision Trees**               | Target function can be approximated by recursive orthogonal hyper-rectangles  | Tabular data with non-linear feature threshold interactions |
| **DBSCAN**                       | Clusters are continuous high-density islands separated by empty space         | Non-spherical geometric topologies with noise               |
| **Neural Networks (MLP)**        | Target function can be represented by compositional hierarchical functions    | Complex continuous mappings                                 |

---

### 16.3 Systematic Model Selection Flowchart

```text
What is the core target format?
  ├─► Discrete Itemsets / Baskets ──► Frequent Pattern Mining (FP-Growth, Apriori)
  ├─► Unlabeled Continuous/Tabular ──►
  │     ├─► Spherical, clean, fixed K ──► K-Means
  │     └─► Arbitrary shapes / noise present ──► DBSCAN / HDBSCAN
  └─► Labeled Data ──►
        ├─► Tabular / Structured Heterogeneous ──► Gradient Boosted Trees (XGBoost/LightGBM)
        ├─► High-Dimensional Sparse Text ──► Naive Bayes or Linear SVM
        ├─► Strict Legal Interpretability Required ──► Shallow CART Tree, Logistic Regression, EBM
        └─► Complex Vision / Audio / NLP Embeddings ──► Deep Neural Networks
```

---

## 17. Bias–Variance Tradeoff & Regularization

---

### 17.1 Mathematical Decomposition of Expected Generalization Error

For any supervised regression estimator $\hat{f}(x)$, expected test mean squared error decomposes into three mutually exclusive components:

$$
\mathbb{E}[(y - \hat{f}(x))^2] = \underbrace{\text{Bias}[\hat{f}(x)]^2}_{\text{Underfitting}} + \underbrace{\text{Var}[\hat{f}(x)]}_{\text{Overfitting}} + \underbrace{\sigma^2}_{\text{Irreducible Noise}}
$$

```text
Error
  ▲
  │       \                      /  Total Generalization Error
  │        \                    /
  │         \      Optimal     /
  │          \     Tradeoff   /
  │           ▼       ▼      ▼
  │            \     ___    /
  │             \___/   \__/
  │              \        /
  │ Bias^2        \      /      Variance
  │ (Underfitting) \    /       (Overfitting)
  └─────────────────▼──/────────────────────────► Model Complexity
```

---

### 17.2 Diagnostic Signatures: Learning Curves & Error Gaps

- **High Bias (Underfitting):** Both training error and validation error are high and nearly identical. Model lacks capacity to capture true pattern.
  - *Remedies:* Add features, create interaction terms, decrease regularization, switch to more complex model family.
- **High Variance (Overfitting):** Training error is exceptionally low, but validation error is dramatically higher (large generalization gap).
  - *Remedies:* Add more training data, apply feature selection, increase regularization penalties, prune trees, use dropout.

---

### 17.3 Regularization Mechanics: L1 (Lasso), L2 (Ridge), ElasticNet, Tree Pruning

- **L2 Regularization (Ridge):** Adds $\lambda \sum \beta_j^2$ penalty. Shrinks coefficients continuously toward zero; handles collinearity; retains all features.
- **L1 Regularization (Lasso):** Adds $\lambda \sum |\beta_j|$ penalty. Constrains optimization to a diamond $L_1$ ball, driving uninformative feature weights to **exactly zero** (performs automatic feature selection).
- **ElasticNet:** Convex combination of L1 and L2 penalties: $\alpha L_1 + (1-\alpha) L_2$.
- **Tree Pruning:** Minimizes cost-complexity criterion $R_\alpha(T) = R(T) + \alpha |T|$.

---

## 18. Hyperparameter Optimization & Tuning

---

### 18.1 Parameters vs. Hyperparameters

- **Model Parameters:** Internal weights learned automatically from training data via optimization (e.g. regression coefficients $\beta$, neural network weights $W, b$, decision tree split thresholds).
- **Hyperparameters:** Configuration choices set externally by the engineer **prior to training** that govern the learning process (e.g. learning rate $\eta$, tree `max_depth`, regularization penalty $\lambda$, DBSCAN $\epsilon$, K-Means $K$).

---

### 18.2 Search Strategies: Grid, Random, Bayesian (Optuna TPE)

- **Grid Search:** Exhaustively evaluates every combination on a discrete grid. Exponentially inefficient; wastes compute testing uninformative hyperparameter variations.
- **Random Search:** Randomly samples hyperparameter combinations from specified statistical distributions. Provably explores search spaces faster than grid search.
- **Bayesian Optimization (Tree-structured Parzen Estimators - TPE):**
  - Models historical trial evaluations probabilistically.
  - Balances exploration (sampling uncertain regions) and exploitation (refining known optimal regions) using Expected Improvement (EI).
  - Implemented canonically via `Optuna`.

---

### 18.3 Tuning Inside Cross-Validation Folds

> **CRITICAL RULE:** Never tune hyperparameters against the test set. Hyperparameter search must be conducted strictly across inner cross-validation folds. Evaluating 500 hyperparameter trials on a single validation set overfits the validation set.

---

## 19. Comprehensive Evaluation Metrics: Technical & Business Impact

---

### 19.1 Supervised Classification Metrics

```text
Confusion Matrix:
                 Actual Positive     Actual Negative
Predicted Pos    True Positive (TP)  False Positive (FP) -> Type I Error
Predicted Neg    False Negative (FN) True Negative (TN) -> Type II Error
                 Type II Error
```

- **Accuracy:** $\frac{\text{TP} + \text{TN}}{\text{Total}}$ (Valid only when classes are perfectly balanced).
- **Precision:** $\frac{\text{TP}}{\text{TP} + \text{FP}}$ (Quality of positive alarms. Critical when false alarms are costly, e.g. spam filter).
- **Recall (Sensitivity):** $\frac{\text{TP}}{\text{TP} + \text{FN}}$ (Completeness of detection. Critical when missing a positive is catastrophic, e.g. cancer, fraud).
- **F1-Score:** Harmonic mean of precision and recall: $\frac{2 \cdot P \cdot R}{P + R}$.
- **PR-AUC (Precision-Recall AUC):** The area under the Precision-Recall curve. Superior to ROC-AUC when evaluating heavily imbalanced datasets.
- **ROC-AUC:** Measures discrimination across all thresholds against a random baseline ($0.5$).

---

### 19.2 Supervised Regression Metrics

- **Mean Absolute Error (MAE):** $\frac{1}{N} \sum |y - \hat{y}|$ (Robust to outliers; preserves target unit).
- **Root Mean Squared Error (RMSE):** $\sqrt{\frac{1}{N} \sum (y - \hat{y})^2}$ (Penalizes large errors heavily due to squaring).
- **Mean Absolute Percentage Error (MAPE):** Measures relative percentage deviation. Undefined when $y = 0$.
- **$R^2$ (Coefficient of Determination):** Proportion of target variance explained by model: $1 - \frac{\text{SS}_{\text{res}}}{\text{SS}_{\text{tot}}}$.

---

### 19.3 Association Mining Metrics

- **Support:** Base frequency.
- **Confidence:** Conditional probability.
- **Lift:** Deviation from independence ($> 1.0$ is positive association).
- **Leverage & Conviction:** Absolute probability gains and implication directional integrity.

---

### 19.4 Clustering Metrics

- **Internal (No Ground Truth):** Silhouette Coefficient ($[-1, 1]$), Davies-Bouldin Index ($\downarrow$), Calinski-Harabasz Index ($\uparrow$).
- **External (Ground Truth Labels Available):** Adjusted Rand Index (ARI), Normalized Mutual Information (NMI).

---

### 19.5 Translating Technical Metrics into Expected Monetary Value ($)

Always translate evaluation metrics into currency for executive stakeholders:

$$
\text{Net Profit} = (\text{TP} \times \text{Benefit}_{\text{TP}}) - (\text{FP} \times \text{Cost}_{\text{FP}}) - (\text{FN} \times \text{Cost}_{\text{FN}}) - \text{Operational Overhead}
$$

---

## 20. Cross-Validation & Resampling Strategies

---

### 20.1 K-Fold & Stratified K-Fold

Partitions training data into $K$ equal folds. Iteratively trains on $K-1$ folds and validates on the remaining fold:

$$
\text{CV Score} = \mu \pm \sigma = \frac{1}{K} \sum_{k=1}^K s_k \pm \text{std}(s_k)
$$

- **Stratified K-Fold:** Guarantees each fold contains identical target class proportions.

---

### 20.2 Temporal Cross-Validation (Expanding & Rolling Window)

For sequential or time-series data:

- **Expanding Window:** Fold 1 trains on $t_1 \dots t_k$, tests on $t_{k+1}$. Fold 2 trains on $t_1 \dots t_{k+1}$, tests on $t_{k+2}$. Never trains on future data.
- **Rolling Window:** Fixed-size training window that slides forward through time.

---

### 20.3 Group & Entity Cross-Validation

Uses `GroupKFold` to ensure all records associated with a specific entity (e.g. `patient_id`, `device_serial`) remain grouped entirely within the training folds or entirely within the validation fold.

---

### 20.4 Nested Cross-Validation (Unbiased Generalization Estimate)

When hyperparameter tuning and model selection are conducted, a single cross-validation loop leaks validation scores into model selection:

- **Inner CV Loop ($K_{\text{inner}} = 3$):** Explores hyperparameters and selects best trial.
- **Outer CV Loop ($K_{\text{outer}} = 5$):** Evaluates true generalization error of the selected model.

---

## 21. Scientific Experimentation & The Single-Variable Principle

---

### 21.1 The Single-Variable Isolation Principle

> **Scientific Core:** In any comparison experiment between Model A and Model B, **change exactly one variable at a time**.

If you simultaneously change the imputation strategy, add SMOTE, and switch from Random Forest to XGBoost, you cannot determine which modification caused the performance change. Hold all other variables, preprocessing steps, and seeds constant.

---

### 21.2 Seed Control & Multi-Run Stability

Stochastic algorithms depend on pseudorandom number generators (seeds). Report performance averaged across multiple seeds (`seed=42, 100, 2026`) to ensure improvements are statistically genuine and not random seed artifacts.

---

### 21.3 Experiment Logging & Metadata Tracking

Every experiment run must automatically record:

1. Exact git commit hash.
2. Complete hyperparameter configuration (`config.yaml`).
3. Execution timestamp and environment dependencies.
4. Full 5W1H empirical metrics context.

---

## 22. Statistical Significance Testing & Confidence Intervals

---

### 22.1 Comparing Model Performance Beyond Mean Scores

If Model A scores 86.4% F1 and Model B scores 87.1% F1 across 5 folds, is Model B genuinely superior or did it win by random chance?

---

### 22.2 Parametric vs. Non-Parametric Tests (Paired t-test, Wilcoxon, McNemar)

- **Paired Student's t-test:** Parametric test evaluating whether mean score differences across folds are significantly non-zero. Assumes normal differences.
- **Wilcoxon Signed-Rank Test:** Non-parametric alternative to paired t-test. Does not assume normality; evaluates rank differences across paired cross-validation folds.
- **McNemar's Test:** Specifically designed for comparing two classifiers evaluated on the **exact same test set**. Evaluates the contingency matrix of disagreement:

$$
\chi^2 = \frac{(|b - c| - 1)^2}{b + c}
$$

Where $b$ is cases Model A got right and B got wrong, and $c$ is cases Model B got right and A got wrong.

---

### 22.3 Bootstrapped Confidence Intervals (95% CI)

Resample the test set with replacement $B = 1,000$ times, calculate metric $M_b$ for each sample, and extract the 2.5th and 97.5th percentiles. If the 95% confidence intervals of Model A and Model B do not overlap, the performance difference is statistically significant at $p < 0.05$.

---

## 23. Error Analysis & Residual Diagnostics (The 5W Framework)

---

### 23.1 Subgroup Slicing & Error Decomposition

Aggregate metrics hide critical subgroup failures. A facial recognition model reporting 96% accuracy may exhibit 99% accuracy on adult males but 62% accuracy on minority female subgroups.

- Slice error rates across demographics, geographies, time-of-day, and value bands.

---

### 23.2 Residual Diagnostic Plots for Regression

Evaluate regression residuals $e_i = y_i - \hat{y}_i$:

1. **Residuals vs. Fitted Values Plot:** Residuals must distribute symmetrically around zero with constant variance (homoscedasticity). A funnel shape indicates heteroscedasticity; a curved pattern indicates uncaptured non-linearity.
2. **Q-Q Plot:** Verifies whether residuals follow a normal distribution.

---

### 23.3 The 5W Framework for Rigorous Metric Reporting

Every reported metric must satisfy the constitutional **5W Framework**:

| W               | Question to Document                        | Example                                                        |
| :-------------- | :------------------------------------------ | :------------------------------------------------------------- |
| **What**  | What exact metric is reported?              | Precision@Top-Decile and PR-AUC                                |
| **Where** | Which dataset, partition, and fold?         | Holdout Test Set (20% partition, unseen)                       |
| **When**  | At what iteration or checkpoint?            | Best early-stopping checkpoint (epoch 42)                      |
| **Why**   | Why did this model beat the baseline?       | Engineered ratio features captured non-linear debt interaction |
| **Which** | Which specific subgroup does this apply to? | High-volume corporate tier accounts                            |

---

## 24. Model Interpretability & Explainable AI

---

### 24.1 Intrinsic vs. Post-Hoc Interpretability

- **Intrinsic (White-Box):** Models whose mathematical structure is directly interpretable by humans (Linear Regression coefficients, shallow Decision Trees, Rule-based systems).
- **Post-Hoc (Black-Box):** Explaining complex models (Ensembles, Neural Networks) after training using external mathematical surrogates.

---

### 24.2 Global Interpretability: Permutation Importance & PDP

- **Permutation Feature Importance:** Measures the increase in prediction error after randomly shuffling the values of a single feature. Model-agnostic and immune to tree impurity bias.
- **Partial Dependence Plots (PDP):** Visualizes the marginal effect of one or two features on the predicted target outcome, holding all other features constant.

---

### 24.3 Local Interpretability: SHAP (Shapley Values) & LIME

- **SHAP (SHapley Additive exPlanations):**
  - Grounded in cooperative game theory.
  - Calculates the unique marginal contribution of each feature value across all possible feature coalitions.
  - Satisfies formal axioms: Local Accuracy, Missingness, and Consistency.

$$
\phi_i(x) = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|! (|F| - |S| - 1)!}{|F|!} \left[ f(S \cup \{i\}) - f(S) \right]
$$

- **LIME (Local Interpretable Model-agnostic Explanations):** Fits an interpretable sparse linear surrogate model locally around the specific sample prediction.

---

## 25. Business Evaluation & Knowledge Validation (CRISP-DM Phase 5)

---

### 25.1 Validating Findings Against Initial Business Criteria

Before deployment, convene the business evaluation gate:

1. Did the pipeline meet the quantifiable business criteria established in §1.1?
2. Does the model operate within legal, compliance, and privacy constraints?
3. Does the financial return on investment (ROI) exceed maintenance costs?

---

### 25.2 The Actionability Filter: Novel, Non-Trivial, Actionable Knowledge

Knowledge extracted by data mining must pass three filters:

- **Novelty:** Discovers relationships not previously known to domain experts.
- **Non-Triviality:** Cannot be derived from basic arithmetic or common knowledge.
- **Actionability:** The business must possess the operational capability to act on the discovered insight.

---

### 25.3 Go / No-Go Deployment Decision Gate

```text
Decision Checklist:
[ ] 1. Leakage verification passed (no future/test data leaked).
[ ] 2. Outperformed simple empirical baselines by a statistically significant margin.
[ ] 3. Passed fairness and subgroup slice equity audit.
[ ] 4. Net financial value (Expected Monetary Value) is strictly positive.
[ ] 5. Explainability requirements satisfied per regulatory mandates.
[ ] 6. Fallback rule heuristic operational if microservice fails.
```

---

## 26. Deployment, Actionability & Operational Monitoring (CRISP-DM Phase 6)

---

### 26.1 Deployment Modalities: Batch, REST API, Embedded, BI Rule Engines

- **Batch Scoring Jobs:** Scheduled cron jobs scoring millions of records in data warehouses (e.g. nightly churn risk scoring).
- **Synchronous REST / gRPC Microservice:** Low-latency online prediction server (e.g. FastAPI / TorchServe scoring loan applications in $< 50\text{ms}$).
- **Embedded Edge Models:** Exporting models via ONNX or TensorRT directly into mobile apps or IoT firmware.
- **BI Rule Engines & Dashboards:** Exporting discovered association rules directly into CRM recommendation engines.

---

### 26.2 Continuous Monitoring: Data Drift vs. Concept Drift

Models degrade after deployment because real-world distributions evolve:

```text
┌──────────────────────┬────────────────────────────────────────────────────────┐
│ Drift Type           │ Mathematical Definition & Manifestation                │
├──────────────────────┼────────────────────────────────────────────────────────┤
│ 1. Data Drift        │ P(X) changes while P(y | X) remains constant.          │
│    (Covariate Shift) │ -> Input feature distributions shift.                  │
│                      │ -> Example: Average applicant income shifts due to     │
│                      │    marketing campaign targeting students.              │
│                      │ -> Detection: Population Stability Index (PSI), KS-test│
├──────────────────────┼────────────────────────────────────────────────────────┤
│ 2. Concept Drift     │ P(y | X) changes while P(X) may remain unchanged.      │
│                      │ -> The relationship between features and target changes│
│                      │ -> Example: Consumer purchasing behavior fundamentally │
│                      │    inverts overnight during a global pandemic.         │
│                      │ -> Detection: Monitoring rolling validation loss/F1.   │
└──────────────────────┴────────────────────────────────────────────────────────┘
```

---

### 26.3 Automated Retraining Loops & Fail-Safe Fallbacks

- **Automated Retraining:** Trigger model re-fitting when PSI exceeds $0.20$ or rolling F1 drops below the baseline threshold.
- **Fail-Safe Fallbacks:** If the ML microservice times out ($> 100\text{ms}$) or receives malformed data, immediately route decisions to a deterministic heuristic rule engine.

---

## 27. Comparative Matrix: Data Mining vs. Machine Learning vs. Deep Learning

| Attribute                     | Data Mining (CRISP-DM / KDD)                                                 | Classical Machine Learning                                | Deep Learning                                                 |
| :---------------------------- | :--------------------------------------------------------------------------- | :-------------------------------------------------------- | :------------------------------------------------------------ |
| **Primary Goal**        | Knowledge discovery, actionable rules, hidden pattern extraction             | Predictive accuracy on structured tabular inputs          | Representation learning on unstructured perceptual data       |
| **Data Modality**       | Heterogeneous databases, transactions, tabular, text, graphs                 | Clean structured tabular feature vectors                  | Raw unstructured perceptual data (images, audio, video, text) |
| **Core Paradigms**      | Association Rules, Clustering, Classification, Anomaly Mining                | Supervised Classification & Regression, Clustering        | Deep Neural Architectures (Transformers, CNNs, Diffusion)     |
| **Front-End Effort**    | **Massive (60–80%)**: Sourcing, Ingestion, Quality Auditing, Cleaning | Moderate: Preprocessing, manual feature engineering       | Low manual feature engineering; high data annotation cost     |
| **Feature Engineering** | Heavily domain-driven manual synthesis                                       | Iterative manual mathematical and statistical engineering | Automated feature representation learning across deep layers  |
| **Interpretability**    | **Essential**: Knowledge must be understandable and actionable         | High to Moderate (Linear models, Tree ensembles + SHAP)   | Low (Black box; requires complex attribution approximations)  |
| **Typical Tooling**     | SQL, pandas, mlxtend, scikit-learn, Spark, Warehouses                        | scikit-learn, XGBoost, LightGBM, Optuna                   | PyTorch, Hugging Face, JAX, CUDA                              |

---

## 28. Practical End-to-End API Patterns

> **Implementation Note:** The production snippets below illustrate standard, leakage-free implementations. Always adapt paths and parameters to your specific project charter.

---

### 28.1 Data Collection & Raw Ingest with Hash Auditing

```python
"""src/data/collect_raw.py — Robust Ingestion with Cryptographic Lineage."""
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataIngest")

def fetch_and_vault_raw_data(api_url: str, output_path: Path) -> Path:
    """Fetches remote data, writes to immutable raw storage, and mints an audit manifest."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
  
    # 1. Fetch data with timeout
    logger.info("Connecting to %s", api_url)
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()
    raw_payload = response.content

    # 2. Enforce immutable raw write
    if output_path.exists():
        raise FileExistsError(f"Raw data file {output_path} already exists. Never overwrite raw data!")
  
    output_path.write_bytes(raw_payload)
    logger.info("Raw data vaulted at %s", output_path)

    # 3. Mint cryptographic lineage manifest
    checksum = hashlib.sha256(raw_payload).hexdigest()
    manifest = {
        "source_url": api_url,
        "vaulted_path": str(output_path),
        "sha256_checksum": checksum,
        "byte_size": len(raw_payload),
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "ingest_agent_version": "v4.0.0"
    }
  
    manifest_path = output_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info("Lineage manifest minted at %s", manifest_path)
    return output_path
```

---

### 28.2 Data Quality Audit & Schema Validation

```python
"""src/data/quality_audit.py — Automated 6-Dimension Quality Audit."""
import pandas as pd
import numpy as np

def audit_tabular_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Generates comprehensive quality audit statistics across all features."""
    audit_records = []
    total_rows = len(df)
  
    for col in df.columns:
        series = df[col]
        null_count = series.isnull().sum()
        unique_count = series.nunique()
        dtype = str(series.dtype)
      
        # Numeric distribution audit
        skewness = np.nan
        kurt = np.nan
        if pd.api.types.is_numeric_dtype(series):
            skewness = float(series.skew())
            kurt = float(series.kurtosis())
          
        audit_records.append({
            "feature": col,
            "dtype": dtype,
            "null_count": int(null_count),
            "null_pct": round(float(null_count / total_rows) * 100, 2),
            "unique_values": int(unique_count),
            "cardinality_ratio": round(float(unique_count / total_rows), 4),
            "skewness": round(skewness, 2) if not np.isnan(skewness) else None,
            "kurtosis": round(kurt, 2) if not np.isnan(kurt) else None
        })
      
    return pd.DataFrame(audit_records)
```

---

### 28.3 Leakage-Free Preprocessing Pipeline (`scikit-learn`)

```python
"""src/models/pipeline_factory.py — Leakage-Proof ColumnTransformer & Pipeline."""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, RobustScaler
from sklearn.ensemble import HistGradientBoostingClassifier

def build_leakage_free_pipeline(
    numeric_features: list[str],
    skewed_features: list[str],
    categorical_features: list[str]
) -> Pipeline:
    """Assembles a modular, leakage-free scikit-learn pipeline."""
  
    # 1. Normal numeric pipeline (Gaussian-like)
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
  
    # 2. Skewed / Outlier-heavy numeric pipeline
    skewed_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('robust_scaler', RobustScaler())
    ])
  
    # 3. Categorical pipeline
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='Unknown')),
        ('encoder', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'))
    ])
  
    # 4. Integrate into ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('skewed', skewed_transformer, skewed_features),
            ('cat', categorical_transformer, categorical_features)
        ],
        remainder='drop'
    )
  
    # 5. Full pipeline with estimator
    full_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', HistGradientBoostingClassifier(random_state=42))
    ])
  
    return full_pipeline
```

---

### 28.4 Association Rule Mining Pipeline (`mlxtend`)

```python
"""src/mining/association_rules.py — Market Basket Mining Pipeline."""
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules

def mine_actionable_rules(
    transactions: list[list[str]],
    min_support: float = 0.02,
    min_lift: float = 1.5
) -> pd.DataFrame:
    """Mines frequent itemsets via FP-Growth and extracts high-lift association rules."""
  
    # 1. One-hot encode variable-length transactions
    te = TransactionEncoder()
    te_ary = te.fit_transform(transactions)
    df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
  
    # 2. Discover frequent itemsets via FP-Growth (avoids Apriori candidate generation)
    frequent_itemsets = fpgrowth(df_encoded, min_support=min_support, use_colnames=True)
  
    if frequent_itemsets.empty:
        return pd.DataFrame()
      
    # 3. Extract association rules filtered by Lift
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_lift)
  
    # 4. Sort by leverage and confidence for actionable commercial insights
    actionable_rules = rules.sort_values(by=["lift", "confidence"], ascending=[False, False])
    return actionable_rules
```

---

### 28.5 Density & Partitioning Clustering Pipeline

```python
"""src/mining/cluster_analysis.py — K-Means and DBSCAN Clustering with Validation."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score

def execute_clustering_benchmarks(X_scaled: np.ndarray, optimal_k: int = 4) -> dict:
    """Executes K-Means and DBSCAN, computing rigorous cluster validity metrics."""
    results = {}
  
    # 1. Partitioning: K-Means
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    kmeans_labels = kmeans.fit_predict(X_scaled)
  
    results['kmeans'] = {
        'model': kmeans,
        'labels': kmeans_labels,
        'silhouette': float(silhouette_score(X_scaled, kmeans_labels)),
        'davies_bouldin': float(davies_bouldin_score(X_scaled, kmeans_labels))
    }
  
    # 2. Density-Based: DBSCAN
    dbscan = DBSCAN(eps=0.8, min_samples=10)
    dbscan_labels = dbscan.fit_predict(X_scaled)
  
    # Only score if more than 1 cluster found (excluding noise -1)
    unique_clusters = set(dbscan_labels) - {-1}
    if len(unique_clusters) > 1:
        mask = dbscan_labels != -1
        results['dbscan'] = {
            'model': dbscan,
            'labels': dbscan_labels,
            'noise_count': int((dbscan_labels == -1).sum()),
            'silhouette': float(silhouette_score(X_scaled[mask], dbscan_labels[mask])),
            'davies_bouldin': float(davies_bouldin_score(X_scaled[mask], dbscan_labels[mask]))
        }
      
    return results
```

---

### 28.6 Cost-Sensitive Classification with Nested CV & SHAP

```python
"""src/models/train_evaluate.py — Nested CV, Cost Evaluation & SHAP Explanation."""
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, f1_score
import shap

def run_cost_sensitive_experiment(
    X: np.ndarray,
    y: np.ndarray,
    cost_fp: float = 15.0,
    cost_fn: float = 250.0
) -> dict:
    """Evaluates cost-sensitive classifier across Stratified Folds with SHAP interpretation."""
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    auc_scores = []
    total_costs = []
  
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
      
        # Fit cost-weighted model
        clf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
        clf.fit(X_train, y_train)
      
        # Predict probabilities
        y_probs = clf.predict_proba(X_val)[:, 1]
      
        # Optimize threshold against cost matrix
        thresholds = np.linspace(0.1, 0.9, 81)
        costs = []
        for t in thresholds:
            y_pred = (y_probs >= t).astype(int)
            fp = np.sum((y_pred == 1) & (y_val == 0))
            fn = np.sum((y_pred == 0) & (y_val == 1))
            costs.append(fp * cost_fp + fn * cost_fn)
          
        optimal_cost = min(costs)
        auc_scores.append(roc_auc_score(y_val, y_probs))
        total_costs.append(optimal_cost)
      
    # Explain final fold model via TreeSHAP
    explainer = shap.TreeExplainer(clf)
    shap_values = explainer.shap_values(X_val)
  
    return {
        "mean_roc_auc": float(np.mean(auc_scores)),
        "std_roc_auc": float(np.std(auc_scores)),
        "mean_expected_cost": float(np.mean(total_costs)),
        "shap_explainer": explainer
    }
```

---

*This document is the canonical Active Reference (v4.0) for the Data Mining and Machine Learning Engineering curriculum. Adhere to its leakage boundaries, validation protocols, and cost-benefit frameworks across all coursework and experiments.*
