### How to Install milnlp Package

Navigate to the root directory of the downloaded package. 

```python
conda install pyqt=5.6.0
pip install -e .
python -m nltk.downloader punkt stopwords averaged_perceptron_tagger
```

In your user environment variables, add the path to the installed pyside2 dependency plugins:
```python
...pyside2/plugins/platforms
```
with the label `QT_QPA_PLATFORM_PLUGIN_PATH`. 

Restart your console. 

Note** Make sure your target display is set to 1920x1080 resolution and the scale is set to 100% or their will be GUI sizing issues. 