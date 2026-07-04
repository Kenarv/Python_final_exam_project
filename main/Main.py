import re
import datetime
import json
import random

class WrongInputError(ValueError): pass

class Player:
    def __init__(self, name: str, score: int, date: str):
        self.name = name
        self.score = score
        self.date = date
        
    def to_dict(self):
        return {
            "name": self.name,
            "score": self.score,
            "date": self.date
        }
        
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data.get("name", ""),
            score=data.get("score", 0),
            date=data.get("date", "")
        )

# ----- Függvények 

def ask_player_name() -> str:
    name = input("Kérlek, add meg a neved: ").strip()
    while not name:
        name = input("A név nem lehet üres! Kérlek, add meg a neved: ").strip()
    return name

def select_category() -> int:
    print("\nElérhető kategóriák:\n1 - Történelem\n2 - Fizika\n3 - Tech")
    while True:
        category_input = input("Írd be a játszani kívánt téma azonosítóját (1, 2 vagy 3): ").strip()
        if category_input in ['1', '2', '3']:
            return int(category_input)
        print("Érvénytelen kategória! Kérlek, 1, 2 vagy 3 számot adj meg.")

def load_questions() -> list:
    try:
        with open('questions.json', encoding='utf-8') as questions_file:
            return json.load(questions_file)
    except FileNotFoundError:
        print("A kérdések JSON fájl nem található. Ellenőrizd a fájl elérési útját és nevét.")
        return []

def filter_questions_by_category(questions_data: list, category: int) -> list:
    questions_n_answers = []
    for item in questions_data:
        if item.get('question_category') == category:
            questions_n_answers.append((
                int(item['question_type']), 
                item['question'], 
                item['correct_answer'], 
                item['pattern']
            ))
    return questions_n_answers

def shuffle_questions(questions_n_answers: list) -> None:
    random.shuffle(questions_n_answers)

def ask_questions(q_type: int, question: str, **kwargs) -> tuple:
    while True:
        try:
            userAnswer = input(f"\n{question}\nVálasz: ").strip()
            
            match q_type:
                case 1:
                    if bool(re.search(kwargs['pattern'], userAnswer, re.IGNORECASE)):
                        return True, 'Helyes válasz! (5 pont)', 5 
                    else:
                        return False, f'Helytelen válasz! A helyes válasz "{kwargs["answer"]}" lett volna!', 0

                case 2:
                    try:
                        userAnswer_int = int(userAnswer)
                        if userAnswer_int == int(kwargs['answer']):
                            return True, 'Helyes válasz! (5 pont)', 5
                        elif bool(re.search(kwargs['pattern'], str(userAnswer_int), re.IGNORECASE)):
                            return False, f'Majdnem! A helyes válasz "{kwargs["answer"]}" lett volna! (3 pont)', 3
                        else:
                            return False, f'Helytelen válasz! A helyes válasz "{kwargs["answer"]}" lett volna!', 0
                    except ValueError:
                        raise WrongInputError(f'Nem számot adtál meg: {userAnswer}')    
                case 3:
                    try:
                        userAnswer_float = float(userAnswer)
                        if userAnswer_float == float(kwargs['answer']):
                            return True, 'Helyes válasz! (5 pont)', 5
                        elif bool(re.search(kwargs['pattern'], str(userAnswer_float))):
                            return False, f'Majdnem! A helyes válasz "{kwargs["answer"]}" lett volna! (3 pont)', 3
                        else:
                            return False, f'Helytelen válasz! A helyes válasz "{kwargs["answer"]}" lett volna!', 0
                    except ValueError:
                        raise WrongInputError(f'Nem számot adtál meg: {userAnswer}')  
                case 4:
                    try:
                        userAnswer_date = datetime.date.fromisoformat(userAnswer)
                        correct_date = datetime.date.fromisoformat(kwargs['answer'])
                        difference = abs((userAnswer_date - correct_date).days)
                        if difference == 0:
                            return True, 'Helyes válasz! (5 pont)', 5
                        else:
                            return False, f'Heltelen válasz! A helyes válasz "{kwargs["answer"]}" lett volna! (eltérés: {difference} nap)', 0
                    except ValueError:
                        raise WrongInputError(f'Nem megfelelő formátumú dátum: {userAnswer}. Használd az ÉÉÉÉ-HH-NN formátumot.')   
        except WrongInputError as err:
            print(f"Hibás formátum! ({err}) Kérlek add meg újra a választ a megfelelő típusban.")
# -------------------------------------------

# ---------------- Fő mag -------------------

#Változók inicializálása:
player_name = ask_player_name()
selected_category = select_category()
all_questions = load_questions()
questions_n_answers = filter_questions_by_category(all_questions, selected_category)
points = 0
max_possible_points = len(questions_n_answers) * 5

#Kérdések keverése helyben:
shuffle_questions(questions_n_answers)

#GAME:
if not questions_n_answers:
    print("Ebben a kategóriában nem találtam kérdéseket.")
else:
    for q_type, question, answer, pattern in questions_n_answers:
        is_correct, message, point = ask_questions(q_type, question, answer=answer, pattern=pattern)
        print(message) 
        points += point
        with open('results_log.txt', 'a', encoding='utf-8') as results_file:
            print(f"{player_name} - {question} -> {message}", file=results_file)

    # Eredmények kiírása
    print(f'\nA pontszámod: {points} / {max_possible_points}')
    percentage = (points / max_possible_points * 100) if max_possible_points > 0 else 0
    print(f'Az elért százalék: {percentage:.3g}%')

    # --- HIGHSCORE / PLAYERS MANIPULÁCIÓ ---
    try:
        with open('players.json', 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            players_objects = [Player.from_dict(p) for p in raw_data]
    except (FileNotFoundError, json.JSONDecodeError):
        players_objects = []
        
    current_player = Player(
        name=player_name,
        score=points,
        date=str(datetime.date.today())
    )
    players_objects.append(current_player)

    with open('players.json', 'w', encoding='utf-8') as f:
        json_ready_data = [player.to_dict() for player in players_objects]
        json.dump(json_ready_data, f, ensure_ascii=False, indent=4)

    players_objects.sort(key=lambda x: x.score, reverse=True)

    print("\n" + "="*30)
    print("         RANGLISTA         ")
    print("="*30)
    for index, player in enumerate(players_objects, start=1):
        current_marker = " -> " if player is current_player else "    "
        print(f"{current_marker}{index}. {player.name}: {player.score} pont ({player.date})")
    print("="*30)