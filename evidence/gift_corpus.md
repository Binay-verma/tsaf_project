---
license: apache-2.0
task_categories:
- time-series-forecasting
tags:
- timeseries
- forecasting
- benchmark
- gifteval
size_categories:
- 1M<n<10M
---
# GIFT-Eval Pre-training Datasets

Pretraining dataset aligned with [GIFT-Eval](https://huggingface.co/datasets/Salesforce/GiftEval) that has 71 univariate and 17 multivariate datasets, spanning seven domains and 13 frequencies, totaling 4.5 million time series and 230 billion data points. Notably this collection of data has no leakage issue with the train/test split and can be used to pretrain foundation models that can be fairly evaluated on GIFT-Eval.

[📄 Paper](https://arxiv.org/abs/2410.10393)

[🖥️ Code](https://github.com/SalesforceAIResearch/gift-eval)

[📔 Blog Post]()

[🏎️ Leader Board](https://huggingface.co/spaces/Salesforce/GIFT-Eval)

## Ethical Considerations

This release is for research purposes only in support of an academic paper. Our models, datasets, and code are not specifically designed or evaluated for all downstream purposes. We strongly recommend users evaluate and address potential concerns related to accuracy, safety, and fairness before deploying this model. We encourage users to consider the common limitations of AI, comply with applicable laws, and leverage best practices when selecting use cases, particularly for high-risk scenarios where errors or misuse could significantly impact people’s lives, rights, or safety. For further guidance on use cases, refer to our AUP and AI AUP. 

## Citation

<!-- If there is a paper or blog post introducing the dataset, the APA and Bibtex information for that should go in this section. -->


If you find this benchmark useful, please consider citing:
```
@article{aksu2024giftevalbenchmarkgeneraltime,
      title={GIFT-Eval: A Benchmark For General Time Series Forecasting Model Evaluation}, 
      author={Taha Aksu and Gerald Woo and Juncheng Liu and Xu Liu and Chenghao Liu and Silvio Savarese and Caiming Xiong and Doyen Sahoo},
      journal = {arxiv preprint arxiv:2410.10393},
      year={2024},
```