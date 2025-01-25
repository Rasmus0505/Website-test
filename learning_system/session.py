# learning_system/session.py
import json
from pathlib import Path
from datetime import datetime
from .srs import SpacedRepetitionSystem

class LearningSession:
    def __init__(self, topic):
        self.topic = topic
        self.srs = SpacedRepetitionSystem()
        self.cards = []
        self.active = True
        self.save_file = Path("learning_progress") / f"{topic}.json"
        
        if self.save_file.exists():
            self.load_progress()

    def add_card(self, card):
        card_id = int(card['id'])
        if card_id not in self.srs.card_data:
            self.srs.card_data[card_id] = {
                'interval': 1,
                'repetitions': 0,
                'efactor': 2.5,
                'next_review': datetime.now()
            }
        if not any(c['id'] == card_id for c in self.cards):
            self.cards.append({
                'id': card_id,
                'title': card['title'],
                'knowledge': card['knowledge'],
                'questions': card['questions']
            })

    def get_next_card(self):
        due_cards = []
        for card in self.cards:
            card_id = int(card['id'])
            if card_id in self.srs.card_data:
                srs_data = self.srs.card_data[card_id]
                if datetime.now() >= srs_data['next_review']:
                    due_cards.append((card, srs_data))
        due_cards.sort(key=lambda x: (x[1]['efactor'], x[1]['next_review']))
        return due_cards[0][0] if due_cards else None

    def save_progress(self):
        progress = {
            'topic': self.topic,
            'cards': self.cards,
            'srs_data': {int(k): v for k, v in self.srs.card_data.items()},
            'timestamp': datetime.now().isoformat()
        }
        with open(self.save_file, 'w') as f:
            json.dump(progress, f, default=str, indent=2)

    def load_progress(self):
        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)
                self.srs.card_data = {
                    int(k): {
                        **v,
                        'next_review': datetime.fromisoformat(v['next_review'])
                    } for k, v in data['srs_data'].items()
                }
                self.cards = data['cards']
        except Exception as e:
            print(f"⚠️ 加载进度失败：{str(e)}")
            self.cards = []