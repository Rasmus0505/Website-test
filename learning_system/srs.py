# learning_system/srs.py
from datetime import datetime, timedelta

class SpacedRepetitionSystem:
    def __init__(self):
        self.card_data = {}
    
    def update_card(self, card_id, quality):
        now = datetime.now()
        data = self.card_data.get(card_id, {
            'interval': 1,
            'repetitions': 0,
            'efactor': 2.5,
            'next_review': now
        })

        if quality < 3:
            data['interval'] = 1
            data['repetitions'] = 0
        else:
            if data['repetitions'] == 0:
                data['interval'] = 1
            elif data['repetitions'] == 1:
                data['interval'] = 6
            else:
                data['interval'] = int(data['interval'] * data['efactor'])
            
            data['efactor'] = max(1.3, data['efactor'] + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
            data['repetitions'] += 1

        data['next_review'] = now + timedelta(days=data['interval'])
        self.card_data[card_id] = data
        return data