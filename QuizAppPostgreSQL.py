import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import psycopg2

# Connect to PostgreSQL database

# Make sure to change the dbname, username, and password with the one you have.
# I have used my Postgres default setup, hence these names.
conn = psycopg2.connect(
    dbname="postgres", 
    user="postgres", 
    password="password", 
    host="localhost", 
    port="5432"
)
cur = conn.cursor()


class Question:
    def __init__(self, question_text, choices, correct_choice):
        self.question_text = question_text
        self.choices = choices
        self.correct_choice = correct_choice

    def is_correct(self, user_choice):
        return self.correct_choice == user_choice


def save_question_series(series_name, questions):
    # Insert question series
    cur.execute("INSERT INTO question_series (name) VALUES (%s) RETURNING id", (series_name,))
    series_id = cur.fetchone()[0]
    conn.commit()

    # Insert questions
    for question in questions:
        cur.execute("""
            INSERT INTO questions (series_id, question_text, choice_1, choice_2, choice_3, choice_4, correct_choice) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (series_id, question.question_text, *question.choices, question.correct_choice))
    conn.commit()


def get_question_series():
    cur.execute("SELECT name FROM question_series")
    series = cur.fetchall()
    return [s[0] for s in series]


def load_questions(series_name):
    cur.execute("""
        SELECT q.question_text, q.choice_1, q.choice_2, q.choice_3, q.choice_4, q.correct_choice
        FROM questions q
        JOIN question_series s ON q.series_id = s.id
        WHERE s.name = %s
    """, (series_name,))
    questions_data = cur.fetchall()
    questions = [Question(q[0], q[1:5], q[5]) for q in questions_data]
    return questions


def save_score(username, score, series_name):
    cur.execute("SELECT id FROM question_series WHERE name = %s", (series_name,))
    series_id = cur.fetchone()[0]
    cur.execute("INSERT INTO leaderboard (username, score, series_id) VALUES (%s, %s, %s)", (username, score, series_id))
    conn.commit()


def load_leaderboard():
    cur.execute("""
        SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10
    """)
    return cur.fetchall()


class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Application")
        self.root.geometry("600x400")

        self.current_question = 0
        self.score = 0
        self.timer = 15
        self.timer_running = False
        self.questions = []
        self.selected_series = None

        self.main_menu()

    # Main menu of the tkinter GUI
    def main_menu(self):
        """Displays the main menu options."""
        self.clear_screen()

        self.menu_label = tk.Label(self.root, text="Quiz Application", font=("Arial", 20))
        self.menu_label.pack(pady=20)

        self.create_button = tk.Button(self.root, text="Create Question Series", command=self.create_question_series, font=("Arial", 14))
        self.create_button.pack(pady=10)

        self.start_button = tk.Button(self.root, text="Start Quiz", command=self.select_question_series, font=("Arial", 14))
        self.start_button.pack(pady=10)

        self.leaderboard_button = tk.Button(self.root, text="View Leaderboard", command=self.view_leaderboard, font=("Arial", 14))
        self.leaderboard_button.pack(pady=10)

        self.quit_button = tk.Button(self.root, text="Quit", command=self.root.quit, font=("Arial", 14))
        self.quit_button.pack(pady=10)

    def clear_screen(self):
        """Clears the current widgets from the screen."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_question_series(self):
        """Allows user to create a custom question series."""
        self.clear_screen()

        self.series_name = simpledialog.askstring("Series Name", "Enter a name for the question series:")
        if not self.series_name:
            self.main_menu()
            return

        self.questions = []
        self.add_question()

    def add_question(self):
        """Prompts user to add a question to the series."""
        question_text = simpledialog.askstring("New Question", "Enter the question:")
        choices = [simpledialog.askstring("Choice", f"Enter choice {i + 1}:") for i in range(4)]
        correct_choice = simpledialog.askinteger("Correct Answer", "Enter the correct choice number (1-4):") - 1

        if question_text and all(choices) and 0 <= correct_choice < 4:
            question = Question(question_text, choices, correct_choice)
            self.questions.append(question)

            more = messagebox.askyesno("Add Another?", "Do you want to add another question?")
            if more:
                self.add_question()
            else:
                save_question_series(self.series_name, self.questions)
                messagebox.showinfo("Saved", f"Series '{self.series_name}' saved successfully!")
                self.main_menu()
        else:
            messagebox.showerror("Error", "Invalid question format. Please try again.")
            self.add_question()

    def select_question_series(self):
        """Allows user to select a saved question series."""
        self.clear_screen()

        series_list = get_question_series()
        if not series_list:
            messagebox.showinfo("No Series", "No question series found. Please create one first.")
            self.main_menu()
            return

        self.selected_series = tk.StringVar()
        tk.Label(self.root, text="Select a Question Series:", font=("Arial", 14)).pack(pady=10)
        for series in series_list:
            tk.Radiobutton(self.root, text=series, variable=self.selected_series, value=series).pack(anchor="w")

        tk.Button(self.root, text="Start", command=self.start_quiz, font=("Arial", 14)).pack(pady=20)

    def start_quiz(self):
        """Loads the selected series and starts the quiz."""
        self.questions = load_questions(self.selected_series.get())
        if not self.questions:
            messagebox.showerror("Error", "Failed to load questions.")
            self.main_menu()
            return

        self.current_question = 0
        self.score = 0
        self.show_question()

    def show_question(self):
        """Displays the current question."""
        self.clear_screen()

        if self.current_question < len(self.questions):
            self.timer = 15
            self.timer_running = True
            self.update_timer()

            question = self.questions[self.current_question]
            tk.Label(self.root, text=f"Q{self.current_question + 1}: {question.question_text}", font=("Arial", 14), wraplength=550).pack(pady=10)

            self.options = tk.IntVar(value=-1)  # Ensures no default selection
            for i, choice in enumerate(question.choices):
                tk.Radiobutton(self.root, text=choice, variable=self.options, value=i, font=("Arial", 12)).pack(anchor="w")

            tk.Button(self.root, text="Submit", command=self.submit_answer, font=("Arial", 12)).pack(pady=10)
        else:
            self.end_quiz()

    def submit_answer(self):
        """Validates the answer and updates the score."""
        if not self.timer_running:
            return

        self.timer_running = False
        user_choice = self.options.get()
        question = self.questions[self.current_question]

        if question.is_correct(user_choice):
            self.score += 1
            messagebox.showinfo("Correct!", "Correct answer!")
        else:
            messagebox.showerror("Incorrect", f"Correct answer was: {question.choices[question.correct_choice]}")

        self.current_question += 1
        self.show_question()

    def end_quiz(self):
        """Ends the quiz and saves the score."""
        username = simpledialog.askstring("Username", "Enter your username:")
        save_score(username, self.score, self.selected_series.get())
        messagebox.showinfo("Quiz Completed", f"Quiz finished! Your score: {self.score}/{len(self.questions)}")
        self.main_menu()

    def view_leaderboard(self):
        """Displays the leaderboard."""
        self.clear_screen()

        leaderboard = load_leaderboard()
        tk.Label(self.root, text="Leaderboard", font=("Arial", 20)).pack(pady=10)
        for rank, (user, score) in enumerate(leaderboard, start=1):
            tk.Label(self.root, text=f"{rank}. {user}: {score}", font=("Arial", 14)).pack(anchor="w")

        tk.Button(self.root, text="Back", command=self.main_menu, font=("Arial", 12)).pack(pady=10)

    def update_timer(self):
        """Updates the timer for the current question."""
        if self.timer > 0 and self.timer_running:
            self.timer -= 1
            self.root.after(1000, self.update_timer)
        elif self.timer == 0:
            messagebox.showerror("Time's Up", "Time's up for this question!")
            self.current_question += 1
            self.show_question()


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
