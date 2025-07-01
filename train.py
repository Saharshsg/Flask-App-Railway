import time
# time.clock has been deprecated in Python 3.3 and removed in Python 3.8
# Monkey-patch it for old versions of SQLAlchemy
if not hasattr(time, 'clock'):
    time.clock = time.perf_counter

from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

# Create a chatbot
chatbot = ChatBot('OfficeBot')

# Create a new trainer for the chatbot
trainer = ChatterBotCorpusTrainer(chatbot)

# Train the chatbot on the English corpus
print("Training bot...")
trainer.train("chatterbot.corpus.english")
print("Training complete.") 