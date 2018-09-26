from milnlp.tokenizers import Tokenizer
from milnlp.sumyplus.SingleDocSummarizer import SingleDocSummarizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from milnlp.mining.phrases import score_keyphrases_by_textrank

file_path = r"C:\Users\zwelz3\Documents\GTRI_Projects\Summarizer\milnlp\Examples\example.pdf"
results = SingleDocSummarizer(Tokenizer, Summarizer)
results.process_document(file_path)

print('\nSummary: ')
for sentence in results.summary:
	print('* ', sentence)

from milnlp.collection.utils.qol import doc_to_text
# Here the input could be any composite document to generate keywords.
text = doc_to_text(results.document)

print('\nKey Words/Phrases: ')
for (word, score) in score_keyphrases_by_textrank(text, n_keywords=10):
	print(word, ',', score)
